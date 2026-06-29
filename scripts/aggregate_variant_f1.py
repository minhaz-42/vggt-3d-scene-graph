from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

"""Aggregate per-scene variant metrics (from evaluate_sparse_view_annotations.py) into the
variant x view-count comparison: mean object_label_f1, the proposed-vs-control deltas, and the
per-scene win counts + sign test that make the sparse-view claim defensible.

Pandas-free on purpose (numpy<2 ABI mismatch has bitten this project on Colab)."""

METRIC_DEFAULT = "object_label_f1"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Aggregate variant comparison F1 from the eval CSV.")
    p.add_argument("--metrics-csv", type=Path, required=True, help="Output of evaluate_sparse_view_annotations.py")
    p.add_argument("--metric", default=METRIC_DEFAULT, help="Metric column to aggregate.")
    p.add_argument("--markdown-output", type=Path)
    p.add_argument("--proposed", default="proposed")
    p.add_argument("--controls", nargs="+", default=["fixed-shrink", "graph-fusion"],
                   help="Variants to compute proposed-minus-control deltas + win counts against.")
    return p.parse_args()


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _sign_test_p(wins: int, losses: int) -> float:
    """Two-sided exact sign test p-value (ties excluded). Pure-Python binomial at p=0.5."""
    n = wins + losses
    if n == 0:
        return 1.0
    from math import comb
    k = min(wins, losses)
    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2.0 ** n)
    return min(1.0, 2.0 * tail)


def main() -> None:
    args = parse_args()
    rows = list(csv.DictReader(args.metrics_csv.open(encoding="utf-8")))
    if not rows:
        raise SystemExit(f"No rows in {args.metrics_csv}")

    metric = args.metric
    # value[variant][view][scene] = metric
    value: dict[str, dict[int, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    recall: dict[str, dict[int, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    precision: dict[str, dict[int, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    variants: list[str] = []
    views: set[int] = set()
    for r in rows:
        v = r["variant"]
        vc = int(r["view_count"])
        scene = r["scene_id"]
        if v not in variants:
            variants.append(v)
        views.add(vc)
        value[v][vc][scene] = float(r[metric])
        if "object_label_recall" in r:
            recall[v][vc][scene] = float(r["object_label_recall"])
        if "object_label_precision" in r:
            precision[v][vc][scene] = float(r["object_label_precision"])
    view_list = sorted(views)

    # Order variants for display: baselines, control, baseline-fusion, proposed last.
    order = ["2d-only", "geometry-only", "semantic-lifting", "fixed-shrink", "graph-fusion", "proposed"]
    variants_sorted = [v for v in order if v in variants] + [v for v in variants if v not in order]

    lines: list[str] = []
    lines.append(f"# Variant comparison on the INDEPENDENT reference — `{metric}`")
    lines.append("")
    lines.append(f"Source: `{args.metrics_csv}`  ·  mean over scenes  ·  views {view_list}")
    n_scenes = max((len(value[v][vc]) for v in variants for vc in view_list if value[v][vc]), default=0)
    lines.append(f"n_scenes = {n_scenes}")
    lines.append("")
    header = "| variant | " + " | ".join(f"v{v}" for v in view_list) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(view_list) + 1))
    for v in variants_sorted:
        cells = []
        for vc in view_list:
            scenes = value[v][vc]
            cells.append(f"{_mean(list(scenes.values())):.4f}" if scenes else "-")
        bold = "**" if v == args.proposed else ""
        lines.append(f"| {bold}{v}{bold} | " + " | ".join(cells) + " |")

    # proposed - control deltas
    prop = args.proposed
    for ctrl in args.controls:
        if prop not in value or ctrl not in value:
            continue
        lines.append("")
        lines.append(f"## `{prop}` − `{ctrl}` ({metric})")
        delta_cells = []
        win_cells = []
        for vc in view_list:
            common = sorted(set(value[prop][vc]) & set(value[ctrl][vc]))
            dmean = _mean([value[prop][vc][s] - value[ctrl][vc][s] for s in common])
            wins = sum(1 for s in common if value[prop][vc][s] > value[ctrl][vc][s] + 1e-9)
            losses = sum(1 for s in common if value[prop][vc][s] < value[ctrl][vc][s] - 1e-9)
            ties = len(common) - wins - losses
            p = _sign_test_p(wins, losses)
            delta_cells.append(f"v{vc}: {dmean:+.4f}")
            win_cells.append(f"v{vc}: {wins}W/{losses}L/{ties}T (p={p:.3f})")
        lines.append("- mean delta — " + ", ".join(delta_cells))
        lines.append("- per-scene wins — " + ", ".join(win_cells))

    # recall / precision means for the proposed + controls (helps explain the F1 movement)
    lines.append("")
    lines.append("## recall / precision (mean over scenes)")
    lines.append("| variant | metric | " + " | ".join(f"v{v}" for v in view_list) + " |")
    lines.append("|" + "---|" * (len(view_list) + 2))
    for v in variants_sorted:
        for name, table in (("recall", recall), ("precision", precision)):
            if not table[v]:
                continue
            cells = [f"{_mean(list(table[v][vc].values())):.4f}" if table[v][vc] else "-" for vc in view_list]
            lines.append(f"| {v} | {name} | " + " | ".join(cells) + " |")

    md = "\n".join(lines) + "\n"
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(md, encoding="utf-8")
        print(f"Wrote {args.markdown_output}")
    print(md)


if __name__ == "__main__":
    main()
