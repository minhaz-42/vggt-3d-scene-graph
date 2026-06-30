#!/usr/bin/env python3
"""VGGT-style teaser: real input RGB frames -> real colored 3D reconstruction with an
open-vocabulary 3D scene graph (labeled object nodes). All real data from a vggt_geometry.npz
(which stores the input images) + the fused scene graph."""
import argparse, json, os
from collections import defaultdict
from pathlib import Path
import numpy as np
os.environ.setdefault("MPLCONFIGDIR", "/tmp/vggt_mpl"); Path("/tmp/vggt_mpl").mkdir(exist_ok=True)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.patches import FancyArrowPatch

LCOL = {"monitor":"#3D5A80","desk":"#D9822B","keyboard":"#2E7D5B","book":"#7B4FA3","chair":"#C0392B",
        "floor":"#9AA0A6","wall":"#B0A48F","lamp":"#E0A800","box":"#5B8C5A","trash can":"#8C6D5B",
        "cup":"#1F9E9E","bottle":"#C2569B","person":"#D81B60","bag":"#6A8CAF","door":"#A0671F"}

def load(npz, conf_pct, maxpts, seed=0):
    d = np.load(npz, allow_pickle=True)
    wp=d["world_points"][0]; im=np.transpose(d["images"][0],(0,2,3,1)); cf=d["world_points_conf"][0]
    P=wp.reshape(-1,3); C=im.reshape(-1,3); K=cf.reshape(-1)
    m=K>=np.percentile(K,conf_pct); P,C=P[m],C[m]
    lo,hi=np.percentile(P,[1,99],axis=0)
    k=np.all((P>=lo-0.15)&(P<=hi+0.15),axis=1); P,C=P[k],C[k]
    r=np.random.default_rng(seed)
    if len(P)>maxpts: i=r.choice(len(P),maxpts,replace=False); P,C=P[i],C[i]
    Pd=np.column_stack([P[:,0],P[:,2],-P[:,1]])
    return Pd, np.clip(C,0,1), np.transpose(d["images"][0],(0,2,3,1))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("npz"); ap.add_argument("graph")
    ap.add_argument("--out", default="paper/figures/fig_teaser.pdf")
    ap.add_argument("--elev", type=float, default=26); ap.add_argument("--azim", type=float, default=-115)
    ap.add_argument("--frames", default="0,4,8")
    ap.add_argument("--conf-pct", type=float, default=48); ap.add_argument("--maxpts", type=int, default=95000)
    a=ap.parse_args()
    P,C,imgs = load(a.npz, a.conf_pct, a.maxpts)
    plt.rcParams.update({"font.family":"serif"})
    fig=plt.figure(figsize=(7.2,3.4))
    gs=gridspec.GridSpec(3,3,width_ratios=[1.0,0.12,3.2],height_ratios=[1,1,1],wspace=0.02,hspace=0.08)

    # left: 3 real input frames
    fr=[int(x) for x in a.frames.split(",")]
    for r,fi in enumerate(fr):
        ax=fig.add_subplot(gs[r,0]); ax.imshow(np.clip(imgs[fi],0,1)); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_edgecolor("#888"); s.set_linewidth(0.8)
        if r==0: ax.set_title("sparse RGB views", fontsize=8.5, color="#222")
    # arrow column
    axm=fig.add_subplot(gs[:,1]); axm.axis("off")
    axm.annotate("", xy=(0.9,0.5), xytext=(0.0,0.5), xycoords="axes fraction",
                 arrowprops=dict(arrowstyle="-|>", color="#444", lw=1.6))

    # right: 3D reconstruction + scene graph labels
    ax=fig.add_subplot(gs[:,2], projection="3d")
    ax.scatter(P[:,0],P[:,1],P[:,2],c=C,s=2.0,marker=".",depthshade=False,edgecolors="none",linewidths=0)
    ax.view_init(elev=a.elev,azim=a.azim); ax.set_axis_off()
    ax.set_box_aspect((np.ptp(P[:,0]),np.ptp(P[:,1]),np.ptp(P[:,2])))
    for L,fn in (("x",ax.set_xlim),("y",ax.set_ylim),("z",ax.set_zlim)):
        pass
    ax.set_xlim(np.percentile(P[:,0],[1,99])); ax.set_ylim(np.percentile(P[:,1],[1,99])); ax.set_zlim(np.percentile(P[:,2],[1,99]))
    ax.set_title("open-vocabulary 3D scene graph", fontsize=8.5, color="#222", y=0.98)

    g=json.load(open(a.graph)); nodes=g["nodes"]
    cz=[np.array(n["centroid_xyz"]) for n in nodes]; lb=[n["label"] for n in nodes]
    parent=list(range(len(nodes)))
    def f(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for i in range(len(nodes)):
        for j in range(i+1,len(nodes)):
            if lb[i]==lb[j] and np.linalg.norm(cz[i]-cz[j])<1.25: parent[f(i)]=f(j)
    grp=defaultdict(list)
    for i in range(len(nodes)): grp[f(i)].append(i)
    items=[(lb[m[0]], np.mean([cz[k] for k in m],axis=0), sum(nodes[k]["num_points"] for k in m)) for m in grp.values()]
    items=[t for t in items if t[0] not in ("floor","wall")]
    items.sort(key=lambda t:-t[2])
    items=items[:8]
    def disp(c): return np.array([c[0],c[2],-c[1]])
    placed=[]
    for lab,c,_ in items:
        p=disp(c); col=LCOL.get(lab,"#444")
        # nudge text up a little extra if close to a previously placed label
        dz=0.07
        for q in placed:
            if abs(p[0]-q[0])<0.18 and abs(p[1]-q[1])<0.18: dz+=0.10
        placed.append(p)
        ax.scatter([p[0]],[p[1]],[p[2]],s=30,c=col,edgecolors="white",linewidths=1.0,depthshade=False,zorder=10)
        ax.text(p[0],p[1],p[2]+dz,lab,fontsize=7.4,color="#111",zorder=11,ha="center",fontweight="medium",
                bbox=dict(facecolor="white",edgecolor=col,linewidth=0.5,alpha=0.9,pad=0.5,boxstyle="round,pad=0.25"))
    fig.savefig(a.out, dpi=220, bbox_inches="tight", pad_inches=0.02)
    print("wrote", a.out)

if __name__=="__main__": main()
