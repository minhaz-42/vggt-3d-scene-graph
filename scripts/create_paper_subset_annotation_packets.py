from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create annotation packets and visual review pages for a benchmark manifest."
    )
    parser.add_argument("--dataset", type=Path, required=True, help="Dataset manifest JSON.")
    parser.add_argument("--results-root", type=Path, required=True, help="Benchmark output root.")
    parser.add_argument("--output-root", type=Path, required=True, help="Annotation packet output root.")
    parser.add_argument("--view-count", type=int, default=10, help="View count to use as the annotation reference.")
    parser.add_argument(
        "--mode",
        choices=["pseudo_reference", "manual_review"],
        default="pseudo_reference",
        help="Annotation draft mode passed to create_annotation_packet.py.",
    )
    parser.add_argument(
        "--scene-id",
        action="append",
        default=[],
        help="Optional scene id to process. Repeat for multiple scenes.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate node/relation CSVs even if they already exist.",
    )
    parser.add_argument("--max-thumbnails-per-node", type=int, default=4)
    parser.add_argument("--thumbnail-long-side", type=int, default=260)
    return parser.parse_args()


def _load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _count_thumbnails(path: Path) -> int:
    thumbs_dir = path / "thumbnails"
    if not thumbs_dir.exists():
        return 0
    return sum(1 for candidate in thumbs_dir.iterdir() if candidate.is_file())


def _packet_name(scene_id: str, mode: str, view_count: int) -> str:
    suffix = "pseudo_from" if mode == "pseudo_reference" else "manual_from"
    return f"{scene_id}_{suffix}_{view_count:02d}view"


def main() -> None:
    args = parse_args()
    manifest = _load_manifest(args.dataset)
    selected_scene_ids = set(args.scene_id)
    project_root = Path.cwd()
    script_dir = Path(__file__).resolve().parent
    view_dir = f"views_{args.view_count:02d}"
    packets = []

    for scene in manifest.get("scenes", []):
        scene_id = str(scene.get("scene_id", ""))
        if selected_scene_ids and scene_id not in selected_scene_ids:
            continue

        scene_dir = Path(str(scene.get("scene_dir", "")))
        scene_graph = args.results_root / scene_id / view_dir / "scene_graph_labeled.json"
        proposals = args.results_root / scene_id / view_dir / "sam_proposals.json"
        output_dir = args.output_root / _packet_name(scene_id, args.mode, args.view_count)
        node_review = output_dir / "node_review.csv"
        relation_review = output_dir / "relation_review.csv"

        if not scene_graph.exists():
            raise FileNotFoundError(f"Missing scene graph: {scene_graph}")
        if not proposals.exists():
            raise FileNotFoundError(f"Missing proposals: {proposals}")
        if not scene_dir.exists():
            raise FileNotFoundError(f"Missing scene image directory: {scene_dir}")

        if args.overwrite or not (node_review.exists() and relation_review.exists()):
            _run(
                [
                    sys.executable,
                    str(script_dir / "create_annotation_packet.py"),
                    "--scene-graph",
                    str(scene_graph),
                    "--output-dir",
                    str(output_dir),
                    "--mode",
                    args.mode,
                ]
            )
        else:
            print(f"Keeping existing review CSVs in {output_dir}")

        _run(
            [
                sys.executable,
                str(script_dir / "render_annotation_review.py"),
                "--scene-graph",
                str(scene_graph),
                "--proposals",
                str(proposals),
                "--scene-dir",
                str(scene_dir),
                "--node-review",
                str(node_review),
                "--relation-review",
                str(relation_review),
                "--output-dir",
                str(output_dir),
                "--max-thumbnails-per-node",
                str(args.max_thumbnails_per_node),
                "--thumbnail-long-side",
                str(args.thumbnail_long_side),
            ]
        )

        packets.append(
            {
                "scene_id": scene_id,
                "view_count": args.view_count,
                "scene_graph": str(scene_graph),
                "proposals": str(proposals),
                "scene_dir": str(scene_dir),
                "packet_dir": str(output_dir),
                "annotation_review_html": str(output_dir / "annotation_review.html"),
                "node_review_csv": str(node_review),
                "relation_review_csv": str(relation_review),
                "annotation_draft_json": str(output_dir / "annotation_draft.json"),
                "node_rows": _count_csv_rows(node_review),
                "relation_rows": _count_csv_rows(relation_review),
                "thumbnail_count": _count_thumbnails(output_dir),
            }
        )

    if selected_scene_ids:
        missing = sorted(selected_scene_ids - {packet["scene_id"] for packet in packets})
        if missing:
            raise ValueError(f"Scene ids not found in manifest: {missing}")

    args.output_root.mkdir(parents=True, exist_ok=True)
    index_path = args.output_root / "annotation_packet_index.json"
    index_path.write_text(
        json.dumps(
            {
                "dataset": str(args.dataset),
                "results_root": str(args.results_root),
                "output_root": str(args.output_root),
                "view_count": args.view_count,
                "mode": args.mode,
                "packets": packets,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    relative_index = index_path.relative_to(project_root) if index_path.is_relative_to(project_root) else index_path
    print(f"Wrote {relative_index}")
    print(f"Created or refreshed {len(packets)} annotation review packets.")


if __name__ == "__main__":
    main()
