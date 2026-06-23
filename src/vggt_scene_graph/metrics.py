from __future__ import annotations

from collections.abc import Iterable
from collections import Counter


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def precision_recall_f1(true_items: Iterable[str], predicted_items: Iterable[str]) -> dict[str, float]:
    true_set = set(true_items)
    predicted_set = set(predicted_items)

    true_positive = len(true_set & predicted_set)
    precision = _safe_divide(true_positive, len(predicted_set))
    recall = _safe_divide(true_positive, len(true_set))
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def multiset_precision_recall_f1(true_items: Iterable[str], predicted_items: Iterable[str]) -> dict[str, float]:
    true_counts = Counter(true_items)
    predicted_counts = Counter(predicted_items)
    true_positive = sum(min(count, predicted_counts[item]) for item, count in true_counts.items())
    predicted_total = sum(predicted_counts.values())
    true_total = sum(true_counts.values())
    precision = _safe_divide(true_positive, predicted_total)
    recall = _safe_divide(true_positive, true_total)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positive": float(true_positive),
        "predicted_total": float(predicted_total),
        "true_total": float(true_total),
    }


def relation_triplet(edge: object) -> str:
    return f"{edge.subject_id}:{edge.relation}:{edge.object_id}"


def labeled_relation_triplets(
    relations: Iterable[dict[str, object]],
    node_labels: dict[str, str],
) -> list[str]:
    triplets = []
    for edge in relations:
        subject_id = str(edge.get("subject_id", ""))
        object_id = str(edge.get("object_id", ""))
        subject_label = node_labels.get(subject_id)
        object_label = node_labels.get(object_id)
        relation = edge.get("relation")
        if subject_label and object_label and relation:
            triplets.append(f"{subject_label}:{relation}:{object_label}")
    return triplets
