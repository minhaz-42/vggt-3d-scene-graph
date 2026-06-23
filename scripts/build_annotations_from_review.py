from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


TRUE_VALUES = {"1", "true", "t", "yes", "y", "keep", "kept"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "drop", "dropped", "skip", "remove", "ignore"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build evaluator-ready object/relation annotations from reviewed CSV sheets."
    )
    parser.add_argument("--node-review", type=Path, required=True)
    parser.add_argument("--relation-review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scene-id", help="Scene id to store in the annotation JSON.")
    parser.add_argument("--annotation-draft", type=Path, help="Optional draft JSON to inherit scene/source metadata.")
    parser.add_argument("--source-scene-graph", type=Path, help="Optional source prediction path for provenance.")
    parser.add_argument("--name", help="Optional annotation set name.")
    parser.add_argument(
        "--require-reviewed",
        action="store_true",
        help="Fail if review_label/keep/review_count fields are blank.",
    )
    return parser.parse_args()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_draft(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _scene_id_from_draft(draft: dict[str, Any]) -> str:
    scenes = draft.get("scenes", [])
    if scenes and isinstance(scenes[0], dict):
        return _clean(scenes[0].get("scene_id"))
    return ""


def _source_from_draft(draft: dict[str, Any]) -> str:
    return _clean(draft.get("source_scene_graph"))


def _parse_keep(raw_value: Any, *, default: bool, context: str) -> bool:
    value = _clean(raw_value).lower()
    if not value:
        return default
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ValueError(f"{context}: invalid keep value {raw_value!r}")


def _parse_count(raw_value: Any, *, default: int | None, context: str) -> int:
    value = _clean(raw_value)
    if not value:
        if default is None:
            raise ValueError(f"{context}: missing count")
        return default
    try:
        count = int(value)
    except ValueError as exc:
        raise ValueError(f"{context}: invalid count {raw_value!r}") from exc
    if count < 0:
        raise ValueError(f"{context}: count must be non-negative, got {count}")
    return count


def _review_label(row: dict[str, str]) -> str:
    return _clean(row.get("review_label")) or _clean(row.get("predicted_label"))


def _build_objects(
    rows: list[dict[str, str]],
    *,
    require_reviewed: bool,
) -> tuple[list[dict[str, object]], dict[str, int]]:
    counts: Counter[str] = Counter()
    stats = {
        "node_rows": len(rows),
        "kept_node_rows": 0,
        "dropped_node_rows": 0,
        "missing_node_review_label": 0,
        "missing_node_keep": 0,
    }
    missing: list[str] = []
    for index, row in enumerate(rows, start=2):
        node_id = _clean(row.get("node_id")) or f"row_{index}"
        if not _clean(row.get("keep")):
            stats["missing_node_keep"] += 1
            if require_reviewed:
                missing.append(f"node_review.csv:{index} {node_id} missing keep")

        keep = _parse_keep(row.get("keep"), default=True, context=f"node_review.csv:{index} {node_id}")
        if not keep:
            stats["dropped_node_rows"] += 1
            continue

        if not _clean(row.get("review_label")):
            stats["missing_node_review_label"] += 1
            if require_reviewed:
                missing.append(f"node_review.csv:{index} {node_id} missing review_label")

        label = _review_label(row)
        if not label:
            missing.append(f"node_review.csv:{index} {node_id} missing label")
            continue

        counts[label] += 1
        stats["kept_node_rows"] += 1

    if require_reviewed and missing:
        raise SystemExit("Review is incomplete:\n" + "\n".join(missing[:50]))

    objects = [{"label": label, "count": count} for label, count in sorted(counts.items())]
    return objects, stats


def _relation_field(row: dict[str, str], review_key: str, source_key: str) -> str:
    return _clean(row.get(review_key)) or _clean(row.get(source_key))


def _build_relations(
    rows: list[dict[str, str]],
    *,
    require_reviewed: bool,
) -> tuple[list[dict[str, object]], dict[str, int]]:
    relations: list[dict[str, object]] = []
    stats = {
        "relation_rows": len(rows),
        "kept_relation_rows": 0,
        "dropped_relation_rows": 0,
        "missing_relation_review_count": 0,
        "missing_relation_keep": 0,
        "relation_count_total": 0,
    }
    missing: list[str] = []
    for index, row in enumerate(rows, start=2):
        context = f"relation_review.csv:{index}"
        if not _clean(row.get("keep")):
            stats["missing_relation_keep"] += 1
            if require_reviewed:
                missing.append(f"{context} missing keep")

        keep = _parse_keep(row.get("keep"), default=True, context=context)
        if not keep:
            stats["dropped_relation_rows"] += 1
            continue

        subject = _relation_field(row, "review_subject_label", "subject_label")
        relation = _relation_field(row, "review_relation", "relation")
        obj = _relation_field(row, "review_object_label", "object_label")
        if not (subject and relation and obj):
            missing.append(f"{context} missing subject/relation/object label")
            continue

        review_count = _clean(row.get("review_count"))
        if not review_count:
            stats["missing_relation_review_count"] += 1
            if require_reviewed:
                missing.append(f"{context} missing review_count")

        count = _parse_count(
            review_count or row.get("count"),
            default=0,
            context=context,
        )
        if count == 0:
            stats["dropped_relation_rows"] += 1
            continue

        relations.append(
            {
                "subject_label": subject,
                "relation": relation,
                "object_label": obj,
                "count": count,
            }
        )
        stats["kept_relation_rows"] += 1
        stats["relation_count_total"] += count

    if require_reviewed and missing:
        raise SystemExit("Review is incomplete:\n" + "\n".join(missing[:50]))

    relations.sort(key=lambda item: (str(item["subject_label"]), str(item["relation"]), str(item["object_label"])))
    return relations, stats


def main() -> None:
    args = parse_args()
    draft = _load_draft(args.annotation_draft)
    scene_id = args.scene_id or _scene_id_from_draft(draft)
    if not scene_id:
        raise SystemExit("Provide --scene-id or --annotation-draft with a scene id.")

    source_scene_graph = (
        str(args.source_scene_graph)
        if args.source_scene_graph
        else _source_from_draft(draft)
    )
    node_rows = _read_csv(args.node_review)
    relation_rows = _read_csv(args.relation_review)
    objects, object_stats = _build_objects(node_rows, require_reviewed=args.require_reviewed)
    relations, relation_stats = _build_relations(relation_rows, require_reviewed=args.require_reviewed)

    review_state = "manual_review_complete" if args.require_reviewed else "review_draft_or_partial"
    payload = {
        "name": args.name or f"{scene_id}_{review_state}",
        "version": "0.1",
        "source_scene_graph": source_scene_graph,
        "notes": (
            "Built from reviewed CSV sheets. If generated without --require-reviewed, blank review fields "
            "fall back to predicted labels and predicted relation counts."
        ),
        "scenes": [
            {
                "scene_id": scene_id,
                "objects": objects,
                "relations": relations,
            }
        ],
        "metadata": {
            "generated_by": "scripts/build_annotations_from_review.py",
            "review_state": review_state,
            "node_review": str(args.node_review),
            "relation_review": str(args.relation_review),
            **object_stats,
            **relation_stats,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote annotation JSON to {args.output}")
    print(
        "objects={objects} relations={relations} relation_instances={relation_instances}".format(
            objects=sum(item["count"] for item in objects),
            relations=len(relations),
            relation_instances=relation_stats["relation_count_total"],
        )
    )
    if not args.require_reviewed:
        print("Generated in draft mode: blank review fields fell back to prediction-derived values.")


if __name__ == "__main__":
    main()
