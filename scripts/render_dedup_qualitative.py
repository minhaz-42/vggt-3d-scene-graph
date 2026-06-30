#!/usr/bin/env python3
"""Render a faithful before/after duplicate-aware-merge figure from a real fused scene graph.

Uses real fused-node centroids (projected onto their top-2 principal axes for a readable
2D layout). The "before" panel shows the raw graph-fusion nodes (same-label duplicates in
the same color reveal over-counting); the "after" panel collapses same-label nodes that are
spatially close and draws the surviving relation edges. Output: paper/figures/fig_qual.pdf
"""
import json, sys
from collections import defaultdict, Counter
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

GRAPH = sys.argv[1] if len(sys.argv) > 1 else \
    "results/benchmark_owlv2_expanded/tum_rgbd_freiburg1_desk/views_10/scene_graph_labeled.json"
OUT = "paper/figures/fig_qual.pdf"

# palette consistent with the LaTeX figures
LCOL = {
    "monitor": "#3D5A80", "desk": "#D9822B", "keyboard": "#2E7D5B", "book": "#7B4FA3",
    "chair": "#C0392B", "floor": "#9AA0A6", "wall": "#B0A48F", "lamp": "#E0A800",
    "box": "#5B8C5A", "trash can": "#8C6D5B", "cup": "#1F9E9E", "bottle": "#C2569B",
}
def color_for(lab): return LCOL.get(lab, "#B7BBC2")

d = json.load(open(GRAPH))
nodes = d["nodes"]
ids = [n["node_id"] for n in nodes]
labels = [n["label"] for n in nodes]
cents = np.array([n["centroid_xyz"] for n in nodes], dtype=float)
npts = np.array([n.get("num_points", 1) for n in nodes], dtype=float)

# project onto top-2 principal axes for a readable, spread-out 2D layout
c0 = cents.mean(0)
U, S, Vt = np.linalg.svd(cents - c0, full_matrices=False)
P = (cents - c0) @ Vt[:2].T  # (N,2)

# --- duplicate-aware merge (illustrative): union same-label nodes within a distance ---
# threshold chosen to reflect the 3D-box-overlap merge used by the benchmark metric.
THRESH = 1.25
parent = list(range(len(nodes)))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b):
    parent[find(a)] = find(b)
for i in range(len(nodes)):
    for j in range(i + 1, len(nodes)):
        if labels[i] == labels[j] and np.linalg.norm(cents[i] - cents[j]) < THRESH:
            union(i, j)
groups = defaultdict(list)
for i in range(len(nodes)):
    groups[find(i)].append(i)

before_counts = Counter(labels)
after_labels = [labels[g[0]] for g in groups.values()]
print(f"before: {len(nodes)} nodes  {dict(before_counts.most_common())}")
print(f"after : {len(groups)} nodes  {dict(Counter(after_labels).most_common())}")

# merged node positions (mean of group in 2D + 3D)
merged = []
idx_to_group = {}
for gi, (root, members) in enumerate(groups.items()):
    p2 = P[members].mean(0); c3 = cents[members].mean(0); npt = npts[members].sum()
    merged.append(dict(label=labels[members[0]], p=p2, c=c3, npts=npt, n=len(members)))
    for m in members:
        idx_to_group[m] = gi

# surviving relations between distinct merged groups
id_to_idx = {nid: k for k, nid in enumerate(ids)}
rel_pairs = set()
for r in d.get("relations", []):
    s = r.get("subject_id") or r.get("source"); o = r.get("object_id") or r.get("target")
    pred = r.get("predicate") or r.get("relation")
    if s in id_to_idx and o in id_to_idx:
        gs, go = idx_to_group[id_to_idx[s]], idx_to_group[id_to_idx[o]]
        if gs != go and pred in ("on", "near", "supported_by", "above"):
            rel_pairs.add((min(gs, go), max(gs, go)))

# ---------------- plot ----------------
plt.rcParams.update({"font.family": "serif", "font.size": 9, "svg.fonttype": "none"})
fig, (axA, axB) = plt.subplots(1, 2, figsize=(7.0, 3.2))

def style(ax, title):
    ax.set_title(title, fontsize=9.5)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor("#888"); sp.set_linewidth(0.6)
    ax.set_aspect("equal", adjustable="datalim")

# Panel A: before (over-counting)
style(axA, f"graph-fusion baseline: {len(nodes)} nodes")
for i in range(len(nodes)):
    axA.scatter(P[i, 0], P[i, 1], s=40 + 90 * np.sqrt(npts[i] / npts.max()),
                color=color_for(labels[i]), edgecolor="white", linewidth=0.5, alpha=0.9, zorder=3)
# ring + count on the over-counted clusters
for lab in ("monitor", "desk"):
    members = [i for i in range(len(nodes)) if labels[i] == lab]
    if len(members) >= 3:
        pts = P[members]; ctr = pts.mean(0)
        rx = (pts[:, 0].max() - pts[:, 0].min()) + 0.5
        ry = (pts[:, 1].max() - pts[:, 1].min()) + 0.5
        axA.add_patch(Ellipse(ctr, rx, ry, fill=False, edgecolor=color_for(lab),
                              lw=1.0, ls="--", alpha=0.8, zorder=2))
        axA.annotate(f"{lab}×{len(members)}", ctr + np.array([0, ry / 2 + 0.42]),
                     ha="center", va="bottom", fontsize=8.5, color=color_for(lab), fontweight="bold",
                     zorder=5, bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=0.6))

# Panel B: after (merged + relations)
style(axB, f"+ duplicate-aware merge: {len(groups)} nodes")
for (a, b) in rel_pairs:
    pa, pb = merged[a]["p"], merged[b]["p"]
    axB.plot([pa[0], pb[0]], [pa[1], pb[1]], color="#BBBBBB", lw=0.7, zorder=1)
ymid = np.median([m["p"][1] for m in merged])
for m in merged:
    axB.scatter(m["p"][0], m["p"][1], s=70 + 120 * np.sqrt(m["npts"] / npts.sum()),
                color=color_for(m["label"]), edgecolor="white", linewidth=0.7, zorder=3)
    up = m["p"][1] >= ymid
    off = np.array([0, 0.22 if up else -0.22]); va = "bottom" if up else "top"
    axB.annotate(m["label"], m["p"] + off, ha="center", va=va, fontsize=7.5, color="#222433",
                 zorder=5, bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=0.4))

# shared limits with margin
allp = np.vstack([P, np.array([m["p"] for m in merged])])
xpad = 0.18 * (allp[:, 0].max() - allp[:, 0].min()); ypad = 0.22 * (allp[:, 1].max() - allp[:, 1].min())
for ax in (axA, axB):
    ax.set_xlim(allp[:, 0].min() - xpad, allp[:, 0].max() + xpad)
    ax.set_ylim(allp[:, 1].min() - ypad, allp[:, 1].max() + ypad)

fig.tight_layout(w_pad=1.5)
fig.savefig(OUT, bbox_inches="tight", pad_inches=0.02)
print("wrote", OUT)
