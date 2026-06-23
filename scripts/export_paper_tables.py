from __future__ import annotations

import argparse
import csv
from pathlib import Path


VARIANT_NAMES = {
    "scene_graph_all_views.json": "OpenCV geometry-only",
    "scene_graph_all_views_clip.json": "OpenCV feature fusion",
    "scene_graph_all_views_sam_clip.json": "SAM semantic fusion",
    "scene_graph_all_views_sam_clip_dinov2.json": "Proposed prototype",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export scene graph summary rows as paper tables.")
    parser.add_argument("--summary", type=Path, default=Path("results/benchmark_tum_rgbd/scene_graph_summary.csv"))
    parser.add_argument("--latex-output", type=Path, default=Path("paper/tables/generated_scene_graph_summary.tex"))
    parser.add_argument("--markdown-output", type=Path, default=Path("paper/tables/generated_scene_graph_summary.md"))
    return parser.parse_args()


def _variant_name(path_value: str) -> str:
    path = Path(path_value)
    return VARIANT_NAMES.get(path.name, path.stem)


def _feature_name(row: dict[str, str]) -> str:
    features = row.get("proposal_feature_backends", "")
    if not features:
        return "none"
    return features.replace(",", "+").replace("handcrafted_color", "handcrafted")


def _proposal_name(row: dict[str, str]) -> str:
    proposals = row.get("proposals_path", "")
    if "sam" in proposals:
        return "SAM"
    if "opencv" in proposals:
        return "OpenCV"
    return "unknown"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _latex_escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _table_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    return [
        [
            _variant_name(row["path"]),
            _proposal_name(row),
            _feature_name(row),
            row.get("num_candidate_nodes", ""),
            row.get("num_nodes", ""),
            row.get("multi_view_nodes", ""),
            row.get("num_relations", ""),
            row.get("mean_uncertainty", ""),
        ]
        for row in rows
    ]


def write_latex(rows: list[dict[str, str]], path: Path) -> None:
    headers = [
        "Variant",
        "Proposals",
        "Features",
        "Candidates",
        "Objects",
        "Multi-view",
        "Relations",
        "Uncertainty",
    ]
    table_rows = _table_rows(rows)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Local prototype ablation on the four-view example scene.}",
        "\\label{tab:local_ablation}",
        "\\begin{tabular}{lllrrrrr}",
        "\\toprule",
        " & ".join(headers) + " \\\\",
        "\\midrule",
    ]
    for row in table_rows:
        lines.append(" & ".join(_latex_escape(value) for value in row) + " \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(rows: list[dict[str, str]], path: Path) -> None:
    headers = [
        "Variant",
        "Proposals",
        "Features",
        "Candidates",
        "Objects",
        "Multi-view",
        "Relations",
        "Uncertainty",
    ]
    table_rows = _table_rows(rows)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in table_rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = _read_rows(args.summary)
    write_latex(rows, args.latex_output)
    write_markdown(rows, args.markdown_output)
    print(f"Wrote {args.latex_output}")
    print(f"Wrote {args.markdown_output}")


if __name__ == "__main__":
    main()
