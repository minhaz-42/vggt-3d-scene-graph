from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .geometry_io import load_geometry_metadata, load_geometry_npz
from .masking import decode_binary_mask_rle, resize_mask
from .types import ObjectNode


@dataclass(slots=True)
class ProposalLiftRecord:
    proposal_id: str
    view_id: str
    bbox_xyxy: tuple[int, int, int, int]
    confidence: float
    mask_rle: dict[str, Any] | None
    metadata: dict[str, Any]


def _as_tuple4(values: object) -> tuple[int, int, int, int]:
    if not isinstance(values, list | tuple) or len(values) != 4:
        raise ValueError(f"Expected bbox_xyxy with four values, got {values!r}.")
    return (int(values[0]), int(values[1]), int(values[2]), int(values[3]))


def load_proposal_records(path: Path) -> list[ProposalLiftRecord]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in payload.get("proposals", []):
        records.append(
            ProposalLiftRecord(
                proposal_id=str(item["proposal_id"]),
                view_id=str(item["view_id"]),
                bbox_xyxy=_as_tuple4(item["bbox_xyxy"]),
                confidence=float(item.get("confidence", 1.0)),
                mask_rle=item.get("mask_rle"),
                metadata={
                    key: value
                    for key, value in item.items()
                    if key not in {"proposal_id", "view_id", "bbox_xyxy", "confidence", "mask_rle"}
                },
            )
        )
    return records


def _image_size(path: Path) -> tuple[int, int]:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read image size: {path}")
    height, width = image.shape[:2]
    return width, height


def _scale_bbox(
    bbox_xyxy: tuple[int, int, int, int],
    source_size_wh: tuple[int, int],
    target_size_wh: tuple[int, int],
) -> tuple[int, int, int, int]:
    source_w, source_h = source_size_wh
    target_w, target_h = target_size_wh
    sx = target_w / max(float(source_w), 1.0)
    sy = target_h / max(float(source_h), 1.0)
    x1, y1, x2, y2 = bbox_xyxy
    scaled = (
        int(np.floor(x1 * sx)),
        int(np.floor(y1 * sy)),
        int(np.ceil(x2 * sx)),
        int(np.ceil(y2 * sy)),
    )
    return (
        int(np.clip(scaled[0], 0, target_w)),
        int(np.clip(scaled[1], 0, target_h)),
        int(np.clip(scaled[2], 0, target_w)),
        int(np.clip(scaled[3], 0, target_h)),
    )


def _sample_points(points: np.ndarray, max_points: int, seed: int = 7) -> np.ndarray:
    if max_points <= 0 or len(points) <= max_points:
        return points
    rng = np.random.default_rng(seed)
    indices = rng.choice(len(points), size=max_points, replace=False)
    return points[np.sort(indices)]


def _point_box(points: np.ndarray) -> dict[str, list[float]]:
    mins = np.min(points, axis=0)
    maxs = np.max(points, axis=0)
    return {
        "min_xyz": mins.round(6).tolist(),
        "max_xyz": maxs.round(6).tolist(),
        "extent_xyz": (maxs - mins).round(6).tolist(),
    }


def _compactness_uncertainty(points: np.ndarray) -> float:
    if len(points) < 2:
        return 1.0
    distances = np.linalg.norm(points - np.median(points, axis=0), axis=1)
    spread = float(np.percentile(distances, 75))
    return float(np.clip(spread, 0.0, 1.0))


def _normalized_feature_vector(feature_payload: Any) -> np.ndarray | None:
    if not isinstance(feature_payload, dict) or "vector" not in feature_payload:
        return None
    vector = np.asarray(feature_payload["vector"], dtype=np.float32).reshape(-1)
    if vector.size == 0:
        return None
    norm = float(np.linalg.norm(vector))
    if norm > 0:
        vector = vector / norm
    return vector.astype(np.float32)


def _feature_from_metadata(metadata: dict[str, Any]) -> tuple[np.ndarray | None, list[str]]:
    features = metadata.get("features")
    if not isinstance(features, dict) or not features:
        return None, []

    combined_keys = ["clip", "dinov2"]
    combined_vectors: list[np.ndarray] = []
    used_backends: list[str] = []
    for feature_key in combined_keys:
        vector = _normalized_feature_vector(features.get(feature_key))
        if vector is not None:
            combined_vectors.append(vector)
            used_backends.append(feature_key)

    if len(combined_vectors) >= 2:
        feature = np.concatenate(combined_vectors).astype(np.float32)
        norm = float(np.linalg.norm(feature))
        if norm > 0:
            feature = feature / norm
        return feature.astype(np.float32), used_backends

    preferred = ["clip", "dinov2", "transformers_image", "handcrafted_color"]
    for feature_key in dict.fromkeys(preferred + sorted(features)):
        vector = _normalized_feature_vector(features.get(feature_key))
        if vector is not None:
            return vector, [feature_key]
    return None, []


