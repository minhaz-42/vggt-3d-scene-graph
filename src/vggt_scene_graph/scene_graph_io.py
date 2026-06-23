from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .types import ObjectNode, RelationEdge, SceneGraph


def _array_summary(array: np.ndarray, max_rows: int = 0) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "shape": list(array.shape),
        "dtype": str(array.dtype),
    }
    if array.size:
        summary["min"] = float(np.nanmin(array))
        summary["max"] = float(np.nanmax(array))
    if max_rows > 0 and array.ndim == 2:
        summary["sample"] = array[:max_rows].round(6).tolist()
    return summary


def node_to_dict(node: ObjectNode, include_point_sample: int = 0) -> dict[str, Any]:
    payload = {
        "node_id": node.node_id,
        "proposal_ids": node.proposal_ids,
        "centroid_xyz": node.centroid_xyz.round(6).tolist(),
        "num_points": int(node.points_xyz.shape[0]) if node.points_xyz.ndim == 2 else int(node.points_xyz.size),
        "points_summary": _array_summary(node.points_xyz, max_rows=include_point_sample),
        "label": node.label,
        "uncertainty": float(node.uncertainty),
        "metadata": node.metadata,
    }
    if node.feature is not None:
        payload["feature_summary"] = _array_summary(node.feature)
    return payload


def relation_to_dict(edge: RelationEdge) -> dict[str, Any]:
    return {
        "subject_id": edge.subject_id,
        "relation": edge.relation,
        "object_id": edge.object_id,
        "confidence": float(edge.confidence),
    }


def scene_graph_to_dict(scene_graph: SceneGraph, include_point_sample: int = 0) -> dict[str, Any]:
    return {
        "scene_id": scene_graph.scene_id,
        "num_nodes": len(scene_graph.nodes),
        "num_relations": len(scene_graph.relations),
        "nodes": [node_to_dict(node, include_point_sample=include_point_sample) for node in scene_graph.nodes],
        "relations": [relation_to_dict(edge) for edge in scene_graph.relations],
    }


def write_scene_graph_json(path: Path, scene_graph: SceneGraph, include_point_sample: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = scene_graph_to_dict(scene_graph, include_point_sample=include_point_sample)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
