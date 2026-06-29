from __future__ import annotations

import argparse
import json
from pathlib import Path

from vggt_scene_graph.datasets import SceneRecord, get_scene, load_dataset_manifest
from vggt_scene_graph.graph_builder import fuse_object_nodes
from vggt_scene_graph.lifting import lift_scene_proposals
from vggt_scene_graph.relations import infer_relations
from vggt_scene_graph.scene_graph_io import scene_graph_to_dict
from vggt_scene_graph.types import SceneGraph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sparse-view 3D scene graph generation.")
    parser.add_argument("--dataset", type=Path, help="Dataset manifest JSON.")
    parser.add_argument("--scene-id", help="Scene id inside the dataset manifest. Defaults to the first scene.")
    parser.add_argument("--scene-dir", type=Path, help="Directory containing scene images for direct-path mode.")
    parser.add_argument("--geometry", type=Path, help="VGGT geometry .npz for direct-path mode.")
    parser.add_argument("--proposals", type=Path, help="2D proposal JSON for direct-path mode.")
    parser.add_argument("--output", type=Path, default=Path("results/scene_graph.json"))
    parser.add_argument("--min-point-confidence", type=float, default=0.2)
    parser.add_argument("--max-points-per-node", type=int, default=4096)
    parser.add_argument("--fusion-distance", type=float, default=0.15)
    parser.add_argument(
        "--fusion-feature-threshold",
        type=float,
        default=0.75,
        help="Require this cosine similarity for cross-view fusion when proposal features are available.",
    )
    parser.add_argument("--max-points-per-fused-node", type=int, default=8192)
    parser.add_argument("--relation-near-threshold", type=float, default=0.35)
    parser.add_argument("--relation-max-distance", type=float, default=0.75)
    parser.add_argument("--include-point-sample", type=int, default=0)
    parser.add_argument(
        "--variant",
        default="graph-fusion",
        choices=["2d-only", "geometry-only", "semantic-lifting", "graph-fusion", "graph-fusion-dedup", "proposed", "fixed-shrink"],
        help="Fusion variant for baselines/ablations. Default reproduces the original pipeline; "
        "'graph-fusion-dedup' adds a post-fusion duplicate-instance merge.",
    )
    parser.add_argument(
        "--dedup-iou",
        type=float,
        default=0.1,
        help="3D-box IoU above which same-label fused nodes are merged (variant=graph-fusion-dedup).",
    )
    parser.add_argument(
        "--use-uncertainty",
        action="store_true",
        help="Enable uncertainty-aware fusion (only consulted when --variant proposed).",
    )
    parser.add_argument("--uncertainty-weight", type=float, default=0.5)
    parser.add_argument("--feature-uncertainty-weight", type=float, default=1.0)
    parser.add_argument("--uncertainty-agg", choices=["max", "mean"], default="max")
    parser.add_argument(
        "--uncertainty-normalize",
        choices=["none", "rank", "minmax"],
        default="none",
        help="Per-scene normalization of node uncertainty before modulation. 'rank'/'minmax' "
        "give the low-range raw signal real dynamic range; 'none' uses the raw value.",
    )
    parser.add_argument("--uncertainty-min-shrink", type=float, default=0.1)
    parser.add_argument("--uncertainty-max-feature-threshold", type=float, default=0.99)
    parser.add_argument("--bridge-tau", type=float, default=0.6)
    parser.add_argument("--fixed-shrink", type=float, default=1.0)
    return parser.parse_args()


def _scene_from_args(args: argparse.Namespace) -> tuple[SceneRecord, dict[str, object]]:
    if args.dataset:
        manifest = load_dataset_manifest(args.dataset)
        scene = get_scene(manifest, args.scene_id) if args.scene_id else manifest.scenes[0]
        return scene, {
            "dataset_name": manifest.name,
            "dataset_version": manifest.version,
            "dataset_path": str(args.dataset),
            "split": scene.split,
        }

    if not args.scene_dir or not args.geometry or not args.proposals:
        raise SystemExit("Direct-path mode requires --scene-dir, --geometry, and --proposals.")

    scene = SceneRecord(
        scene_id=args.scene_id or args.scene_dir.name,
        scene_dir=args.scene_dir,
        image_paths=[],
        geometry_path=args.geometry,
        proposals_path=args.proposals,
    )
    return scene, {"dataset_name": "direct_paths", "dataset_version": "manual"}


