from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from vggt_scene_graph.metrics import labeled_relation_triplets, multiset_precision_recall_f1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate sparse-view scene graphs with per-scene annotation packets."
    )
    parser.add_argument("--dataset", type=Path, required=True, help="Dataset manifest JSON.")
    parser.add_argument("--results-root", type=Path, required=True, help="Benchmark output root.")
    parser.add_argument("--annotations-root", type=Path, required=True, help="Annotation packet root.")
    parser.add_argument("--output", type=Path, required=True, help="Combined metrics CSV.")
    parser.add_argument("--view-counts", type=int, nargs="*", help="View counts to evaluate.")
    parser.add_argument(
        "--reference-view-count",
        type=int,
        default=10,
        help="View count used to name the annotation packet.",
    )
    parser.add_argument(
        "--packet-mode",
        choices=["pseudo_reference", "manual_review"],
        default="pseudo_reference",
        help="Annotation packet naming mode.",
    )
    parser.add_argument(
        "--annotation-file-name",
        default="annotation_draft.json",
        help="Annotation JSON inside each packet, e.g. annotation_draft.json or annotation_checked.json.",
    )
    parser.add_argument("--scene-id", action="append", default=[], help="Optional scene id filter.")
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _packet_name(scene_id: str, mode: str, view_count: int) -> str:
    suffix = "pseudo_from" if mode == "pseudo_reference" else "manual_from"
    return f"{scene_id}_{suffix}_{view_count:02d}view"


def _node_label(node: dict[str, Any]) -> str | None:
    label = node.get("label")
    if isinstance(label, str) and label and label != "sam_mask":
        return label
    metadata = node.get("metadata", {})
    open_vocab_label = metadata.get("open_vocab_label") if isinstance(metadata, dict) else None
    if isinstance(open_vocab_label, str) and open_vocab_label:
        return open_vocab_label
    return None


def _quality_row(path: Path, payload: dict[str, Any], view_count: int) -> dict[str, object]:
    nodes = payload.get("nodes", [])
    relations = payload.get("relations", [])
    pipeline = payload.get("pipeline", {})
    uncertainties = [float(node.get("uncertainty", 0.0)) for node in nodes]
    multi_view_nodes = [
        node for node in nodes if int(node.get("metadata", {}).get("num_views", 0)) >= 2
    ]
    return {
        "path": str(path),
        "scene_id": payload.get("scene_id"),
        "view_count": view_count,
        "num_nodes": len(nodes),
        "num_relations": len(relations),
        "num_candidate_nodes": pipeline.get("num_candidate_nodes"),
        "multi_view_nodes": len(multi_view_nodes),
        "multi_view_ratio": round(len(multi_view_nodes) / len(nodes), 6) if nodes else 0.0,
        "mean_uncertainty": round(_mean(uncertainties), 6),
        "relation_density": round(len(relations) / max(len(nodes) * max(len(nodes) - 1, 1), 1), 6),
        "proposal_feature_backends": ",".join(pipeline.get("proposal_feature_backends", [])),
    }


def _annotation_by_scene(annotation_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    scenes = annotation_payload.get("scenes", [])
    return {str(scene["scene_id"]): scene for scene in scenes}


def _annotation_labels(scene_annotation: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for item in scene_annotation.get("objects", []):
        label = item.get("label")
        if not label:
            continue
        count = int(item.get("count", 1))
        labels.extend([str(label)] * max(count, 0))
    return labels


def _annotation_relation_triplets(scene_annotation: dict[str, Any]) -> list[str]:
    triplets: list[str] = []
    for edge in scene_annotation.get("relations", []):
        subject = edge.get("subject_label")
        relation = edge.get("relation")
        obj = edge.get("object_label")
        if subject and relation and obj:
            count = int(edge.get("count", 1))
            triplets.extend([f"{subject}:{relation}:{obj}"] * max(count, 0))
    return triplets


def _evaluate_graph(
    graph_path: Path,
    annotation_path: Path,
    *,
    view_count: int,
    reference_view_count: int,
) -> dict[str, object]:
    graph_payload = _load_json(graph_path)
    annotation_payload = _load_json(annotation_path)
    annotations = _annotation_by_scene(annotation_payload)
    row = _quality_row(graph_path, graph_payload, view_count)
    scene_id = str(graph_payload.get("scene_id"))
    scene_annotation = annotations.get(scene_id)
    if not scene_annotation:
        raise ValueError(f"{annotation_path} does not contain annotation for scene {scene_id}")

    nodes = graph_payload.get("nodes", [])
    predicted_labels = [label for node in nodes if (label := _node_label(node))]
    node_labels = {
        str(node.get("node_id")): label
        for node in nodes
        if (label := _node_label(node))
    }
    object_scores = multiset_precision_recall_f1(_annotation_labels(scene_annotation), predicted_labels)
    relation_scores = multiset_precision_recall_f1(
        _annotation_relation_triplets(scene_annotation),
        labeled_relation_triplets(graph_payload.get("relations", []), node_labels),
    )
    metadata = annotation_payload.get("metadata", {})
    row.update(
        {
            "reference_view_count": reference_view_count,
            "is_reference_view": view_count == reference_view_count,
            "annotation_path": str(annotation_path),
            "annotation_name": annotation_payload.get("name", ""),
            "annotation_review_state": metadata.get("review_state", "annotation_draft"),
            "object_label_precision": round(object_scores["precision"], 6),
            "object_label_recall": round(object_scores["recall"], 6),
            "object_label_f1": round(object_scores["f1"], 6),
            "relation_triplet_precision": round(relation_scores["precision"], 6),
            "relation_triplet_recall": round(relation_scores["recall"], 6),
            "relation_triplet_f1": round(relation_scores["f1"], 6),
        }
    )
    return row


def main() -> None:
    args = parse_args()
    manifest = _load_json(args.dataset)
    selected_scene_ids = set(args.scene_id)
    view_counts = args.view_counts or [int(value) for value in manifest.get("sparse_view_counts", [])]
    if not view_counts:
        raise SystemExit("Provide --view-counts or use a dataset manifest with sparse_view_counts.")

    rows: list[dict[str, object]] = []
    for scene in manifest.get("scenes", []):
        scene_id = str(scene.get("scene_id", ""))
        if selected_scene_ids and scene_id not in selected_scene_ids:
            continue
        annotation_path = (
            args.annotations_root
            / _packet_name(scene_id, args.packet_mode, args.reference_view_count)
            / args.annotation_file_name
        )
        if not annotation_path.exists():
            raise FileNotFoundError(f"Missing annotation file: {annotation_path}")
        for view_count in view_counts:
            graph_path = args.results_root / scene_id / f"views_{view_count:02d}" / "scene_graph_labeled.json"
            if not graph_path.exists():
                raise FileNotFoundError(f"Missing scene graph: {graph_path}")
            rows.append(
                _evaluate_graph(
                    graph_path,
                    annotation_path,
                    view_count=view_count,
                    reference_view_count=args.reference_view_count,
                )
            )

    if selected_scene_ids:
        missing = sorted(selected_scene_ids - {str(row["scene_id"]) for row in rows})
        if missing:
            raise ValueError(f"Scene ids not found in manifest: {missing}")

    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} evaluation rows to {args.output}")


if __name__ == "__main__":
    main()
