from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from vggt_scene_graph.metrics import labeled_relation_triplets, multiset_precision_recall_f1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate scene graph outputs against optional annotations.")
    parser.add_argument("scene_graphs", type=Path, nargs="+")
    parser.add_argument("--annotations", type=Path, help="Optional object/relation annotation JSON.")
    parser.add_argument("--output", type=Path, default=Path("results/evaluation/scene_graph_metrics.csv"))
    return parser.parse_args()


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _annotation_by_scene(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    scenes = payload.get("scenes", [])
    return {str(scene["scene_id"]): scene for scene in scenes}


def _node_label(node: dict[str, Any]) -> str | None:
    label = node.get("label")
    if isinstance(label, str) and label and label != "sam_mask":
        return label
    metadata = node.get("metadata", {})
    open_vocab_label = metadata.get("open_vocab_label") if isinstance(metadata, dict) else None
    if isinstance(open_vocab_label, str) and open_vocab_label:
        return open_vocab_label
    return None


def _quality_row(path: Path, payload: dict[str, Any]) -> dict[str, object]:
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
        "variant": pipeline.get("variant", "graph-fusion"),
        "num_nodes": len(nodes),
        "num_relations": len(relations),
        "num_candidate_nodes": pipeline.get("num_candidate_nodes"),
        "multi_view_nodes": len(multi_view_nodes),
        "multi_view_ratio": round(len(multi_view_nodes) / len(nodes), 6) if nodes else 0.0,
        "mean_uncertainty": round(_mean(uncertainties), 6),
        "relation_density": round(len(relations) / max(len(nodes) * max(len(nodes) - 1, 1), 1), 6),
        "proposal_feature_backends": ",".join(pipeline.get("proposal_feature_backends", [])),
    }


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


def summarize(path: Path, annotations: dict[str, dict[str, Any]]) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    row = _quality_row(path, payload)
    scene_annotation = annotations.get(str(payload.get("scene_id")))
    if not scene_annotation:
        return row

    nodes = payload.get("nodes", [])
    predicted_labels = [label for node in nodes if (label := _node_label(node))]
    node_labels = {
        str(node.get("node_id")): label
        for node in nodes
        if (label := _node_label(node))
    }
    object_scores = multiset_precision_recall_f1(_annotation_labels(scene_annotation), predicted_labels)
    relation_scores = multiset_precision_recall_f1(
        _annotation_relation_triplets(scene_annotation),
        labeled_relation_triplets(payload.get("relations", []), node_labels),
    )
    row.update(
        {
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
    annotations = _annotation_by_scene(args.annotations)
    rows = [summarize(path, annotations) for path in args.scene_graphs]
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote evaluation rows to {args.output}")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
