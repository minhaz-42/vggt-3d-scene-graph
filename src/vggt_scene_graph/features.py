from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import cv2
import numpy as np
from PIL import Image

from .masking import decode_binary_mask_rle


class ProposalFeatureExtractor(Protocol):
    backend_name: str
    model_name: str

    def extract(self, image_bgr: np.ndarray, record: dict[str, Any]) -> np.ndarray:
        ...


def _bbox(record: dict[str, Any]) -> tuple[int, int, int, int]:
    values = record["bbox_xyxy"]
    return (int(values[0]), int(values[1]), int(values[2]), int(values[3]))


def _masked_crop(image_bgr: np.ndarray, record: dict[str, Any]) -> np.ndarray:
    x1, y1, x2, y2 = _bbox(record)
    x1 = max(0, min(x1, image_bgr.shape[1]))
    x2 = max(0, min(x2, image_bgr.shape[1]))
    y1 = max(0, min(y1, image_bgr.shape[0]))
    y2 = max(0, min(y2, image_bgr.shape[0]))
    if x2 <= x1 or y2 <= y1:
        return np.zeros((1, 1, 3), dtype=np.uint8)

    crop = image_bgr[y1:y2, x1:x2].copy()
    if "mask_rle" not in record:
        return crop

    mask = decode_binary_mask_rle(record["mask_rle"])[y1:y2, x1:x2]
    if mask.shape[:2] != crop.shape[:2]:
        return crop

    background = np.zeros_like(crop)
    return np.where(mask[..., None], crop, background)


@dataclass(slots=True)
class HandcraftedColorFeatureExtractor:
    backend_name: str = "handcrafted_color"
    model_name: str = "hsv_histogram_color_moments_v1"

    def extract(self, image_bgr: np.ndarray, record: dict[str, Any]) -> np.ndarray:
        crop = _masked_crop(image_bgr, record)
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        valid = np.any(crop > 0, axis=-1)
        if not valid.any():
            valid = np.ones(crop.shape[:2], dtype=bool)

        hist = cv2.calcHist(
            [hsv],
            channels=[0, 1, 2],
            mask=valid.astype(np.uint8),
            histSize=[8, 4, 4],
            ranges=[0, 180, 0, 256, 0, 256],
        ).reshape(-1)
        hist = hist / max(float(hist.sum()), 1.0)

        pixels = crop[valid].astype(np.float32) / 255.0
        mean = pixels.mean(axis=0)
        std = pixels.std(axis=0)
        x1, y1, x2, y2 = _bbox(record)
        image_h, image_w = image_bgr.shape[:2]
        geometry = np.array(
            [
                (x2 - x1) / max(float(image_w), 1.0),
                (y2 - y1) / max(float(image_h), 1.0),
                ((x1 + x2) / 2.0) / max(float(image_w), 1.0),
                ((y1 + y2) / 2.0) / max(float(image_h), 1.0),
                float(record.get("mask_area", 0)) / max(float(record.get("image_area", image_h * image_w)), 1.0),
            ],
            dtype=np.float32,
        )

        feature = np.concatenate([hist.astype(np.float32), mean, std, geometry])
        norm = float(np.linalg.norm(feature))
        if norm > 0:
            feature = feature / norm
        return feature.astype(np.float32)


class TransformersImageFeatureExtractor:
    def __init__(
        self,
        model_name: str,
        backend_name: str = "transformers_image",
        device: str = "cpu",
    ) -> None:
        try:
            import torch
            from transformers import AutoImageProcessor, AutoModel
        except ImportError as exc:
            raise RuntimeError(
                "The transformers feature backend requires `transformers`. Install it first, then rerun."
            ) from exc

        self.backend_name = backend_name
        self.model_name = model_name
        self.device = device
        self._torch = torch
        if backend_name == "clip":
            from transformers import AutoProcessor, CLIPModel

            self._processor = AutoProcessor.from_pretrained(model_name)
            self._model = CLIPModel.from_pretrained(model_name).to(device)
        else:
            self._processor = AutoImageProcessor.from_pretrained(model_name)
            self._model = AutoModel.from_pretrained(model_name).to(device)
        self._model.eval()

    def extract(self, image_bgr: np.ndarray, record: dict[str, Any]) -> np.ndarray:
        crop_bgr = _masked_crop(image_bgr, record)
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(crop_rgb)
        inputs = self._processor(images=image, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with self._torch.inference_mode():
            if self.backend_name == "clip":
                outputs = self._model.get_image_features(**inputs)
                if isinstance(outputs, self._torch.Tensor):
                    feature = outputs[0]
                elif hasattr(outputs, "image_embeds") and outputs.image_embeds is not None:
                    feature = outputs.image_embeds[0]
                elif hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                    feature = outputs.pooler_output
                    if (
                        hasattr(self._model, "visual_projection")
                        and feature.shape[-1] == self._model.visual_projection.in_features
                    ):
                        feature = self._model.visual_projection(feature)
                    feature = feature[0]
                else:
                    vision_outputs = self._model.vision_model(**inputs)
                    feature = vision_outputs.pooler_output
                    if (
                        hasattr(self._model, "visual_projection")
                        and feature.shape[-1] == self._model.visual_projection.in_features
                    ):
                        feature = self._model.visual_projection(feature)
                    feature = feature[0]
            else:
                outputs = self._model(**inputs)

                if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                    feature = outputs.pooler_output[0]
                elif hasattr(outputs, "last_hidden_state"):
                    feature = outputs.last_hidden_state[:, 0][0]
                else:
                    raise RuntimeError(f"Could not identify feature tensor in outputs for {self.model_name}.")

        feature = feature.detach().cpu().float().numpy()
        feature = np.asarray(feature, dtype=np.float32).reshape(-1)
        norm = float(np.linalg.norm(feature))
        if norm > 0:
            feature = feature / norm
        return feature.astype(np.float32)


def make_feature_extractor(
    backend: str = "handcrafted_color",
    model_name: str | None = None,
    device: str = "cpu",
) -> ProposalFeatureExtractor:
    if backend == "handcrafted_color":
        return HandcraftedColorFeatureExtractor()
    if backend in {"transformers", "clip", "dinov2"}:
        if model_name is None:
            model_name = "openai/clip-vit-base-patch32" if backend == "clip" else "facebook/dinov2-base"
        return TransformersImageFeatureExtractor(model_name=model_name, backend_name=backend, device=device)
    raise ValueError(f"Unknown feature backend: {backend}")


def extract_features_for_records(
    scene_dir: Path,
    records: list[dict[str, Any]],
    extractor: ProposalFeatureExtractor,
) -> list[dict[str, Any]]:
    image_cache: dict[str, np.ndarray] = {}
    output_records = []
    for record in records:
        image_name = f"{record['view_id']}.jpg"
        image_path = scene_dir / image_name
        if not image_path.exists():
            image_path = scene_dir / f"{record['view_id']}.png"
        if str(image_path) not in image_cache:
            image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"Could not read image for feature extraction: {image_path}")
            image_cache[str(image_path)] = image

        feature = extractor.extract(image_cache[str(image_path)], record)
        updated = dict(record)
        features = dict(updated.get("features", {}))
        features[extractor.backend_name] = {
            "model_name": extractor.model_name,
            "dim": int(feature.shape[0]),
            "normalized": True,
            "vector": feature.round(8).tolist(),
        }
        updated["features"] = features
        output_records.append(updated)
    return output_records
