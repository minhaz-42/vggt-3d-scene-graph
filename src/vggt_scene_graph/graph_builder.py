from __future__ import annotations

from collections.abc import Iterable

import networkx as nx
import numpy as np

from .types import ObjectNode


def cosine_similarity(left: np.ndarray | None, right: np.ndarray | None) -> float:
    if left is None or right is None:
        return 0.0
    if left.shape != right.shape:
        return 0.0

    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    return float(np.dot(left, right) / (left_norm * right_norm))


def centroid_distance(left: ObjectNode, right: ObjectNode) -> float:
    return float(np.linalg.norm(left.centroid_xyz - right.centroid_xyz))


def geometry_affinity(left: ObjectNode, right: ObjectNode, sigma: float = 0.25) -> float:
    distance = centroid_distance(left, right)
    return float(np.exp(-(distance * distance) / max(sigma * sigma, 1e-8)))


def merge_score(
    left: ObjectNode,
    right: ObjectNode,
    semantic_weight: float = 0.45,
    geometry_weight: float = 0.30,
    uncertainty_weight: float = 0.10,
) -> float:
    semantic = cosine_similarity(left.feature, right.feature)
    geometry = geometry_affinity(left, right)
    certainty = 1.0 - min(1.0, (left.uncertainty + right.uncertainty) / 2.0)
    return semantic_weight * semantic + geometry_weight * geometry + uncertainty_weight * certainty


def build_candidate_graph(
    nodes: Iterable[ObjectNode],
    merge_threshold: float = 0.65,
) -> nx.Graph:
    node_list = list(nodes)
    graph = nx.Graph()

    for node in node_list:
        graph.add_node(node.node_id, object=node)

    for index, left in enumerate(node_list):
        for right in node_list[index + 1 :]:
            score = merge_score(left, right)
            if score >= merge_threshold:
                graph.add_edge(left.node_id, right.node_id, weight=score)

    return graph


def connected_components_as_clusters(graph: nx.Graph) -> list[list[str]]:
    return [list(component) for component in nx.connected_components(graph)]


def build_geometry_fusion_graph(
    nodes: Iterable[ObjectNode],
    distance_threshold: float = 0.15,
    feature_similarity_threshold: float | None = None,
    allow_same_view_edges: bool = False,
    *,
    use_uncertainty: bool = False,
    uncertainty_weight: float = 0.0,
    feature_uncertainty_weight: float = 0.0,
    uncertainty_agg: str = "max",
    min_shrink: float = 0.1,
    max_feature_threshold: float = 0.99,
    bridge_tau: float = 1.0,
    fixed_shrink: float = 1.0,
) -> nx.Graph:
    """Build the cross-view fusion candidate graph.

    With ``use_uncertainty=False`` (and ``fixed_shrink=1.0``) this reproduces the original
    geometry+feature gate bit-for-bit. When enabled (the ``proposed`` variant), the effective
    distance threshold is shrunk and the feature-similarity bar is raised in proportion to the
    pair's joint uncertainty, and a bridge veto forbids two uncertain nodes from seeding a merge.
    See docs/phase1_uncertainty_fusion_spec.md.
    """
    node_list = list(nodes)
    if not (0.0 < fixed_shrink <= 1.0):
        raise ValueError(f"fixed_shrink must be in (0, 1] to keep eff_distance <= base, got {fixed_shrink}")
    if use_uncertainty:
        if uncertainty_weight < 0 or feature_uncertainty_weight < 0:
            raise ValueError("uncertainty_weight and feature_uncertainty_weight must be >= 0 to preserve gate monotonicity")
        if not (0.0 < min_shrink <= 1.0):
            raise ValueError(f"min_shrink must be in (0, 1], got {min_shrink}")
    graph = nx.Graph()

    for node in node_list:
        graph.add_node(node.node_id, object=node)

    for index, left in enumerate(node_list):
        for right in node_list[index + 1 :]:
            left_view = left.metadata.get("view_id")
            right_view = right.metadata.get("view_id")
            if not allow_same_view_edges and left_view == right_view:
                continue

            eff_distance_threshold = distance_threshold * fixed_shrink
            eff_feature_threshold = feature_similarity_threshold
            veto = False
            if use_uncertainty:
                u_left = float(getattr(left, "uncertainty", 0.0) or 0.0)
                u_right = float(getattr(right, "uncertainty", 0.0) or 0.0)
                u_pair = max(u_left, u_right) if uncertainty_agg == "max" else 0.5 * (u_left + u_right)
                u_pair = min(max(u_pair, 0.0), 1.0)
                shrink = max(1.0 - uncertainty_weight * u_pair, min_shrink)
                eff_distance_threshold = distance_threshold * shrink
                if feature_similarity_threshold is not None:
                    gap = 1.0 - feature_similarity_threshold
                    eff_feature_threshold = min(
                        feature_similarity_threshold + feature_uncertainty_weight * u_pair * gap,
                        max(feature_similarity_threshold, max_feature_threshold),
                    )
                veto = (u_left > bridge_tau) and (u_right > bridge_tau)

            distance = centroid_distance(left, right)
            if distance <= eff_distance_threshold and not veto:
                feature_similarity = None
                if eff_feature_threshold is not None and left.feature is not None and right.feature is not None:
                    feature_similarity = cosine_similarity(left.feature, right.feature)
                    if feature_similarity < eff_feature_threshold:
                        continue
                graph.add_edge(
                    left.node_id,
                    right.node_id,
                    weight=1.0 - distance / max(distance_threshold, 1e-8),
                    distance=distance,
                    feature_similarity=feature_similarity,
                )

    return graph


