from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create manual/pseudo annotation files from a labeled scene graph.")
    parser.add_argument("--scene-graph", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=["pseudo_reference", "manual_review"],
        default="pseudo_reference",
        help="Whether the draft should be treated as a prediction-derived pseudo reference or a manual review packet.",
    )
    return parser.parse_args()


def _node_label(node: dict[str, Any]) -> str:
    label = node.get("label")
    if isinstance(label, str) and label:
        return label
    metadata = node.get("metadata", {})
    if isinstance(metadata, dict):
        open_vocab_label = metadata.get("open_vocab_label")
        if isinstance(open_vocab_label, str) and open_vocab_label:
            return open_vocab_label
    return "unknown object"


def _top_scores(node: dict[str, Any], top_k: int = 5) -> str:
    scores = node.get("metadata", {}).get("open_vocab_scores", [])
    if not isinstance(scores, list):
        return ""
    parts = []
    for item in scores[:top_k]:
        if isinstance(item, dict):
            parts.append(f"{item.get('label')}:{float(item.get('score', 0.0)):.4f}")
    return "; ".join(parts)


def _node_rows(nodes: list[dict[str, Any]]) -> list[dict[str, object]]:
    rows = []
    for node in nodes:
        metadata = node.get("metadata", {})
        bbox_3d = metadata.get("bbox_3d", {}) if isinstance(metadata, dict) else {}
        rows.append(
            {
                "node_id": node.get("node_id"),
                "predicted_label": _node_label(node),
                "review_label": "",
                "keep": "",
                "uncertainty": node.get("uncertainty"),
                "num_points": node.get("num_points"),
                "num_views": metadata.get("num_views") if isinstance(metadata, dict) else "",
                "view_ids": ",".join(metadata.get("view_ids", [])) if isinstance(metadata, dict) else "",
                "num_source_nodes": metadata.get("num_source_nodes") if isinstance(metadata, dict) else "",
                "centroid_xyz": node.get("centroid_xyz"),
                "bbox_min_xyz": bbox_3d.get("min_xyz"),
                "bbox_max_xyz": bbox_3d.get("max_xyz"),
                "bbox_extent_xyz": bbox_3d.get("extent_xyz"),
                "top_open_vocab_scores": _top_scores(node),
                "proposal_ids": ",".join(str(value) for value in node.get("proposal_ids", [])),
            }
        )
    return rows


def _relation_rows(
    relations: list[dict[str, Any]],
    node_labels: dict[str, str],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for edge in relations:
        subject_id = str(edge.get("subject_id", ""))
        object_id = str(edge.get("object_id", ""))
        subject_label = node_labels.get(subject_id)
        object_label = node_labels.get(object_id)
        relation = edge.get("relation")
        if not subject_label or not object_label or not relation:
            continue
        grouped[(subject_label, str(relation), object_label)].append(float(edge.get("confidence", 0.0)))

    rows = []
    for (subject_label, relation, object_label), confidences in sorted(grouped.items()):
        rows.append(
            {
                "subject_label": subject_label,
                "relation": relation,
                "object_label": object_label,
                "review_subject_label": "",
                "review_relation": "",
                "review_object_label": "",
                "count": len(confidences),
                "review_count": "",
                "keep": "",
                "mean_confidence": round(sum(confidences) / len(confidences), 6),
            }
        )
    return rows


def _annotation_draft(
    payload: dict[str, Any],
    node_rows: list[dict[str, object]],
    relation_rows: list[dict[str, object]],
    mode: str,
) -> dict[str, Any]:
    label_counts = Counter(str(row["predicted_label"]) for row in node_rows)
    return {
        "name": f"{payload.get('scene_id')}_{mode}_annotations",
        "version": "0.1",
        "source_scene_graph": payload.get("source_path"),
        "notes": (
            "Prediction-derived pseudo reference. Edit object counts and relation counts after manual "
            "review before treating this as ground truth."
            if mode == "pseudo_reference"
            else "Manual review draft. Fill review_label/keep in node_review.csv and review_count in relation_review.csv."
        ),
        "scenes": [
            {
                "scene_id": payload.get("scene_id"),
                "objects": [
                    {"label": label, "count": count}
                    for label, count in sorted(label_counts.items())
                ],
                "relations": [
                    {
                        "subject_label": row["subject_label"],
                        "relation": row["relation"],
                        "object_label": row["object_label"],
                        "count": row["count"],
                    }
                    for row in relation_rows
                ],
            }
        ],
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    payload = json.loads(args.scene_graph.read_text(encoding="utf-8"))
    payload["source_path"] = str(args.scene_graph)
    nodes = payload.get("nodes", [])
    relations = payload.get("relations", [])
    node_rows = _node_rows(nodes)
    node_labels = {str(node.get("node_id")): _node_label(node) for node in nodes}
    relation_rows = _relation_rows(relations, node_labels)
    annotation_payload = _annotation_draft(payload, node_rows, relation_rows, args.mode)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    node_csv = args.output_dir / "node_review.csv"
    relation_csv = args.output_dir / "relation_review.csv"
    annotation_json = args.output_dir / "annotation_draft.json"
    readme = args.output_dir / "README.md"
    _write_csv(node_csv, node_rows)
    _write_csv(relation_csv, relation_rows)
    annotation_json.write_text(json.dumps(annotation_payload, indent=2), encoding="utf-8")
    readme.write_text(
        "\n".join(
            [
                "# Annotation Packet",
                "",
                f"Source graph: `{args.scene_graph}`",
                "",
                "- `node_review.csv`: per-node label review sheet.",
                "- `relation_review.csv`: aggregated labeled relation triplets with editable review columns.",
                "- `annotation_draft.json`: prediction-derived annotation draft for evaluator input.",
                "- `annotation_review.html`: optional visual review sheet generated by "
                "`scripts/render_annotation_review.py`.",
                "",
                "For real ground truth, edit the review CSVs after manual inspection, then run "
                "`scripts/build_annotations_from_review.py`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {node_csv}")
    print(f"Wrote {relation_csv}")
    print(f"Wrote {annotation_json}")


if __name__ == "__main__":
    main()
