from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from vggt_scene_graph.geometry_io import list_scene_images
from vggt_scene_graph.masking import encode_binary_mask_rle

"""Open-vocabulary object proposals via OWLv2 (drop-in replacement for run_sam_proposals.py).

Why this exists: the previous proposal stage (SAM automatic masks + CLIP-per-patch labeling)
produced surface/background fragments that CLIP then mislabeled as room-scale categories
(floor/curtain/bed/...), making the open-vocabulary object claim false and the eval circular.
OWLv2 is a genuine open-vocabulary *detector*: given the indoor vocabulary as text queries, it
returns object boxes WITH labels directly. The label is carried in `label_hint`, which the
lifting stage maps to `ObjectNode.label` — so the real label flows through with no separate
CLIP-text-similarity labeling step.

Output schema matches run_sam_proposals.py so this is a drop-in for the `proposals` stage:
each record has proposal_id / view_id / bbox_xyxy / mask_area / image_area / confidence /
backend / label_hint, plus owlv2_label, owlv2_score, and label_candidates. If a SAM checkpoint
is supplied, each detection box is turned into a clean instance mask (box-prompted SAM) and a
`mask_rle` is added so the lifting stage selects only object pixels (not the bbox background).
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OWLv2 open-vocabulary object proposals for a scene.")
    parser.add_argument("--scene-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True, help="Open-vocab label vocabulary JSON.")
    parser.add_argument("--image-name", action="append", default=[], help="Specific image filename to process.")
    parser.add_argument("--owlv2-model", default="google/owlv2-base-patch16-ensemble")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--threshold", type=float, default=0.2, help="Detection score threshold.")
    parser.add_argument("--nms-iou", type=float, default=0.5, help="Per-class NMS IoU; <=0 disables NMS.")
    parser.add_argument("--max-detections-per-image", type=int, default=30)
    parser.add_argument("--top-k-label-candidates", type=int, default=3)
    parser.add_argument("--exclude-label", action="append", default=["unknown object"],
                        help="Vocab entries to NOT use as detection queries (repeatable).")
    parser.add_argument("--prompt-template", default="{}",
                        help="Query text template, e.g. 'a photo of a {}'. Default is the bare label.")
    parser.add_argument("--local-files-only", action="store_true", help="Load OWLv2 only from local cache.")
    # Optional SAM box-prompted masks for clean 3D lifting.
    parser.add_argument("--sam-checkpoint", type=Path, help="If set, refine each box into a mask via box-prompted SAM.")
    parser.add_argument("--sam-model-type", default="vit_b", choices=["vit_h", "vit_l", "vit_b"])
    parser.add_argument("--sam-device", help="Device for SAM; defaults to --device.")
    return parser.parse_args()


def _resolve_device(name: str) -> str:
    import torch

    if name != "auto":
        return name
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _load_queries(path: Path, exclude: list[str], template: str) -> tuple[list[str], list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    labels = payload.get("labels", payload) if isinstance(payload, dict) else payload
    labels = [str(label).strip() for label in labels if str(label).strip()]
    excluded = {e.strip() for e in exclude}
    label_names = [label for label in labels if label not in excluded]
    if not label_names:
        raise SystemExit(f"No usable labels in {path} after excluding {sorted(excluded)}.")
    prompts = [template.format(label) for label in label_names]
    return label_names, prompts


def _load_owlv2(model_name: str, device: str, local_files_only: bool):
    import torch  # noqa: F401
    from transformers import Owlv2ForObjectDetection, Owlv2Processor

    processor = Owlv2Processor.from_pretrained(model_name, local_files_only=local_files_only)
    model = Owlv2ForObjectDetection.from_pretrained(model_name, local_files_only=local_files_only)
    model = model.to(device).eval()
    return processor, model


def _per_class_nms(boxes, scores, labels, iou: float):
    import torch
    from torchvision.ops import nms

    if iou <= 0 or len(scores) == 0:
        return torch.arange(len(scores))
    keep: list = []
    for cls in labels.unique():
        idx = (labels == cls).nonzero(as_tuple=True)[0]
        kept = nms(boxes[idx].float(), scores[idx].float(), iou)
        keep.append(idx[kept])
    return torch.cat(keep) if keep else torch.empty(0, dtype=torch.long)


class _SamMasker:
    """Box-prompted SAM: turn a detection box into a clean instance mask."""

    def __init__(self, checkpoint: Path, model_type: str, device: str) -> None:
        try:
            from segment_anything import SamPredictor, sam_model_registry
        except ImportError as exc:
            raise RuntimeError("Box-prompted masks need the `segment-anything` package.") from exc
        if not checkpoint.exists():
            raise FileNotFoundError(f"SAM checkpoint not found: {checkpoint}")
        sam = sam_model_registry[model_type](checkpoint=str(checkpoint)).to(device)
        self._predictor = SamPredictor(sam)
        self._current_view: str | None = None

    def set_image(self, view_id: str, image_rgb: np.ndarray) -> None:
        if self._current_view != view_id:
            self._predictor.set_image(image_rgb)
            self._current_view = view_id

    def mask_for_box(self, box_xyxy: tuple[int, int, int, int]) -> np.ndarray:
        masks, scores, _ = self._predictor.predict(
            box=np.asarray(box_xyxy, dtype=np.float32), multimask_output=False
        )
        return masks[0].astype(bool)


def main() -> None:
    args = parse_args()
    device = _resolve_device(args.device)
    sam_device = args.sam_device or device

    if args.image_name:
        image_paths = [args.scene_dir / name for name in args.image_name]
    else:
        image_paths = list_scene_images(args.scene_dir)
    if not image_paths:
        raise SystemExit(f"No images found in {args.scene_dir}")
    missing = [p for p in image_paths if not p.exists()]
    if missing:
        raise SystemExit(f"Selected image files do not exist: {', '.join(str(p) for p in missing)}")

    label_names, prompts = _load_queries(args.labels, args.exclude_label, args.prompt_template)
    print(f"device={device} threshold={args.threshold} nms_iou={args.nms_iou} "
          f"n_queries={len(label_names)} sam_masks={args.sam_checkpoint is not None}")

    import torch

    processor, model = _load_owlv2(args.owlv2_model, device, args.local_files_only)
    masker = (
        _SamMasker(args.sam_checkpoint, args.sam_model_type, sam_device)
        if args.sam_checkpoint is not None
        else None
    )

    records: list[dict[str, Any]] = []
    counts_by_image: dict[str, int] = {}
    for image_path in image_paths:
        image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError(f"Could not read image: {image_path}")
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        height, width = image_rgb.shape[:2]
        image_area = int(height * width)
        view_id = image_path.stem

        from PIL import Image

        inputs = processor(text=[prompts], images=Image.fromarray(image_rgb), return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)
        target_sizes = torch.tensor([(height, width)]).to(device)
        result = processor.post_process_grounded_object_detection(
            outputs, target_sizes=target_sizes, threshold=args.threshold
        )[0]

        boxes = result["boxes"].detach().cpu()
        scores = result["scores"].detach().cpu()
        labels = result["labels"].detach().cpu()

        keep = _per_class_nms(boxes, scores, labels, args.nms_iou)
        keep = keep[torch.argsort(scores[keep], descending=True)][: args.max_detections_per_image]

        records_for_image: list[dict[str, Any]] = []
        if masker is not None and len(keep):
            masker.set_image(view_id, image_rgb)
        for rank, i in enumerate(keep.tolist()):
            x1, y1, x2, y2 = boxes[i].tolist()
            x1 = int(np.clip(np.floor(x1), 0, width))
            y1 = int(np.clip(np.floor(y1), 0, height))
            x2 = int(np.clip(np.ceil(x2), 0, width))
            y2 = int(np.clip(np.ceil(y2), 0, height))
            if x2 <= x1 or y2 <= y1:
                continue
            label = label_names[int(labels[i])]
            score = float(scores[i])

            record: dict[str, Any] = {
                "proposal_id": f"{view_id}_owlv2_{rank + 1:03d}",
                "view_id": view_id,
                "bbox_xyxy": [x1, y1, x2, y2],
                "image_area": image_area,
                "confidence": score,
                "backend": "owlv2" if masker is None else "owlv2+sam",
                "label_hint": label,          # -> ObjectNode.label via lifting
                "owlv2_label": label,
                "owlv2_score": score,
            }

            if masker is not None:
                mask = masker.mask_for_box((x1, y1, x2, y2))
                record["mask_area"] = int(mask.sum())
                record["mask_rle"] = encode_binary_mask_rle(mask)
            else:
                # No mask: lifting falls back to the bbox rectangle. Report the bbox area.
                record["mask_area"] = int((x2 - x1) * (y2 - y1))

            records_for_image.append(record)

        counts_by_image[image_path.name] = len(records_for_image)
        records.extend(records_for_image)
        top = ", ".join(f"{r['owlv2_label']}:{r['owlv2_score']:.2f}" for r in records_for_image[:8])
        print(f"{image_path.name}: {len(records_for_image)} proposals | {top}")

    payload = {
        "scene_dir": str(args.scene_dir),
        "backend": "owlv2" if masker is None else "owlv2+sam",
        "owlv2_model": args.owlv2_model,
        "label_vocab_path": str(args.labels),
        "num_queries": len(label_names),
        "threshold": args.threshold,
        "nms_iou": args.nms_iou,
        "prompt_template": args.prompt_template,
        "mask_source": "box_prompted_sam" if masker is not None else "none",
        "sam_checkpoint": str(args.sam_checkpoint) if args.sam_checkpoint else None,
        "sam_model_type": args.sam_model_type if masker is not None else None,
        "mask_encoding": "simple_rle_c_order" if masker is not None else None,
        "num_images": len(image_paths),
        "num_proposals": len(records),
        "counts_by_image": counts_by_image,
        "proposals": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} OWLv2 proposal records to {args.output}")


if __name__ == "__main__":
    main()
