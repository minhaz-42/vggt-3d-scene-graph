from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create assistant-prefilled annotation review CSVs from the current "
            "pseudo labels. Existing reviewer entries are preserved."
        )
    )
    parser.add_argument(
        "--packet-index",
        type=Path,
        required=True,
        help="annotation_packet_index.json generated with the annotation packets.",
    )
    parser.add_argument(
        "--suffix",
        default="assistant_prefill",
        help="Suffix for copy outputs, e.g. node_review_assistant_prefill.csv.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Fill the original node_review.csv and relation_review.csv files.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing prefill copy files.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create .before_assistant_prefill.csv backups when using --in-place.",
    )
    return parser.parse_args()


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _copy_target(path: Path, suffix: str) -> Path:
    return path.with_name(f"{path.stem}_{suffix}{path.suffix}")


def _backup_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}.before_assistant_prefill{path.suffix}")


def _fill_if_blank(row: dict[str, str], key: str, value: str) -> int:
    if _clean(row.get(key)):
        return 0
    row[key] = value
    return 1


def _prefill_nodes(rows: list[dict[str, str]]) -> dict[str, int]:
    filled = {"review_label": 0, "keep": 0}
    for row in rows:
        predicted_label = _clean(row.get("predicted_label"))
        filled["review_label"] += _fill_if_blank(row, "review_label", predicted_label)
        filled["keep"] += _fill_if_blank(row, "keep", "keep")
    return filled


def _prefill_relations(rows: list[dict[str, str]]) -> dict[str, int]:
    filled = {
        "review_subject_label": 0,
        "review_relation": 0,
        "review_object_label": 0,
        "review_count": 0,
        "keep": 0,
    }
    for row in rows:
        filled["review_subject_label"] += _fill_if_blank(
            row, "review_subject_label", _clean(row.get("subject_label"))
        )
        filled["review_relation"] += _fill_if_blank(row, "review_relation", _clean(row.get("relation")))
        filled["review_object_label"] += _fill_if_blank(
            row, "review_object_label", _clean(row.get("object_label"))
        )
        filled["review_count"] += _fill_if_blank(row, "review_count", _clean(row.get("count")))
        filled["keep"] += _fill_if_blank(row, "keep", "keep")
    return filled


def _write_result(
    source_path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    *,
    args: argparse.Namespace,
) -> Path:
    target = source_path if args.in_place else _copy_target(source_path, args.suffix)
    if target.exists() and target != source_path and not args.overwrite:
        raise SystemExit(f"{target} already exists; pass --overwrite to replace it.")
    if args.in_place and not args.no_backup:
        backup = _backup_path(source_path)
        if not backup.exists():
            backup.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    _write_csv(target, fieldnames, rows)
    return target


def main() -> None:
    args = parse_args()
    index = json.loads(args.packet_index.read_text(encoding="utf-8"))
    total_summary: dict[str, int] = {}

    for packet in index.get("packets", []):
        node_path = Path(packet["node_review_csv"])
        relation_path = Path(packet["relation_review_csv"])

        node_fields, node_rows = _read_csv(node_path)
        relation_fields, relation_rows = _read_csv(relation_path)

        node_filled = _prefill_nodes(node_rows)
        relation_filled = _prefill_relations(relation_rows)

        node_target = _write_result(node_path, node_fields, node_rows, args=args)
        relation_target = _write_result(relation_path, relation_fields, relation_rows, args=args)

        for key, value in {**node_filled, **relation_filled}.items():
            total_summary[key] = total_summary.get(key, 0) + value

        print(f"{packet['scene_id']}: wrote {node_target} and {relation_target}")

    print("filled=" + json.dumps(total_summary, sort_keys=True))
    print(
        "Note: these are assistant-prefilled pseudo-label reviews. Verify uncertain rows "
        "before treating them as human-checked annotations."
    )


if __name__ == "__main__":
    main()
