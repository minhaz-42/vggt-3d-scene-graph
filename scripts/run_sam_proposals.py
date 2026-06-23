from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from vggt_scene_graph.geometry_io import list_scene_images
from vggt_scene_graph.masking import encode_binary_mask_rle
from vggt_scene_graph.proposals import mask_to_bbox


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SAM automatic mask proposals for a scene.")
    parser.add_argument("--scene-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--image-name", action="append", default=[], help="Specific image filename to process.")
    parser.add_argument("--model-type", default="vit_h", choices=["vit_h", "vit_l", "vit_b"])
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--min-area", type=int, default=512)
    parser.add_argument("--max-proposals-per-image", type=int, default=50)
    parser.add_argument("--max-image-side", type=int, default=1024, help="Resize long side before SAM; 0 disables.")
    parser.add_argument("--points-per-side", type=int, default=16)
    parser.add_argument("--pred-iou-thresh", type=float, default=0.88)
    parser.add_argument("--stability-score-thresh", type=float, default=0.95)
    return parser.parse_args()


def _load_generator(args: argparse.Namespace):
    try:
        from segment_anything import SamAutomaticMaskGenerator, sam_model_registry
    except ImportError as exc:
        raise RuntimeError(
            "SAM proposals require the `segment-anything` package. Install optional dependencies first, "
            "then provide a SAM checkpoint with --checkpoint."
        ) from exc

    if not args.checkpoint.exists():
        raise FileNotFoundError(f"SAM checkpoint not found: {args.checkpoint}")

    model = sam_model_registry[args.model_type](checkpoint=str(args.checkpoint))
    model.to(device=args.device)
    return SamAutomaticMaskGenerator(
        model,
        points_per_side=args.points_per_side,
        pred_iou_thresh=args.pred_iou_thresh,
        stability_score_thresh=args.stability_score_thresh,
    )


def _resize_for_sam(image_rgb, max_image_side: int):
    if max_image_side <= 0:
        return image_rgb
    height, width = image_rgb.shape[:2]
    long_side = max(height, width)
    if long_side <= max_image_side:
        return image_rgb
    scale = max_image_side / float(long_side)
    new_size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    return cv2.resize(image_rgb, new_size, interpolation=cv2.INTER_AREA)


def _mask_to_original_size(mask: np.ndarray, original_hw: tuple[int, int]) -> np.ndarray:
    original_h, original_w = original_hw
    if mask.shape[:2] == (original_h, original_w):
        return mask
    resized = cv2.resize(mask.astype(np.uint8), (original_w, original_h), interpolation=cv2.INTER_NEAREST)
    return resized > 0


def _record_from_sam_mask(
    mask_payload: dict[str, object],
    view_id: str,
    index: int,
    image_area: int,
    original_hw: tuple[int, int],
) -> dict[str, object]:
    mask = _mask_to_original_size(mask_payload["segmentation"], original_hw)
    x1, y1, x2, y2 = mask_to_bbox(mask)
    area = int(mask.sum())
    return {
        "proposal_id": f"{view_id}_sam_{index:03d}",
        "view_id": view_id,
        "bbox_xyxy": [x1, y1, x2, y2],
        "mask_area": area,
        "image_area": image_area,
        "confidence": float(mask_payload.get("predicted_iou", mask_payload.get("stability_score", 1.0))),
        "backend": "sam_automatic_mask_generator",
        "label_hint": "sam_mask",
        "sam_predicted_iou": float(mask_payload.get("predicted_iou", 0.0)),
        "sam_stability_score": float(mask_payload.get("stability_score", 0.0)),
        "mask_rle": encode_binary_mask_rle(mask),
    }


def main() -> None:
    args = parse_args()
    if args.image_name:
        image_paths = [args.scene_dir / image_name for image_name in args.image_name]
    else:
        image_paths = list_scene_images(args.scene_dir)
    if not image_paths:
        raise SystemExit(f"No images found in {args.scene_dir}")
    missing = [path for path in image_paths if not path.exists()]
    if missing:
        raise SystemExit(f"Selected image files do not exist: {', '.join(str(path) for path in missing)}")

    generator = _load_generator(args)
    records: list[dict[str, object]] = []
    counts_by_image: dict[str, int] = {}
    for image_path in image_paths:
        image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError(f"Could not read image: {image_path}")
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        sam_image_rgb = _resize_for_sam(image_rgb, args.max_image_side)
        original_hw = image_rgb.shape[:2]
        image_area = int(image_bgr.shape[0] * image_bgr.shape[1])
        masks = generator.generate(sam_image_rgb)
        records_for_image = []
        for mask in masks:
            record = _record_from_sam_mask(mask, image_path.stem, len(records_for_image) + 1, image_area, original_hw)
            if int(record["mask_area"]) >= args.min_area:
                records_for_image.append(record)
        records_for_image.sort(key=lambda record: int(record["mask_area"]), reverse=True)
        records_for_image = records_for_image[: args.max_proposals_per_image]
        counts_by_image[image_path.name] = len(records_for_image)
        records.extend(records_for_image)

    payload = {
        "scene_dir": str(args.scene_dir),
        "backend": "sam_automatic_mask_generator",
        "model_type": args.model_type,
        "checkpoint": str(args.checkpoint),
        "max_image_side": args.max_image_side,
        "points_per_side": args.points_per_side,
        "pred_iou_thresh": args.pred_iou_thresh,
        "stability_score_thresh": args.stability_score_thresh,
        "mask_encoding": "simple_rle_c_order",
        "num_images": len(image_paths),
        "num_proposals": len(records),
        "counts_by_image": counts_by_image,
        "proposals": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} SAM proposal records to {args.output}")
    for image_name, count in counts_by_image.items():
        print(f"{image_name}: {count} proposals")


if __name__ == "__main__":
    main()
