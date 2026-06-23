from __future__ import annotations

import numpy as np

from .types import ObjectNode, RelationEdge


def infer_pair_relation(
    subject: ObjectNode,
    obj: ObjectNode,
    near_threshold: float = 0.35,
    vertical_threshold: float = 0.08,
    max_distance: float | None = None,
) -> RelationEdge | None:
    delta = obj.centroid_xyz - subject.centroid_xyz
    distance = float(np.linalg.norm(delta))

    if max_distance is not None and distance > max_distance:
        return None

    if distance <= near_threshold:
        return RelationEdge(subject.node_id, "near", obj.node_id, confidence=1.0 - distance / near_threshold)

    if abs(delta[2]) > vertical_threshold:
        if delta[2] < 0:
            return RelationEdge(subject.node_id, "above", obj.node_id, confidence=min(1.0, abs(delta[2])))
        return RelationEdge(subject.node_id, "below", obj.node_id, confidence=min(1.0, abs(delta[2])))

    if abs(delta[0]) > abs(delta[1]):
        relation = "left_of" if delta[0] > 0 else "right_of"
    else:
        relation = "behind" if delta[1] > 0 else "in_front_of"

    return RelationEdge(subject.node_id, relation, obj.node_id, confidence=0.5)


def infer_relations(
    nodes: list[ObjectNode],
    near_threshold: float = 0.35,
    vertical_threshold: float = 0.08,
    max_distance: float | None = None,
) -> list[RelationEdge]:
    relations: list[RelationEdge] = []
    for subject in nodes:
        for obj in nodes:
            if subject.node_id == obj.node_id:
                continue
            relation = infer_pair_relation(
                subject,
                obj,
                near_threshold=near_threshold,
                vertical_threshold=vertical_threshold,
                max_distance=max_distance,
            )
            if relation is not None:
                relations.append(relation)
    return relations
