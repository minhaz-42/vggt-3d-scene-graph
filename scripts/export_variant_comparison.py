from __future__ import annotations

import argparse
import csv
import json
import statistics
from glob import glob
from pathlib import Path

"""Aggregate structural scene-graph statistics across fusion variants for the baseline
comparison table (Phase 1, docs/phase1_uncertainty_fusion_spec.md).

The default ("graph-fusion") variant lives at <results-root>/<scene>/views_NN/; other
variants live under <results-root>/variants/<variant>/<scene>/views_NN/. Reads the
(unlabeled) scene_graph.json so it works without the CLIP labelling stage.
"""

METRICS = [
    ("fused_objects", "Fused objects", "higher = more split / less merge", True),
    ("multi_view_objects", "Multi-view objects", "objects seen in >=2 views", True),
    ("mean_source_nodes", "Mean source nodes/obj", "avg candidates fused per object (higher = more merging)", False),
    ("relations", "Relations", "#spatial relations", True),
    ("mean_uncertainty", "Mean uncertainty", "avg node uncertainty", False),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export a fusion-variant structural comparison table.")
    p.add_argument("--results-root", type=Path, required=True)
    p.add_argument("--view-counts", type=int, nargs="+", default=[3, 5, 8, 10])
    p.add_argument("--baseline-variant", default="graph-fusion")
    p.add_argument("--markdown-output", type=Path)
    p.add_argument("--csv-output", type=Path)
    return p.parse_args()


def stats_for(path: Path) -> dict[str, float]:
    d = json.loads(path.read_text())
    nodes = d.get("nodes", [])
    pipe = d.get("pipeline", {})
    src = [int(n.get("metadata", {}).get("num_source_nodes", 1)) for n in nodes]
    unc = [float(n.get("uncertainty", 0.0)) for n in nodes]
    return {
        "candidate_nodes": pipe.get("num_candidate_nodes") or 0,
        "fused_objects": len(nodes),
        "multi_view_objects": sum(1 for n in nodes if int(n.get("metadata", {}).get("num_views", 0)) >= 2),
        "mean_source_nodes": statistics.mean(src) if src else 0.0,
        "relations": len(d.get("relations", [])),
        "mean_uncertainty": statistics.mean(unc) if unc else 0.0,
    }


def discover_variants(root: Path, baseline: str) -> list[str]:
    variants = [baseline]
    vdir = root / "variants"
    if vdir.is_dir():
        variants += sorted(p.name for p in vdir.iterdir() if p.is_dir())
    return variants


def glob_for(root: Path, variant: str, baseline: str, v: int) -> list[str]:
    sub = f"views_{v:02d}"
    if variant == baseline:
        return sorted(glob(str(root / f"*/{sub}/scene_graph.json")))
    return sorted(glob(str(root / "variants" / variant / f"*/{sub}/scene_graph.json")))


def aggregate(root: Path, variant: str, baseline: str, view_counts: list[int]) -> dict[int, dict | None]:
    out: dict[int, dict | None] = {}
    for v in view_counts:
        files = [f for f in glob_for(root, variant, baseline, v) if "/variants/" in f or variant == baseline]
        if not files:
            out[v] = None
            continue
        rows = [stats_for(Path(f)) for f in files]
        out[v] = {k: statistics.mean([r[k] for r in rows]) for k in rows[0]}
        out[v]["n_scenes"] = len(files)
    return out


def main() -> None:
    args = parse_args()
    root = args.results_root
    variants = discover_variants(root, args.baseline_variant)
    data = {var: aggregate(root, var, args.baseline_variant, args.view_counts) for var in variants}

    lines: list[str] = ["# Fusion Variant Structural Comparison", ""]
    lines.append(f"Results root: `{root}`  ·  view counts: {args.view_counts}")
    lines.append("")
    lines.append("Structural (annotation-free) statistics, averaged over scenes. Object/relation")
    lines.append("F1 require the labelling + checked-annotation stages (run on GPU/Colab).")
    for key, title, desc, intish in METRICS:
        lines.append("")
        lines.append(f"## {title} — {desc}")
        lines.append("| variant | " + " | ".join(f"views={v}" for v in args.view_counts) + " |")
        lines.append("|---" * (len(args.view_counts) + 1) + "|")
        for var in variants:
            cells = []
            for v in args.view_counts:
                r = data[var][v]
                cells.append("-" if r is None else (f"{r[key]:.1f}" if intish else f"{r[key]:.4f}"))
            lines.append(f"| {var} | " + " | ".join(cells) + " |")
    md = "\n".join(lines) + "\n"

    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(md, encoding="utf-8")
        print(f"Wrote {args.markdown_output}")
    else:
        print(md)

    if args.csv_output:
        args.csv_output.parent.mkdir(parents=True, exist_ok=True)
        with args.csv_output.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["variant", "view_count", "n_scenes", "candidate_nodes", "fused_objects",
                        "multi_view_objects", "mean_source_nodes", "relations", "mean_uncertainty"])
            for var in variants:
                for v in args.view_counts:
                    r = data[var][v]
                    if r is None:
                        continue
                    w.writerow([var, v, int(r["n_scenes"]), round(r["candidate_nodes"], 2),
                                round(r["fused_objects"], 2), round(r["multi_view_objects"], 2),
                                round(r["mean_source_nodes"], 4), round(r["relations"], 2),
                                round(r["mean_uncertainty"], 6)])
        print(f"Wrote {args.csv_output}")


if __name__ == "__main__":
    main()
