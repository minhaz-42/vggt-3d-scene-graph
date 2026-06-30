#!/usr/bin/env python3
"""Render a real VGGT world-point cloud (colored by RGB) as a VGGT-style 3D figure.

Loads a vggt_geometry.npz (world_points + images + confidence + camera poses) and renders
an oblique colored point cloud with matplotlib 3D. Supports a viewpoint-grid preview (to pick
the best angle) and a single clean render, optionally with camera frustums and labeled object
nodes from a scene graph (before/after duplicate-aware merge).
"""
import argparse, json, os
from pathlib import Path
import numpy as np
os.environ.setdefault("MPLCONFIGDIR", "/tmp/vggt_mpl")
Path("/tmp/vggt_mpl").mkdir(exist_ok=True)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

LCOL = {"monitor":"#3D5A80","desk":"#D9822B","keyboard":"#2E7D5B","book":"#7B4FA3",
        "chair":"#C0392B","floor":"#9AA0A6","wall":"#B0A48F","lamp":"#E0A800","box":"#5B8C5A",
        "trash can":"#8C6D5B","cup":"#1F9E9E","bottle":"#C2569B","person":"#D81B60"}

def load_cloud(npz, conf_pct, max_points, seed=0):
    d = np.load(npz, allow_pickle=True)
    wp = d["world_points"][0]            # (V,H,W,3)
    im = np.transpose(d["images"][0], (0, 2, 3, 1))  # (V,H,W,3) in 0..1
    conf = d["world_points_conf"][0]     # (V,H,W)
    V = wp.shape[0]
    P = wp.reshape(-1, 3); C = im.reshape(-1, 3); K = conf.reshape(-1)
    thr = np.percentile(K, conf_pct)
    m = K >= thr
    P, C = P[m], C[m]
    # spatial outlier trim (robust axis limits)
    lo, hi = np.percentile(P, [1, 99], axis=0)
    keep = np.all((P >= lo - 0.15) & (P <= hi + 0.15), axis=1)
    P, C = P[keep], C[keep]
    rng = np.random.default_rng(seed)
    if len(P) > max_points:
        idx = rng.choice(len(P), max_points, replace=False); P, C = P[idx], C[idx]
    # OpenCV cam frame (y down, z fwd) -> display with up = -y
    Pd = np.column_stack([P[:, 0], P[:, 2], -P[:, 1]])
    return Pd, np.clip(C, 0, 1), d

def style_axes(ax, P, hide=True):
    ax.set_box_aspect((np.ptp(P[:,0]), np.ptp(P[:,1]), np.ptp(P[:,2])))
    if hide:
        ax.set_axis_off()
    ax.set_xlim(np.percentile(P[:,0],[1,99])); ax.set_ylim(np.percentile(P[:,1],[1,99]))
    ax.set_zlim(np.percentile(P[:,2],[1,99]))
    try: ax.set_proj_type("persp")
    except Exception: pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("npz")
    ap.add_argument("--out", default="paper/figures/_pc.png")
    ap.add_argument("--grid", action="store_true", help="2x2 viewpoint preview")
    ap.add_argument("--elev", type=float, default=22)
    ap.add_argument("--azim", type=float, default=-72)
    ap.add_argument("--conf-pct", type=float, default=55)
    ap.add_argument("--max-points", type=int, default=70000)
    ap.add_argument("--size", type=float, default=1.4)
    ap.add_argument("--graph", default=None, help="scene_graph_labeled.json for object overlay")
    ap.add_argument("--dedup", action="store_true", help="overlay merged objects instead of raw")
    args = ap.parse_args()

    P, C, d = load_cloud(args.npz, args.conf_pct, args.max_points)
    plt.rcParams.update({"font.family": "serif"})

    if args.grid:
        views = [(18, -72), (22, 30), (40, -120), (12, -150)]
        fig = plt.figure(figsize=(9, 8))
        for i, (e, a) in enumerate(views, 1):
            ax = fig.add_subplot(2, 2, i, projection="3d")
            ax.scatter(P[:,0], P[:,1], P[:,2], c=C, s=args.size, marker=".",
                       depthshade=False, edgecolors="none", linewidths=0)
            ax.view_init(elev=e, azim=a); style_axes(ax, P)
            ax.set_title(f"elev={e}, azim={a}", fontsize=9)
        fig.tight_layout(); fig.savefig(args.out, dpi=150, bbox_inches="tight", pad_inches=0.05)
        print("wrote grid", args.out); return

    fig = plt.figure(figsize=(5.2, 4.2))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(P[:,0], P[:,1], P[:,2], c=C, s=args.size, marker=".",
               depthshade=False, edgecolors="none", linewidths=0)
    ax.view_init(elev=args.elev, azim=args.azim); style_axes(ax, P)

    if args.graph:
        g = json.load(open(args.graph)); nodes = g["nodes"]
        def disp(c): return np.array([c[0], c[2], -c[1]])
        if args.dedup:
            from collections import defaultdict
            parent = list(range(len(nodes)))
            def f(a):
                while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
                return a
            cz=[n["centroid_xyz"] for n in nodes]; lb=[n["label"] for n in nodes]
            for i in range(len(nodes)):
                for j in range(i+1,len(nodes)):
                    if lb[i]==lb[j] and np.linalg.norm(np.array(cz[i])-np.array(cz[j]))<1.25:
                        parent[f(i)]=f(j)
            grp=defaultdict(list)
            for i in range(len(nodes)): grp[f(i)].append(i)
            items=[(lb[m[0]], np.mean([cz[k] for k in m],axis=0)) for m in grp.values()]
        else:
            items=[(n["label"], np.array(n["centroid_xyz"])) for n in nodes]
        for lab, c in items:
            p = disp(c); col = LCOL.get(lab, "#444")
            ax.scatter([p[0]],[p[1]],[p[2]], s=70, c=col, edgecolors="white",
                       linewidths=1.0, depthshade=False, zorder=10)
            ax.text(p[0], p[1], p[2]+0.04, lab, fontsize=6.5, color="#111", zorder=11)

    fig.savefig(args.out, dpi=200, bbox_inches="tight", pad_inches=0.02)
    print("wrote", args.out, "| points:", len(P))

if __name__ == "__main__":
    main()