def fuse_node_cluster(cluster_nodes: list[ObjectNode], node_id: str, max_points: int = 8192) -> ObjectNode:
    if not cluster_nodes:
        raise ValueError("Cannot fuse an empty node cluster.")

    points = np.concatenate([node.points_xyz for node in cluster_nodes], axis=0)
    if len(points) > max_points:
        rng = np.random.default_rng(7)
        indices = rng.choice(len(points), size=max_points, replace=False)
        points = points[np.sort(indices)]

    proposal_ids: list[str] = []
    labels: list[str] = []
    views: list[str] = []
    for node in cluster_nodes:
        proposal_ids.extend(node.proposal_ids)
        if node.label:
            labels.append(node.label)
        view_id = node.metadata.get("view_id")
        if isinstance(view_id, str):
            views.append(view_id)

    centroid = np.mean(points, axis=0).astype(np.float32)
    feature_arrays = [
        node.feature for node in cluster_nodes if node.feature is not None and node.feature.ndim == 1
    ]
    feature = None
    if feature_arrays:
        feature_dim = feature_arrays[0].shape[0]
        same_dim_features = [array for array in feature_arrays if array.shape[0] == feature_dim]
        if same_dim_features:
            feature = np.mean(np.stack(same_dim_features), axis=0).astype(np.float32)
            feature_norm = float(np.linalg.norm(feature))
            if feature_norm > 0:
                feature = feature / feature_norm

    uncertainty = float(np.mean([node.uncertainty for node in cluster_nodes]))
    if views:
        uncertainty *= 1.0 / min(len(set(views)), 3)

    mins = np.min(points, axis=0)
    maxs = np.max(points, axis=0)
    label = max(set(labels), key=labels.count) if labels else None
    return ObjectNode(
        node_id=node_id,
        proposal_ids=proposal_ids,
        points_xyz=points.astype(np.float32),
        centroid_xyz=centroid,
        feature=feature,
        label=label,
        uncertainty=float(np.clip(uncertainty, 0.0, 1.0)),
        metadata={
            "source_node_ids": [node.node_id for node in cluster_nodes],
            "view_ids": sorted(set(views)),
            "num_source_nodes": len(cluster_nodes),
            "num_views": len(set(views)),
            "bbox_3d": {
                "min_xyz": mins.round(6).tolist(),
                "max_xyz": maxs.round(6).tolist(),
                "extent_xyz": (maxs - mins).round(6).tolist(),
            },
        },
    )


FUSION_VARIANTS = (
    "2d-only",
    "geometry-only",
    "semantic-lifting",
    "graph-fusion",
    "proposed",
    "fixed-shrink",
)


def fuse_object_nodes(
    nodes: Iterable[ObjectNode],
    distance_threshold: float = 0.15,
    feature_similarity_threshold: float | None = None,
    max_points_per_fused_node: int = 8192,
    *,
    variant: str = "graph-fusion",
    use_uncertainty: bool = False,
    uncertainty_weight: float = 0.0,
    feature_uncertainty_weight: float = 0.0,
    uncertainty_agg: str = "max",
    min_shrink: float = 0.1,
    max_feature_threshold: float = 0.99,
    bridge_tau: float = 1.0,
    fixed_shrink: float = 1.0,
) -> list[ObjectNode]:
    """Fuse lifted candidate nodes into cross-view objects.

    All five paper variants route through this one entry point via ``variant``; only the gate
    parameters differ. The connected-components + ``fuse_node_cluster`` tail is identical for
    every variant. ``variant="graph-fusion"`` (default) reproduces the original pipeline.
    See docs/phase1_uncertainty_fusion_spec.md.
    """
    if variant not in FUSION_VARIANTS:
        raise ValueError(f"Unknown fusion variant: {variant!r}. Expected one of {FUSION_VARIANTS}.")

    node_list = list(nodes)

    gate = {
        "distance_threshold": distance_threshold,
        "feature_similarity_threshold": feature_similarity_threshold,
        "allow_same_view_edges": False,
    }
    if variant == "2d-only":
        gate["distance_threshold"] = float("inf")
        gate["allow_same_view_edges"] = True
    elif variant == "geometry-only":
        gate["feature_similarity_threshold"] = None
    elif variant == "proposed":
        gate.update(
            use_uncertainty=True,  # proposed is uncertainty-ON by definition (spec §5); weight=0 is the no-op
            uncertainty_weight=uncertainty_weight,
            feature_uncertainty_weight=feature_uncertainty_weight,
            uncertainty_agg=uncertainty_agg,
            min_shrink=min_shrink,
            max_feature_threshold=max_feature_threshold,
            bridge_tau=bridge_tau,
        )
    elif variant == "fixed-shrink":
        gate["fixed_shrink"] = fixed_shrink

    if variant == "semantic-lifting":
        graph = nx.Graph()
        for node in node_list:
            graph.add_node(node.node_id, object=node)
    else:
        graph = build_geometry_fusion_graph(node_list, **gate)

    node_by_id = {node.node_id: node for node in node_list}
    fused_nodes: list[ObjectNode] = []
    for index, component in enumerate(nx.connected_components(graph), start=1):
        cluster_nodes = [node_by_id[node_id] for node_id in sorted(component)]
        fused_nodes.append(
            fuse_node_cluster(cluster_nodes, node_id=f"object_{index:03d}", max_points=max_points_per_fused_node)
        )
    return fused_nodes
