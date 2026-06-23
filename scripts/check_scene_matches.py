from __future__ import annotations

import argparse
import json
from pathlib import Path

from vggt_scene_graph.geometry_io import list_scene_images
from vggt_scene_graph.image_matching import pairwise_scene_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether scene images have enough shared visual structure.")
    parser.add_argument("--scene-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/scene_match_report.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_paths = list_scene_images(args.scene_dir)
    if len(image_paths) < 2:
        raise SystemExit("Need at least two images for pairwise matching.")

    reports = pairwise_scene_report(image_paths)
    payload = {
        "scene_dir": str(args.scene_dir),
        "num_images": len(image_paths),
        "images": [path.name for path in image_paths],
        "pairwise_reports": reports,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote scene match report to {args.output}")
    for report in reports:
        print(
            f"{report['left_image']} <-> {report['right_image']}: "
            f"good={report['good_matches']}, ratio={report['match_ratio']:.4f}"
        )


if __name__ == "__main__":
    main()
