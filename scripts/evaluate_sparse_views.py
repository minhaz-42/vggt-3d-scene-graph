from __future__ import annotations

import argparse
import json
from pathlib import Path

from vggt_scene_graph.datasets import load_dataset_manifest, sparse_view_split
from vggt_scene_graph.geometry_io import list_scene_images


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create sparse-view experiment split records.")
    parser.add_argument("--dataset", type=Path, help="Dataset manifest JSON.")
    parser.add_argument("--scene-dir", type=Path, help="Directory containing scene images for direct mode.")
    parser.add_argument("--views", type=int, nargs="+", help="View counts. Defaults to manifest counts or 3/5/8/10.")
    parser.add_argument("--output", type=Path, default=Path("results/sparse_view_splits.json"))
    return parser.parse_args()


def _direct_scene_records(scene_dir: Path, view_counts: list[int]) -> list[dict[str, object]]:
    images = list_scene_images(scene_dir)
    records = []
    for view_count in view_counts:
        selected = sparse_view_split(images, view_count)
        records.append(
            {
                "scene_id": scene_dir.name,
                "split": "direct",
                "view_count": view_count,
                "available_views": len(images),
                "selected_images": [path.name for path in selected],
            }
        )
    return records


def _manifest_scene_records(dataset_path: Path, view_counts: list[int] | None) -> tuple[dict[str, object], list[dict[str, object]]]:
    manifest = load_dataset_manifest(dataset_path)
    counts = view_counts or manifest.sparse_view_counts
    records = []
    for scene in manifest.scenes:
        for view_count in counts:
            selected = sparse_view_split(scene.image_paths, view_count)
            records.append(
                {
                    "scene_id": scene.scene_id,
                    "split": scene.split,
                    "view_count": view_count,
                    "available_views": len(scene.image_paths),
                    "selected_images": [path.name for path in selected],
                    "scene_dir": str(scene.scene_dir),
                    "geometry_path": str(scene.geometry_path) if scene.geometry_path else None,
                    "proposals_path": str(scene.proposals_path) if scene.proposals_path else None,
                }
            )

    metadata = {
        "dataset_name": manifest.name,
        "dataset_version": manifest.version,
        "dataset_path": str(dataset_path),
        "num_scenes": len(manifest.scenes),
    }
    return metadata, records


def main() -> None:
    args = parse_args()
    if args.dataset:
        metadata, records = _manifest_scene_records(args.dataset, args.views)
    else:
        if args.scene_dir is None:
            raise SystemExit("Provide --dataset or --scene-dir.")
        counts = args.views or [3, 5, 8, 10]
        metadata = {"dataset_name": "direct_scene_dir", "scene_dir": str(args.scene_dir)}
        records = _direct_scene_records(args.scene_dir, counts)

    payload = {
        "metadata": metadata,
        "num_records": len(records),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} sparse-view split records to {args.output}")
    for record in records:
        print(f"{record['scene_id']} {record['view_count']} views: {record['selected_images']}")


if __name__ == "__main__":
    main()
