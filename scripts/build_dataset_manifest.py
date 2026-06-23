from __future__ import annotations

import argparse
import json
from pathlib import Path

from vggt_scene_graph.geometry_io import list_scene_images


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a dataset manifest from benchmark scene image folders.")
    parser.add_argument("--dataset-root", type=Path, required=True, help="Root containing one folder per scene.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--name", default="sparse_view_benchmark")
    parser.add_argument("--version", default="0.1")
    parser.add_argument("--split", default="val")
    parser.add_argument("--scene-glob", default="*")
    parser.add_argument("--images-subdir", default="images", help="Subfolder inside each scene; use . for scene root.")
    parser.add_argument("--max-scenes", type=int)
    parser.add_argument("--max-images-per-scene", type=int)
    parser.add_argument("--view-stride", type=int, default=1)
    parser.add_argument("--sparse-view-counts", type=int, nargs="+", default=[3, 5, 8, 10])
    parser.add_argument("--dataset-label", default="benchmark_subset")
    return parser.parse_args()


def _select_images(scene_dir: Path, max_images: int | None, stride: int) -> list[Path]:
    images = list_scene_images(scene_dir)
    stride = max(stride, 1)
    images = images[::stride]
    if max_images is not None:
        images = images[:max_images]
    return images


def main() -> None:
    args = parse_args()
    scene_roots = sorted(path for path in args.dataset_root.glob(args.scene_glob) if path.is_dir())
    if args.max_scenes is not None:
        scene_roots = scene_roots[: args.max_scenes]

    scenes = []
    for scene_root in scene_roots:
        scene_dir = scene_root / args.images_subdir
        if args.images_subdir == ".":
            scene_dir = scene_root
        images = _select_images(scene_dir, args.max_images_per_scene, args.view_stride)
        if not images:
            print(f"Skipping {scene_root}: no images found in {scene_dir}")
            continue
        scenes.append(
            {
                "scene_id": scene_root.name,
                "split": args.split,
                "scene_dir": str(scene_dir.resolve()),
                "images": [path.name for path in images],
                "metadata": {
                    "dataset": args.dataset_label,
                    "source_scene_dir": str(scene_root.resolve()),
                    "has_ground_truth_instances": False,
                    "has_scene_graph_labels": False,
                },
            }
        )

    payload = {
        "name": args.name,
        "version": args.version,
        "root": ".",
        "sparse_view_counts": args.sparse_view_counts,
        "metadata": {
            "stage": "paper_experiments",
            "dataset_root": str(args.dataset_root.resolve()),
            "dataset_label": args.dataset_label,
            "images_subdir": args.images_subdir,
            "view_stride": args.view_stride,
        },
        "scenes": scenes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(scenes)} scenes to {args.output}")


if __name__ == "__main__":
    main()