def _proposal_feature_backends(proposals_path: Path) -> list[str]:
    payload = json.loads(proposals_path.read_text(encoding="utf-8"))
    feature_backends = payload.get("feature_backends")
    if isinstance(feature_backends, list):
        return sorted(str(backend) for backend in feature_backends)

    return sorted(
        {
            str(backend)
            for record in payload.get("proposals", [])
            if isinstance(record.get("features"), dict)
            for backend in record["features"]
        }
    )


def main() -> None:
    args = parse_args()
    scene, dataset_metadata = _scene_from_args(args)
    if scene.geometry_path is None:
        raise SystemExit(f"Scene {scene.scene_id} has no geometry_path.")
    if scene.proposals_path is None:
        raise SystemExit(f"Scene {scene.scene_id} has no proposals_path.")

    candidate_nodes = lift_scene_proposals(
        scene.geometry_path,
        scene.proposals_path,
        min_confidence=args.min_point_confidence,
        max_points_per_node=args.max_points_per_node,
    )
    fused_nodes = fuse_object_nodes(
        candidate_nodes,
        distance_threshold=args.fusion_distance,
        feature_similarity_threshold=args.fusion_feature_threshold,
        max_points_per_fused_node=args.max_points_per_fused_node,
        variant=args.variant,
        use_uncertainty=args.use_uncertainty,
        uncertainty_weight=args.uncertainty_weight,
        feature_uncertainty_weight=args.feature_uncertainty_weight,
        uncertainty_agg=args.uncertainty_agg,
        uncertainty_normalize=args.uncertainty_normalize,
        min_shrink=args.uncertainty_min_shrink,
        max_feature_threshold=args.uncertainty_max_feature_threshold,
        bridge_tau=args.bridge_tau,
        fixed_shrink=args.fixed_shrink,
        dedup_iou=args.dedup_iou,
    )
    relations = infer_relations(
        fused_nodes,
        near_threshold=args.relation_near_threshold,
        max_distance=args.relation_max_distance,
    )

    scene_graph = SceneGraph(scene_id=scene.scene_id, nodes=fused_nodes, relations=relations)
    payload = scene_graph_to_dict(scene_graph, include_point_sample=args.include_point_sample)
    payload["pipeline"] = {
        "status": "prototype_complete",
        "scene_dir": str(scene.scene_dir),
        "geometry_path": str(scene.geometry_path),
        "proposals_path": str(scene.proposals_path),
        "proposal_feature_backends": _proposal_feature_backends(scene.proposals_path),
        "num_candidate_nodes": len(candidate_nodes),
        "num_fused_nodes": len(fused_nodes),
        "num_relations": len(relations),
        "variant": args.variant,
        "use_uncertainty": args.use_uncertainty or args.variant == "proposed",
        "uncertainty_weight": args.uncertainty_weight,
        "feature_uncertainty_weight": args.feature_uncertainty_weight,
        "uncertainty_agg": args.uncertainty_agg,
        "uncertainty_normalize": args.uncertainty_normalize,
        "uncertainty_min_shrink": args.uncertainty_min_shrink,
        "uncertainty_max_feature_threshold": args.uncertainty_max_feature_threshold,
        "bridge_tau": args.bridge_tau,
        "fixed_shrink": args.fixed_shrink,
        "dedup_iou": args.dedup_iou,
        "min_point_confidence": args.min_point_confidence,
        "fusion_distance": args.fusion_distance,
        "fusion_feature_threshold": args.fusion_feature_threshold,
        "relation_near_threshold": args.relation_near_threshold,
        "relation_max_distance": args.relation_max_distance,
        **dataset_metadata,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote scene graph to {args.output}")
    print(f"candidate_nodes={len(candidate_nodes)} fused_nodes={len(fused_nodes)} relations={len(relations)}")


if __name__ == "__main__":
    main()