def lift_proposal_record(
    record: ProposalLiftRecord,
    view_index: int,
    image_path: Path,
    world_points: np.ndarray,
    world_points_conf: np.ndarray | None,
    min_confidence: float = 0.2,
    max_points: int = 4096,
) -> ObjectNode | None:
    target_h, target_w = world_points.shape[:2]
    source_size = _image_size(image_path)
    bbox_scaled = _scale_bbox(record.bbox_xyxy, source_size, (target_w, target_h))
    x1, y1, x2, y2 = bbox_scaled
    if x2 <= x1 or y2 <= y1:
        return None

    if record.mask_rle is not None:
        source_mask = decode_binary_mask_rle(record.mask_rle)
        target_mask = resize_mask(source_mask, (target_w, target_h))
        target_mask &= np.isfinite(world_points).all(axis=-1)
    else:
        target_mask = np.zeros((target_h, target_w), dtype=bool)
        target_mask[y1:y2, x1:x2] = True

    proposal_points = world_points[target_mask].reshape(-1, 3)
    valid_mask = np.isfinite(proposal_points).all(axis=1)
    proposal_conf = None
    mean_conf = None
    if world_points_conf is not None:
        proposal_conf = world_points_conf[target_mask].reshape(-1)
        valid_mask &= proposal_conf >= min_confidence
        if valid_mask.any():
            mean_conf = float(np.mean(proposal_conf[valid_mask]))

    proposal_points = proposal_points[valid_mask]
    if len(proposal_points) == 0:
        return None

    sampled_points = _sample_points(proposal_points.astype(np.float32), max_points=max_points)
    centroid = np.mean(sampled_points, axis=0).astype(np.float32)
    uncertainty_from_conf = 1.0 - float(np.clip(mean_conf if mean_conf is not None else record.confidence, 0.0, 1.0))
    compactness_uncertainty = _compactness_uncertainty(sampled_points)
    uncertainty = float(np.clip(0.7 * uncertainty_from_conf + 0.3 * compactness_uncertainty, 0.0, 1.0))

    feature, feature_backends_used = _feature_from_metadata(record.metadata)

    return ObjectNode(
        node_id=f"obj_{record.proposal_id}",
        proposal_ids=[record.proposal_id],
        points_xyz=sampled_points,
        centroid_xyz=centroid,
        feature=feature,
        label=record.metadata.get("label_hint") or record.metadata.get("backend"),
        uncertainty=uncertainty,
        metadata={
            "view_id": record.view_id,
            "view_index": view_index,
            "image_path": str(image_path),
            "bbox_xyxy": list(record.bbox_xyxy),
            "bbox_geometry_xyxy": list(bbox_scaled),
            "used_mask_rle": record.mask_rle is not None,
            "proposal_confidence": record.confidence,
            "mean_world_point_confidence": mean_conf,
            "num_lifted_points": int(len(proposal_points)),
            "num_sampled_points": int(len(sampled_points)),
            "feature_backends_used": feature_backends_used,
            "feature_dim": int(feature.shape[0]) if feature is not None else None,
            "bbox_3d": _point_box(sampled_points),
            **record.metadata,
        },
    )


def lift_scene_proposals(
    geometry_path: Path,
    proposals_path: Path,
    min_confidence: float = 0.2,
    max_points_per_node: int = 4096,
) -> list[ObjectNode]:
    arrays = load_geometry_npz(geometry_path)
    metadata = load_geometry_metadata(geometry_path)
    image_paths = [Path(path) for path in metadata.get("image_paths", [])]
    view_ids = [path.stem for path in image_paths]
    view_index_by_id = {view_id: index for index, view_id in enumerate(view_ids)}
    proposals = load_proposal_records(proposals_path)

    if "world_points" not in arrays:
        raise ValueError(f"Geometry file {geometry_path} has no `world_points` array.")
    world_points = arrays["world_points"]
    if world_points.ndim != 5:
        raise ValueError(f"Expected world_points shape [B, V, H, W, 3], got {world_points.shape}.")
    world_points_conf = arrays.get("world_points_conf")

    nodes: list[ObjectNode] = []
    for record in proposals:
        view_index = view_index_by_id.get(record.view_id)
        if view_index is None:
            continue
        node = lift_proposal_record(
            record,
            view_index=view_index,
            image_path=image_paths[view_index],
            world_points=world_points[0, view_index],
            world_points_conf=world_points_conf[0, view_index] if world_points_conf is not None else None,
            min_confidence=min_confidence,
            max_points=max_points_per_node,
        )
        if node is not None:
            nodes.append(node)

    return nodes
