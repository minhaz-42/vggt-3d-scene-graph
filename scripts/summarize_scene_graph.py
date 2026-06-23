from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize generated scene graph JSON files.")
    parser.add_argument("scene_graphs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, default=Path("results/scene_graph_summary.csv"))
    return parser.parse_args()


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def summarize(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
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
        "num_nodes": len(nodes),
        "num_relations": len(relations),
        "num_candidate_nodes": pipeline.get("num_candidate_nodes"),
        "multi_view_nodes": len(multi_view_nodes),
        "mean_uncertainty": round(_mean(uncertainties), 6),
        "proposal_feature_backends": ",".join(pipeline.get("proposal_feature_backends", [])),
        "geometry_path": pipeline.get("geometry_path"),
        "proposals_path": pipeline.get("proposals_path"),
    }


def main() -> None:
    args = parse_args()
    rows = [summarize(path) for path in args.scene_graphs]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote summary to {args.output}")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
