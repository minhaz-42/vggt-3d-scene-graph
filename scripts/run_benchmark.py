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
    parser.add_argument(
        "--proposal-backend",
        default="owlv2",
        choices=["owlv2", "sam"],
        help="Object-proposal front-end. 'owlv2' = open-vocab detector (real labels, the fix); "
        "'sam' = legacy SAM auto-masks + CLIP-text labels (kept for reproducing old runs).",
    )
    parser.add_argument(
        "--sam-checkpoint",
        type=Path,
        help="SAM checkpoint. Required for --proposal-backend sam; optional for owlv2 "
        "(when set, OWLv2 boxes are refined into clean instance masks via box-prompted SAM).",
    )
    parser.add_argument("--sam-model-type", default="vit_b", choices=["vit_h", "vit_l", "vit_b"])
    parser.add_argument("--sam-max-image-side", type=int, default=1024)
    parser.add_argument("--sam-points-per-side", type=int, default=16)
    parser.add_argument("--sam-max-proposals-per-image", type=int, default=30)
    # OWLv2 open-vocab detector knobs (proposal-backend=owlv2). Queries come from --label-vocab.
    parser.add_argument("--owlv2-model", default="google/owlv2-base-patch16-ensemble")
    parser.add_argument("--owlv2-threshold", type=float, default=0.2, help="OWLv2 detection score threshold.")
    parser.add_argument("--owlv2-nms-iou", type=float, default=0.5, help="OWLv2 per-class NMS IoU; <=0 disables.")
    parser.add_argument("--owlv2-max-detections", type=int, default=30, help="Max OWLv2 detections per image.")
    parser.add_argument(
        "--owlv2-device",
        default="auto",
        choices=["auto", "cpu", "mps", "cuda"],
        help="Device for OWLv2 (and box-prompted SAM). 'auto' picks cuda>mps>cpu.",
    )
    parser.add_argument(
        "--proposal-local-files-only",
        action="store_true",
        help="Load the OWLv2 detector from the local HF cache only (offline).",
    )
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
        choices=["2d-only", "geometry-only", "semantic-lifting", "graph-fusion", "graph-fusion-dedup", "proposed", "fixed-shrink"],
        help="Fusion variant for the graph stage. Non-default variants reuse the shared upstream "
        "feature cache and write graphs under <output-root>/variants/<variant>/.",
    )
    parser.add_argument("--dedup-iou", type=float, default=0.1, help="3D-box IoU for duplicate-instance merge (variant=graph-fusion-dedup).")
    parser.add_argument("--use-uncertainty", action="store_true", help="Enable uncertainty-aware fusion (variant=proposed).")
    parser.add_argument("--uncertainty-weight", type=float, default=0.5)
    parser.add_argument("--feature-uncertainty-weight", type=float, default=1.0)
    parser.add_argument("--uncertainty-agg", choices=["max", "mean"], default="max")
    parser.add_argument("--uncertainty-normalize", choices=["none", "rank", "minmax"], default="none")
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


def _validate_proposal_backend(args: argparse.Namespace, stages: set[str]) -> None:
    if "proposals" not in stages:
        return
    if args.proposal_backend == "sam" and args.sam_checkpoint is None:
        raise SystemExit("--sam-checkpoint is required for --proposal-backend sam.")
    if args.proposal_backend == "owlv2" and args.label_vocab is None:
        raise SystemExit(
            "--label-vocab is required for --proposal-backend owlv2 (it supplies the detector's text queries)."
        )


def main() -> None:
    args = parse_args()
    stages = _stage_set(args.stages)
    _validate_proposal_backend(args, stages)
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
            # Proposal/feature filenames are backend-namespaced so an OWLv2 run never clobbers
            # (or silently reuses) the legacy SAM-auto cache, and the names stay honest.
            file_prefix = "owlv2" if args.proposal_backend == "owlv2" else "sam"
            raw_proposals_path = feature_dir / f"{file_prefix}_proposals.json"
            clip_path = feature_dir / f"{file_prefix}_clip_features.json"
            dinov2_path = feature_dir / f"{file_prefix}_clip_dinov2_features.json"
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
                "proposal_backend": args.proposal_backend,
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
                if args.proposal_backend == "owlv2":
                    proposals_command = [
                        sys.executable,
                        "scripts/run_owlv2_proposals.py",
                        "--scene-dir",
                        str(scene.scene_dir),
                        *_image_args(image_names),
                        "--labels",
                        str(args.label_vocab),
                        "--owlv2-model",
                        args.owlv2_model,
                        "--device",
                        args.owlv2_device,
                        "--threshold",
                        str(args.owlv2_threshold),
                        "--nms-iou",
                        str(args.owlv2_nms_iou),
                        "--max-detections-per-image",
                        str(args.owlv2_max_detections),
                        "--output",
                        str(raw_proposals_path),
                    ]
                    if args.sam_checkpoint is not None:
                        # Box-prompted SAM masks → clean 3D lifting (only object pixels, not bbox bg).
                        proposals_command += [
                            "--sam-checkpoint",
                            str(args.sam_checkpoint),
                            "--sam-model-type",
                            args.sam_model_type,
                        ]
                    if args.proposal_local_files_only:
                        proposals_command.append("--local-files-only")
                else:
                    proposals_command = [
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
                        str(raw_proposals_path),
                    ]
                commands.append(_run_command(proposals_command, raw_proposals_path, args))

            if "clip" in stages:
                commands.append(
                    _run_command(
                        [
                            sys.executable,
                            "scripts/extract_proposal_features.py",
                            "--scene-dir",
                            str(scene.scene_dir),
                            "--proposals",
                            str(raw_proposals_path),
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
                        "--uncertainty-normalize",
                        args.uncertainty_normalize,
                        "--uncertainty-min-shrink",
                        str(args.uncertainty_min_shrink),
                        "--uncertainty-max-feature-threshold",
                        str(args.uncertainty_max_feature_threshold),
                        "--bridge-tau",
                        str(args.bridge_tau),
                    ]
                if args.variant == "fixed-shrink":
                    graph_command += ["--fixed-shrink", str(args.fixed_shrink)]
                if args.variant == "graph-fusion-dedup":
                    graph_command += ["--dedup-iou", str(args.dedup_iou)]
                commands.append(_run_command(graph_command, graph_path, args))

            # OWLv2 carries real labels on every proposal, so labeling is a score-weighted vote
            # over the fused node's owlv2_labels (no vocab needed). SAM has no labels, so it still
            # needs the CLIP-text-similarity stage against a vocabulary.
            labeled_graph_available = "labels" in stages and (
                args.proposal_backend == "owlv2" or args.label_vocab is not None
            )
            if labeled_graph_available:
                if args.proposal_backend == "owlv2":
                    label_command = [
                        sys.executable,
                        "scripts/assign_detector_labels.py",
                        "--scene-graph",
                        str(graph_path),
                        "--proposals",
                        str(dinov2_path),
                        "--output",
                        str(labeled_graph_path),
                    ]
                else:
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
                commands.append(_run_command(label_command, labeled_graph_path, args))

            if "figure" in stages:
                graph_for_figure = labeled_graph_path if labeled_graph_available else graph_path
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
                "proposal_backend": args.proposal_backend,
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
