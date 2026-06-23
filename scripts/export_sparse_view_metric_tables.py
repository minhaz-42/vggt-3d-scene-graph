from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export sparse-view annotation metrics to paper tables.")
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--latex-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--aggregate-latex-output", type=Path, required=True)
    parser.add_argument("--aggregate-markdown-output", type=Path, required=True)
    parser.add_argument(
        "--caption",
        default="TUM RGB-D paper-subset pseudo-reference consistency results.",
    )
    parser.add_argument(
        "--aggregate-caption",
        default="Average pseudo-reference consistency over the five-scene TUM RGB-D paper subset.",
    )
    parser.add_argument("--label", default="tab:tum_rgbd_paper_subset_pseudo_reference_results")
    parser.add_argument("--aggregate-label", default="tab:tum_rgbd_paper_subset_pseudo_reference_by_view")
    return parser.parse_args()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _view_count(row: dict[str, str]) -> int:
    value = row.get("view_count")
    if value:
        return int(float(value))
    match = re.search(r"views_(\d+)", row.get("path", ""))
    return int(match.group(1)) if match else 0


def _short_scene(scene_id: str) -> str:
    return scene_id.removeprefix("tum_rgbd_")


def _float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value else 0.0


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def _latex_escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _table_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    sorted_rows = sorted(rows, key=lambda row: (_short_scene(row.get("scene_id", "")), _view_count(row)))
    output_rows = []
    for row in sorted_rows:
        output_rows.append(
            [
                _short_scene(row.get("scene_id", "")),
                str(_view_count(row)),
                _fmt(_float(row, "object_label_precision")),
                _fmt(_float(row, "object_label_recall")),
                _fmt(_float(row, "object_label_f1")),
                _fmt(_float(row, "relation_triplet_precision")),
                _fmt(_float(row, "relation_triplet_recall")),
                _fmt(_float(row, "relation_triplet_f1")),
            ]
        )
    return output_rows


def _aggregate_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    groups: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[_view_count(row)].append(row)

    output_rows = []
    for view_count in sorted(groups):
        group = groups[view_count]
        count = len(group)
        output_rows.append(
            [
                str(view_count),
                str(count),
                _fmt(sum(_float(row, "object_label_precision") for row in group) / count),
                _fmt(sum(_float(row, "object_label_recall") for row in group) / count),
                _fmt(sum(_float(row, "object_label_f1") for row in group) / count),
                _fmt(sum(_float(row, "relation_triplet_precision") for row in group) / count),
                _fmt(sum(_float(row, "relation_triplet_recall") for row in group) / count),
                _fmt(sum(_float(row, "relation_triplet_f1") for row in group) / count),
            ]
        )
    return output_rows


def _write_latex(
    rows: list[list[str]],
    path: Path,
    *,
    headers: list[str],
    caption: str,
    label: str,
    column_spec: str,
) -> None:
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        f"\\caption{{{_latex_escape(caption)}}}",
        f"\\label{{{label}}}",
        "\\small",
        "\\resizebox{\\linewidth}{!}{%",
        f"\\begin{{tabular}}{{{column_spec}}}",
        "\\toprule",
        " & ".join(_latex_escape(header) for header in headers) + " \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(_latex_escape(value) for value in row) + " \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}", "}", "\\end{table}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_markdown(rows: list[list[str]], path: Path, *, headers: list[str]) -> None:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = _read_rows(args.metrics)
    full_headers = ["Scene", "Views", "Obj P", "Obj R", "Obj F1", "Rel P", "Rel R", "Rel F1"]
    full_rows = _table_rows(rows)
    _write_latex(
        full_rows,
        args.latex_output,
        headers=full_headers,
        caption=args.caption,
        label=args.label,
        column_spec="lrrrrrrr",
    )
    _write_markdown(full_rows, args.markdown_output, headers=full_headers)

    aggregate_headers = ["Views", "Scenes", "Obj P", "Obj R", "Obj F1", "Rel P", "Rel R", "Rel F1"]
    aggregate_rows = _aggregate_rows(rows)
    _write_latex(
        aggregate_rows,
        args.aggregate_latex_output,
        headers=aggregate_headers,
        caption=args.aggregate_caption,
        label=args.aggregate_label,
        column_spec="rrrrrrrr",
    )
    _write_markdown(aggregate_rows, args.aggregate_markdown_output, headers=aggregate_headers)

    print(f"Wrote {args.latex_output}")
    print(f"Wrote {args.markdown_output}")
    print(f"Wrote {args.aggregate_latex_output}")
    print(f"Wrote {args.aggregate_markdown_output}")


if __name__ == "__main__":
    main()
