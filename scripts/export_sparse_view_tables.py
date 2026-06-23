from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export sparse-view benchmark CSVs to paper tables.")
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--latex-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--aggregate-latex-output", type=Path, required=True)
    parser.add_argument("--aggregate-markdown-output", type=Path, required=True)
    parser.add_argument("--caption", default="TUM RGB-D paper-subset sparse-view scene graph results.")
    parser.add_argument("--label", default="tab:tum_rgbd_paper_subset_results")
    parser.add_argument("--aggregate-label", default="tab:tum_rgbd_paper_subset_by_view")
    return parser.parse_args()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _view_count(path_value: str) -> int:
    match = re.search(r"views_(\d+)", path_value)
    if not match:
        return 0
    return int(match.group(1))


def _short_scene(scene_id: str) -> str:
    return scene_id.removeprefix("tum_rgbd_")


def _float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value else 0.0


def _int(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    return int(float(value)) if value else 0


def _fmt_mean(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def _fmt_uncertainty(value: float) -> str:
    return f"{value:.6f}"


def _latex_escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _table_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    sorted_rows = sorted(rows, key=lambda row: (_short_scene(row.get("scene_id", "")), _view_count(row.get("path", ""))))
    table_rows = []
    for row in sorted_rows:
        table_rows.append(
            [
                _short_scene(row.get("scene_id", "")),
                str(_view_count(row.get("path", ""))),
                str(_int(row, "num_candidate_nodes")),
                str(_int(row, "num_nodes")),
                str(_int(row, "multi_view_nodes")),
                str(_int(row, "num_relations")),
                _fmt_uncertainty(_float(row, "mean_uncertainty")),
            ]
        )
    return table_rows


def _aggregate_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    groups: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[_view_count(row.get("path", ""))].append(row)

    output_rows = []
    for view_count in sorted(groups):
        group = groups[view_count]
        count = len(group)
        output_rows.append(
            [
                str(view_count),
                str(count),
                _fmt_mean(sum(_int(row, "num_candidate_nodes") for row in group) / count),
                _fmt_mean(sum(_int(row, "num_nodes") for row in group) / count),
                _fmt_mean(sum(_int(row, "multi_view_nodes") for row in group) / count),
                _fmt_mean(sum(_int(row, "num_relations") for row in group) / count),
                _fmt_uncertainty(sum(_float(row, "mean_uncertainty") for row in group) / count),
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
    rows = _read_rows(args.summary)

    full_headers = ["Scene", "Views", "Candidates", "Objects", "Multi-view", "Relations", "Uncertainty"]
    full_rows = _table_rows(rows)
    _write_latex(
        full_rows,
        args.latex_output,
        headers=full_headers,
        caption=args.caption,
        label=args.label,
        column_spec="lrrrrrr",
    )
    _write_markdown(full_rows, args.markdown_output, headers=full_headers)

    aggregate_headers = ["Views", "Scenes", "Candidates", "Objects", "Multi-view", "Relations", "Uncertainty"]
    aggregate_rows = _aggregate_rows(rows)
    _write_latex(
        aggregate_rows,
        args.aggregate_latex_output,
        headers=aggregate_headers,
        caption="Average sparse-view scene graph statistics over the five-scene TUM RGB-D paper subset.",
        label=args.aggregate_label,
        column_spec="rrrrrrr",
    )
    _write_markdown(aggregate_rows, args.aggregate_markdown_output, headers=aggregate_headers)

    print(f"Wrote {args.latex_output}")
    print(f"Wrote {args.markdown_output}")
    print(f"Wrote {args.aggregate_latex_output}")
    print(f"Wrote {args.aggregate_markdown_output}")


if __name__ == "__main__":
    main()
