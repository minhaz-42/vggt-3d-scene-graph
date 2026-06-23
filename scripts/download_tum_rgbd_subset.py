from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Iterable

from huggingface_hub import HfApi, hf_hub_download


DEFAULT_SEQUENCES = [
    "rgbd_dataset_freiburg1_room",
    "rgbd_dataset_freiburg1_desk",
    "rgbd_dataset_freiburg1_desk2",
    "rgbd_dataset_freiburg2_xyz",
    "rgbd_dataset_freiburg3_long_office_household",
]

OFFICIAL_TUM_URL = "https://cvg.cit.tum.de/data/datasets/rgbd-dataset"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a sparse RGB-only TUM RGB-D benchmark subset.")
    parser.add_argument("--repo-id", default="voviktyl/TUM_RGBD-SLAM", help="Hugging Face dataset mirror repo id.")
    parser.add_argument("--sequences", nargs="+", default=DEFAULT_SEQUENCES)
    parser.add_argument("--output-root", type=Path, default=Path("data/benchmark/tum_rgbd_paper_subset"))
    parser.add_argument("--manifest-output", type=Path, default=Path("configs/datasets/tum_rgbd_paper_subset.json"))
    parser.add_argument("--num-frames", type=int, default=10)
    parser.add_argument("--sample-mode", choices=["stride", "even"], default="stride")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--frame-stride", type=int, default=10)
    parser.add_argument("--sparse-view-counts", type=int, nargs="+", default=[3, 5, 8, 10])
    parser.add_argument("--split", default="val")
    parser.add_argument("--force", action="store_true", help="Overwrite existing local frame files.")
    parser.add_argument("--dry-run", action="store_true", help="List selected remote frames without downloading.")
    parser.add_argument("--discover", action="store_true", help="List available top-level TUM sequence folders and exit.")
    return parser.parse_args()


def _scene_id(sequence: str) -> str:
    if sequence.startswith("rgbd_dataset_"):
        return "tum_rgbd_" + sequence.removeprefix("rgbd_dataset_")
    return "tum_rgbd_" + sequence


def _is_rgb_image(path: str) -> bool:
    suffix = Path(path).suffix.lower()
    return suffix in {".png", ".jpg", ".jpeg"} and "/rgb/" in path


def _list_rgb_files(api: HfApi, repo_id: str, sequence: str) -> list[str]:
    rgb_dir = f"{sequence}/rgb"
    entries = api.list_repo_tree(
        repo_id=repo_id,
        repo_type="dataset",
        path_in_repo=rgb_dir,
        recursive=False,
    )
    paths = [str(getattr(entry, "path", "")) for entry in entries]
    return sorted(path for path in paths if _is_rgb_image(path))


def _discover_sequences(api: HfApi, repo_id: str) -> list[str]:
    entries = api.list_repo_tree(repo_id=repo_id, repo_type="dataset", recursive=False)
    sequences = []
    for entry in entries:
        path = str(getattr(entry, "path", ""))
        if path.startswith("rgbd_dataset_"):
            sequences.append(path)
    return sorted(sequences)


def _sample_stride(paths: list[str], count: int, start_index: int, stride: int) -> list[str]:
    stride = max(stride, 1)
    start_index = max(start_index, 0)
    selected = paths[start_index::stride][:count]
    if len(selected) >= count:
        return selected
    selected_paths = set(selected)
    for path in paths:
        if path in selected_paths:
            continue
        selected.append(path)
        selected_paths.add(path)
        if len(selected) >= count:
            break
    return selected


def _sample_even(paths: list[str], count: int) -> list[str]:
    if count >= len(paths):
        return paths
    if count <= 1:
        return paths[:count]
    last_index = len(paths) - 1
    indices = [round(index * last_index / (count - 1)) for index in range(count)]
    return [paths[index] for index in indices]


def _sample_paths(paths: list[str], args: argparse.Namespace) -> list[str]:
    if args.sample_mode == "even":
        return _sample_even(paths, args.num_frames)
    return _sample_stride(paths, args.num_frames, args.start_index, args.frame_stride)


