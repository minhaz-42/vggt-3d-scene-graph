from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

from vggt_scene_graph.datasets import load_dataset_manifest, sparse_view_split


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run benchmark-scale sparse-view scene graph experiments.")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("results/benchmark"))
    parser.add_argument("--scene-id", action="append", default=[], help="Scene id to run. Repeat for multiple scenes.")
    parser.add_argument("--view-counts", type=int, nargs="+", help="Override manifest sparse-view counts.")
    parser.add_argument(
        "--stages",
        nargs="+",
        default=["all"],
        choices=["all", "geometry", "proposals", "clip", "dinov2", "graph", "labels", "figure"],
    )
    parser.add_argument("--sam-checkpoint", type=Path, help="SAM checkpoint for proposal generation.")
    parser.add_argument("--sam-model-type", default="vit_b", choices=["vit_h", "vit_l", "vit_b"])
    parser.add_argument("--sam-max-image-side", type=int, default=1024)
    parser.add_argument("--sam-points-per-side", type=int, default=16)
    parser.add_argument("--sam-max-proposals-per-image", type=int, default=30)
    parser.add_argument("--geometry-device", default="cpu", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--feature-device", default="cpu")
    parser.add_argument("--clip-model", default="openai/clip-vit-base-patch32")
    parser.add_argument("--dinov2-model", default="facebook/dinov2-base")
    parser.add_argument("--label-vocab", type=Path, help="Optional labels JSON for open-vocabulary node labeling.")
    parser.add_argument("--label-local-files-only", action="store_true", help="Load CLIP labels from local cache only.")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands without running them.")
    parser.add_argument("--index-output", type=Path, help="Benchmark index JSON path.")
    parser.add_argument(
        "--variant",
        default="graph-fusion",
        choices=["2d-only", "geometry-only", "semantic-lifting", "graph-fusion", "proposed", "fixed-shrink"],
        help="Fusion variant for the graph stage. Non-default variants reuse the shared upstream "
        "feature cache and write graphs under <output-root>/variants/<variant>/.",
    )
    parser.add_argument("--use-uncertainty", action="store_true", help="Enable uncertainty-aware fusion (variant=proposed).")
    parser.add_argument("--uncertainty-weight", type=float, default=0.5)
    parser.add_argument("--feature-uncertainty-weight", type=float, default=1.0)
    parser.add_argument("--uncertainty-agg", choices=["max", "mean"], default="max")
    parser.add_argument("--uncertainty-min-shrink", type=float, default=0.1)
    parser.add_argument("--uncertainty-max-feature-threshold", type=float, default=0.99)
    parser.add_argument("--bridge-tau", type=float, default=0.6)
    parser.add_argument("--fixed-shrink", type=float, default=1.0)
    return parser.parse_args()


def _stage_set(stages: list[str]) -> set[str]:
    if "all" in stages:
        return {"geometry", "proposals", "clip", "dinov2", "graph", "labels", "figure"}
    return set(stages)


def _image_args(image_names: list[str]) -> list[str]:
    args: list[str] = []
    for image_name in image_names:
        args.extend(["--image-name", image_name])
    return args


def _run_command(cmd: list[str], output_path: Path | None, args: argparse.Namespace) -> dict[str, object]:
    record = {
        "command": shlex.join(cmd),
        "output_path": str(output_path) if output_path else None,
        "status": "planned" if args.dry_run else "pending",
    }
    if output_path is not None and args.skip_existing and output_path.exists():
        record["status"] = "skipped_existing"
        print(f"SKIP {output_path}")
        return record

    print(shlex.join(cmd))
    if args.dry_run:
        return record

    subprocess.run(cmd, check=True)
    record["status"] = "complete"
    return record


def _require_sam(args: argparse.Namespace, stages: set[str]) -> None:
    if "proposals" in stages and args.sam_checkpoint is None:
        raise SystemExit("--sam-checkpoint is required when running the proposals stage.")


def main() -> None:
    args = parse_args()
    stages = _stage_set(args.stages)
    _require_sam(args, stages)
    manifest = load_dataset_manifest(args.dataset)
    selected_scene_ids = set(args.scene_id)
    scenes = [scene for scene in manifest.scenes if not selected_scene_ids or scene.scene_id in selected_scene_ids]
    missing_scene_ids = sorted(selected_scene_ids - {scene.scene_id for scene in manifest.scenes})
    if missing_scene_ids:
        raise SystemExit(f"Scene id(s) not found in dataset: {', '.join(missing_scene_ids)}")
    view_counts = args.view_counts or manifest.sparse_view_counts
    index_records: list[dict[str, object]] = []

    for scene in scenes:
        for view_count in view_counts:
            selected = sparse_view_split(scene.image_paths, view_count)
            image_names = [path.name for path in selected]
            view_subdir = f"views_{len(image_names):02d}"
            # Upstream features (geometry/SAM/CLIP/DINOv2) are variant-independent and shared.
            feature_dir = args.output_root / scene.scene_id / view_subdir
            # Graphs are per-variant. The default variant keeps the original layout for
            # backward compatibility; other variants are namespaced under variants/<variant>/.
            if args.variant == "graph-fusion":
                graph_dir = feature_dir
            else:
                graph_dir = args.output_root / "variants" / args.variant / scene.scene_id / view_subdir
            geometry_path = feature_dir / "vggt_geometry.npz"
            sam_path = feature_dir / "sam_proposals.json"
            clip_path = feature_dir / "sam_clip_features.json"
            dinov2_path = feature_dir / "sam_clip_dinov2_features.json"
            graph_path = graph_dir / "scene_graph.json"
            labeled_graph_path = graph_dir / "scene_graph_labeled.json"
            figure_path = graph_dir / "scene_graph.png"
            feature_dir.mkdir(parents=True, exist_ok=True)
            graph_dir.mkdir(parents=True, exist_ok=True)

            commands: list[dict[str, object]] = []
            common = {
                "scene_id": scene.scene_id,
                "split": scene.split,
                "variant": args.variant,
                "view_count": len(image_names),
                "selected_images": image_names,
                "run_dir": str(graph_dir),
                "feature_dir": str(feature_dir),
                "geometry_path": str(geometry_path),
                "proposals_path": str(dinov2_path),
                "scene_graph_path": str(graph_path),
                "labeled_scene_graph_path": str(labeled_graph_path),
                "figure_path": str(figure_path),
            }

            if "geometry" in stages:
                commands.append(
                    _run_command(
                        [
                            sys.executable,
                            "scripts/run_vggt_geometry.py",
                            "--scene-dir",
                            str(scene.scene_dir),
                            *_image_args(image_names),
                            "--output",
                            str(geometry_path),
                            "--device",
                            args.geometry_device,
                        ],
                        geometry_path,
                        args,
                    )
                )

            if "proposals" in stages:
                commands.append(
                    _run_command(
                        [
                            sys.executable,
                            "scripts/run_sam_proposals.py",
                            "--scene-dir",
                            str(scene.scene_dir),
                            *_image_args(image_names),
                            "--checkpoint",
                            str(args.sam_checkpoint),
                            "--model-type",
                            args.sam_model_type,
                            "--max-image-side",
                            str(args.sam_max_image_side),
                            "--points-per-side",
                            str(args.sam_points_per_side),
                            "--max-proposals-per-image",
                            str(args.sam_max_proposals_per_image),
                            "--output",
                            str(sam_path),
                        ],
                        sam_path,
                        args,
                    )
                )

            if "clip" in stages:
                commands.append(
                    _run_command(
                        [
                            sys.executable,
                            "scripts/extract_proposal_features.py",
                            "--scene-dir",
                            str(scene.scene_dir),
                            "--proposals",
                            str(sam_path),
                            "--output",
                            str(clip_path),
                            "--backend",
                            "clip",
                            "--model-name",
                            args.clip_model,
                            "--device",
                            args.feature_device,
                        ],
                        clip_path,
                        args,
                    )
                )

            if "dinov2" in stages:
                commands.append(
                    _run_command(
                        [
                            sys.executable,
                            "scripts/extract_proposal_features.py",
                            "--scene-dir",
                            str(scene.scene_dir),
                            "--proposals",
                            str(clip_path),
                            "--output",
                            str(dinov2_path),
                            "--backend",
                            "dinov2",
                            "--model-name",
                            args.dinov2_model,
                            "--device",
                            args.feature_device,
                        ],
                        dinov2_path,
                        args,
                    )
                )

            if "graph" in stages:
                graph_command = [
                    sys.executable,
                    "scripts/run_pipeline.py",
                    "--scene-id",
                    scene.scene_id,
                    "--scene-dir",
                    str(scene.scene_dir),
                    "--geometry",
                    str(geometry_path),
                    "--proposals",
                    str(dinov2_path),
                    "--output",
                    str(graph_path),
                    "--variant",
                    args.variant,
                ]
                if args.variant == "proposed":
                    # proposed is uncertainty-ON by definition; forward all knobs so a sweep can
                    # set them per point (weight=0 + feature-weight=0 + bridge-tau>=1 is the no-op).
                    graph_command += [
                        "--use-uncertainty",
                        "--uncertainty-weight",
                        str(args.uncertainty_weight),
                        "--feature-uncertainty-weight",
                        str(args.feature_uncertainty_weight),
                        "--uncertainty-agg",
                        args.uncertainty_agg,
                        "--uncertainty-min-shrink",
                        str(args.uncertainty_min_shrink),
                        "--uncertainty-max-feature-threshold",
                        str(args.uncertainty_max_feature_threshold),
                        "--bridge-tau",
                        str(args.bridge_tau),
                    ]
                if args.variant == "fixed-shrink":
                    graph_command += ["--fixed-shrink", str(args.fixed_shrink)]
                commands.append(_run_command(graph_command, graph_path, args))

            if "labels" in stages and args.label_vocab is not None:
                label_command = [
                    sys.executable,
                    "scripts/assign_open_vocab_labels.py",
                    "--scene-graph",
                    str(graph_path),
                    "--proposals",
                    str(dinov2_path),
                    "--labels",
                    str(args.label_vocab),
                    "--output",
                    str(labeled_graph_path),
                    "--model-name",
                    args.clip_model,
                    "--device",
                    args.feature_device,
                ]
                if args.label_local_files_only:
                    label_command.append("--local-files-only")
                commands.append(
                    _run_command(
                        label_command,
                        labeled_graph_path,
                        args,
                    )
                )

            if "figure" in stages:
                graph_for_figure = labeled_graph_path if "labels" in stages and args.label_vocab is not None else graph_path
                commands.append(
                    _run_command(
                        [
                            sys.executable,
                            "scripts/visualize_scene_graph.py",
                            str(graph_for_figure),
                            "--output",
                            str(figure_path),
                        ],
                        figure_path,
                        args,
                    )
                )

            index_records.append({**common, "commands": commands})

    if args.index_output:
        output_path = args.index_output
    elif args.variant == "graph-fusion":
        output_path = args.output_root / "benchmark_index.json"
    else:
        output_path = args.output_root / "variants" / args.variant / "benchmark_index.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "dataset": str(args.dataset),
                "dataset_name": manifest.name,
                "dataset_version": manifest.version,
                "variant": args.variant,
                "stages": sorted(stages),
                "num_runs": len(index_records),
                "runs": index_records,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote benchmark index to {output_path}")


if __name__ == "__main__":
    main()
