from __future__ import annotations

import argparse
import json
from pathlib import Path

from vggt_scene_graph.geometry_io import list_scene_images
from vggt_scene_graph.proposals import connected_component_proposals, proposal_record_dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run lightweight local 2D proposal extraction.")
    parser.add_argument("--scene-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/2d_proposals.json"))
    parser.add_argument("--min-area", type=int, default=512)
    parser.add_argument("--max-proposals-per-image", type=int, default=20)
    parser.add_argument("--no-masks", action="store_true", help="Store only boxes, not RLE masks.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_paths = list_scene_images(args.scene_dir)
    if not image_paths:
        raise SystemExit(f"No images found in {args.scene_dir}")

    records: list[dict[str, object]] = []
    counts_by_image: dict[str, int] = {}
    for image_path in image_paths:
        proposals = connected_component_proposals(
            image_path,
            view_id=image_path.stem,
            min_area=args.min_area,
            max_proposals=args.max_proposals_per_image,
        )
        counts_by_image[image_path.name] = len(proposals)
        records.extend(proposal_record_dict(proposal, include_mask=not args.no_masks) for proposal in proposals)

    payload = {
        "scene_dir": str(args.scene_dir),
        "backend": "opencv_connected_components",
        "mask_encoding": None if args.no_masks else "simple_rle_c_order",
        "num_images": len(image_paths),
        "num_proposals": len(records),
        "counts_by_image": counts_by_image,
        "proposals": records,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} proposal records to {args.output}")
    for image_name, count in counts_by_image.items():
        print(f"{image_name}: {count} proposals")


if __name__ == "__main__":
    main()