def _copy_remote_frame(repo_id: str, remote_path: str, output_path: Path, force: bool) -> None:
    if output_path.exists() and not force:
        return
    local_path = hf_hub_download(repo_id=repo_id, repo_type="dataset", filename=remote_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(local_path, output_path)


def _dataset_readme(sequence: str, selected_paths: list[str], repo_id: str) -> str:
    lines = [
        f"# TUM RGB-D {sequence} Sparse RGB Subset",
        "",
        "This folder contains a sparse RGB-only subset of the public TUM RGB-D benchmark.",
        "",
        "Official dataset page:",
        "",
        "```text",
        OFFICIAL_TUM_URL,
        "```",
        "",
        "Downloaded mirror path:",
        "",
        "```text",
        f"https://huggingface.co/datasets/{repo_id}/tree/main/{sequence}/rgb",
        "```",
        "",
        "The TUM RGB-D benchmark is published by the Computer Vision Group at Technical",
        "University of Munich. The official dataset page states that, unless noted otherwise,",
        "the benchmark data is licensed under CC BY 4.0.",
        "",
        "Current files are renamed sparse-view RGB frames:",
        "",
        "| Local file | Original TUM RGB timestamp file |",
        "| --- | --- |",
    ]
    for index, remote_path in enumerate(selected_paths, start=1):
        local_name = f"frame_{index:06d}{Path(remote_path).suffix.lower()}"
        lines.append(f"| `images/{local_name}` | `{remote_path}` |")
    return "\n".join(lines) + "\n"


def _manifest_payload(
    scenes: list[dict[str, object]],
    args: argparse.Namespace,
) -> dict[str, object]:
    return {
        "name": "tum_rgbd_paper_subset",
        "version": "0.1",
        "root": ".",
        "sparse_view_counts": args.sparse_view_counts,
        "metadata": {
            "stage": "paper_experiments",
            "dataset": "TUM_RGBD",
            "source_repo": args.repo_id,
            "dataset_root": str(args.output_root.resolve()),
            "sample_mode": args.sample_mode,
            "start_index": args.start_index,
            "frame_stride": args.frame_stride,
            "num_frames_per_scene": args.num_frames,
        },
        "scenes": scenes,
    }


def _manifest_scene(scene_id: str, sequence: str, scene_dir: Path, image_names: Iterable[str], args: argparse.Namespace) -> dict[str, object]:
    scene_root = scene_dir.parent
    return {
        "scene_id": scene_id,
        "split": args.split,
        "scene_dir": str(scene_dir.resolve()),
        "images": list(image_names),
        "metadata": {
            "dataset": "TUM_RGBD",
            "sequence": sequence,
            "source_repo": args.repo_id,
            "source_scene_dir": str(scene_root.resolve()),
            "has_ground_truth_instances": False,
            "has_scene_graph_labels": False,
        },
    }


def main() -> None:
    args = parse_args()
    if args.num_frames <= 0:
        raise SystemExit("--num-frames must be positive")

    api = HfApi()
    if args.discover:
        sequences = _discover_sequences(api, args.repo_id)
        for sequence in sequences:
            print(sequence)
        print(f"Found {len(sequences)} sequence folders in {args.repo_id}")
        return

    scenes: list[dict[str, object]] = []
    for sequence in args.sequences:
        scene_id = _scene_id(sequence)
        print(f"Collecting {sequence} as {scene_id}", flush=True)
        try:
            rgb_paths = _list_rgb_files(api, args.repo_id, sequence)
        except Exception as exc:  # noqa: BLE001 - report and continue with remaining sequences.
            print(f"Skipping {sequence}: could not list RGB files ({exc})")
            continue

        if not rgb_paths:
            print(f"Skipping {sequence}: no RGB images found")
            continue

        selected_paths = _sample_paths(rgb_paths, args)
        scene_root = args.output_root / scene_id
        images_dir = scene_root / "images"
        image_names: list[str] = []
        for index, remote_path in enumerate(selected_paths, start=1):
            local_name = f"frame_{index:06d}{Path(remote_path).suffix.lower()}"
            image_names.append(local_name)
            if args.dry_run:
                continue
            _copy_remote_frame(args.repo_id, remote_path, images_dir / local_name, args.force)
            print(f"  [{index:02d}/{len(selected_paths):02d}] {remote_path} -> {local_name}", flush=True)

        if not args.dry_run:
            scene_root.mkdir(parents=True, exist_ok=True)
            (scene_root / "DATASET.md").write_text(
                _dataset_readme(sequence, selected_paths, args.repo_id),
                encoding="utf-8",
            )

        scenes.append(_manifest_scene(scene_id, sequence, images_dir, image_names, args))
        print(f"Selected {len(selected_paths)} / {len(rgb_paths)} RGB frames for {scene_id}", flush=True)

    manifest = _manifest_payload(scenes, args)
    if args.dry_run:
        print(json.dumps(manifest, indent=2))
        return

    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(scenes)} scenes to {args.manifest_output}", flush=True)


if __name__ == "__main__":
    main()
