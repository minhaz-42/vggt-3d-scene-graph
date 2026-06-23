from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class ViewGeometry:
    """Geometry predicted for one input view."""

    view_id: str
    camera_intrinsic: np.ndarray
    camera_extrinsic: np.ndarray
    depth: np.ndarray
    depth_confidence: np.ndarray | None = None


@dataclass(slots=True)
class MaskProposal:
    """A 2D object proposal and its associated features."""

    proposal_id: str
    view_id: str
    mask: np.ndarray
    bbox_xyxy: tuple[int, int, int, int]
    clip_feature: np.ndarray | None = None
    dino_feature: np.ndarray | None = None
    confidence: float = 1.0
    label_hint: str | None = None


@dataclass(slots=True)
class ObjectNode:
    """A lifted 3D object candidate."""

    node_id: str
    proposal_ids: list[str]
    points_xyz: np.ndarray
    centroid_xyz: np.ndarray
    feature: np.ndarray | None = None
    label: str | None = None
    uncertainty: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RelationEdge:
    """A spatial relation between two object nodes."""

    subject_id: str
    relation: str
    object_id: str
    confidence: float


@dataclass(slots=True)
class SceneGraph:
    """Language-grounded 3D scene graph output."""

    scene_id: str
    nodes: list[ObjectNode]
    relations: list[RelationEdge]
