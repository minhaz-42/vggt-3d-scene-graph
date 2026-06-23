from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/vggt_scene_graph_matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/vggt_scene_graph_cache")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a simple 3D scene graph visualization.")
    parser.add_argument("scene_graph", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/scene_graph.png"))
    parser.add_argument("--relation", default="near", help="Relation type to draw as edges.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.scene_graph.read_text(encoding="utf-8"))
    nodes = payload.get("nodes", [])
    relations = payload.get("relations", [])
    node_by_id = {node["node_id"]: node for node in nodes}

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_title(f"{payload.get('scene_id', 'scene')} scene graph")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")

    xs = []
    ys = []
    zs = []
    labels = []
    colors = []
    for node in nodes:
        x, y, z = node["centroid_xyz"]
        xs.append(x)
        ys.append(y)
        zs.append(z)
        labels.append(node["node_id"])
        colors.append(float(node.get("uncertainty", 0.0)))

    scatter = ax.scatter(xs, ys, zs, c=colors, cmap="viridis_r", s=70, depthshade=True)
    fig.colorbar(scatter, ax=ax, shrink=0.65, label="uncertainty")

    for node_id, x, y, z in zip(labels, xs, ys, zs, strict=True):
        ax.text(x, y, z, node_id.replace("object_", "o"), fontsize=8)

    for edge in relations:
        if edge.get("relation") != args.relation:
            continue
        subject = node_by_id.get(edge.get("subject_id"))
        obj = node_by_id.get(edge.get("object_id"))
        if subject is None or obj is None:
            continue
        sx, sy, sz = subject["centroid_xyz"]
        ox, oy, oz = obj["centroid_xyz"]
        ax.plot([sx, ox], [sy, oy], [sz, oz], color="0.35", alpha=0.25, linewidth=1)

    ax.view_init(elev=22, azim=-58)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    print(f"Wrote scene graph visualization to {args.output}")


if __name__ == "__main__":
    main()
