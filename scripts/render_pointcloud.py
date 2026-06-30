#!/usr/bin/env python3
"""Render a real VGGT world-point cloud (colored by RGB) as a crisp VGGT-style 3D figure,
with optional camera frustums (from real extrinsics/intrinsics) and labeled object nodes."""
import argparse, json, os
from collections import defaultdict
from pathlib import Path
import numpy as np
os.environ.setdefault("MPLCONFIGDIR", "/tmp/vggt_mpl"); Path("/tmp/vggt_mpl").mkdir(exist_ok=True)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

LCOL = {"monitor":"#3D5A80","desk":"#D9822B","keyboard":"#2E7D5B","book":"#7B4FA3","chair":"#C0392B",
        "floor":"#9AA0A6","wall":"#B0A48F","lamp":"#E0A800","box":"#5B8C5A","trash can":"#8C6D5B",
        "cup":"#1F9E9E","bottle":"#C2569B","person":"#D81B60","bag":"#6A8CAF","door":"#A0671F"}

def disp(P):  # OpenCV cam frame (y down, z fwd) -> display up = -y
    return np.column_stack([P[:,0], P[:,2], -P[:,1]])

def load(npz, conf_pct, maxpts, seed=0):
    d = np.load(npz, allow_pickle=True)
    wp=d["world_points"][0]; im=np.transpose(d["images"][0],(0,2,3,1)); cf=d["world_points_conf"][0]
    P=wp.reshape(-1,3); C=im.reshape(-1,3); K=cf.reshape(-1)
    m=K>=np.percentile(K,conf_pct); P,C=P[m],C[m]
    lo,hi=np.percentile(P,[1.5,98.5],axis=0)
    k=np.all((P>=lo-0.1)&(P<=hi+0.1),axis=1); P,C=P[k],C[k]
    r=np.random.default_rng(seed)
    if len(P)>maxpts: i=r.choice(len(P),maxpts,replace=False); P,C=P[i],C[i]
    return disp(P), np.clip(C,0,1), d

def frustums(ax, d, scale, color="#33415C"):
    extr=d["camera_extrinsics"][0]; intr=d["camera_intrinsics"][0]
    H,W = d["world_points"][0].shape[1], d["world_points"][0].shape[2]
    depth=0.13*scale
    idx=np.unique(np.linspace(0,extr.shape[0]-1,min(6,extr.shape[0])).astype(int))
    for v in idx:
        R=extr[v,:,:3]; t=extr[v,:,3]; Km=intr[v]; Ki=np.linalg.inv(Km)
        C=-R.T@t
        corners=[]
        for (u,w) in [(0,0),(W,0),(W,H),(0,H)]:
            ray=Ki@np.array([u,w,1.0]); pc=ray*depth
            corners.append(R.T@(pc-t))
        pts=disp(np.array([C]+corners))
        c0=pts[0]
        for cc in pts[1:]:
            ax.plot([c0[0],cc[0]],[c0[1],cc[1]],[c0[2],cc[2]],color=color,lw=0.5,alpha=0.7,zorder=12)
        sq=pts[1:][[0,1,2,3,0]]
        ax.plot(sq[:,0],sq[:,1],sq[:,2],color=color,lw=0.5,alpha=0.7,zorder=12)

def style(ax,P,hide=True):
    ax.set_box_aspect((np.ptp(P[:,0]),np.ptp(P[:,1]),np.ptp(P[:,2])))
    if hide: ax.set_axis_off()
    ax.set_xlim(np.percentile(P[:,0],[1,99])); ax.set_ylim(np.percentile(P[:,1],[1,99])); ax.set_zlim(np.percentile(P[:,2],[1,99]))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("npz"); ap.add_argument("--out", default="paper/figures/_pc.png")
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--elev", type=float, default=24); ap.add_argument("--azim", type=float, default=-113)
    ap.add_argument("--conf-pct", type=float, default=62); ap.add_argument("--max-points", type=int, default=150000)
    ap.add_argument("--size", type=float, default=3.2); ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--frustums", action="store_true")
    ap.add_argument("--graph", default=None); ap.add_argument("--dedup", action="store_true")
    a=ap.parse_args()
    P,C,d=load(a.npz,a.conf_pct,a.max_points); plt.rcParams.update({"font.family":"serif"})
    scale=float(np.mean([np.ptp(P[:,i]) for i in range(3)]))
    if a.grid:
        fig=plt.figure(figsize=(9,8))
        for i,(e,az) in enumerate([(18,-72),(24,-113),(40,-120),(12,-150)],1):
            ax=fig.add_subplot(2,2,i,projection="3d")
            ax.scatter(P[:,0],P[:,1],P[:,2],c=C,s=a.size,marker=".",depthshade=False,edgecolors="none",linewidths=0,rasterized=True)
            ax.view_init(elev=e,azim=az); style(ax,P); ax.set_title(f"elev={e} azim={az}",fontsize=9)
        fig.tight_layout(); fig.savefig(a.out,dpi=140,bbox_inches="tight",pad_inches=0.04); print("wrote grid",a.out); return
    fig=plt.figure(figsize=(5.4,4.4)); ax=fig.add_subplot(111,projection="3d")
    ax.scatter(P[:,0],P[:,1],P[:,2],c=C,s=a.size,marker=".",depthshade=False,edgecolors="none",linewidths=0,rasterized=True)
    ax.view_init(elev=a.elev,azim=a.azim); style(ax,P)
    if a.frustums: frustums(ax,d,scale)
    if a.graph:
        g=json.load(open(a.graph)); nodes=g["nodes"]; cz=[np.array(n["centroid_xyz"]) for n in nodes]; lb=[n["label"] for n in nodes]
        if a.dedup:
            par=list(range(len(nodes)))
            def f(x):
                while par[x]!=x: par[x]=par[par[x]]; x=par[x]
                return x
            for i in range(len(nodes)):
                for j in range(i+1,len(nodes)):
                    if lb[i]==lb[j] and np.linalg.norm(cz[i]-cz[j])<1.25: par[f(i)]=f(j)
            grp=defaultdict(list)
            for i in range(len(nodes)): grp[f(i)].append(i)
            items=[(lb[m[0]],np.mean([cz[k] for k in m],axis=0)) for m in grp.values()]
        else: items=[(lb[i],cz[i]) for i in range(len(nodes))]
        for lab,c in items:
            if lab in ("floor","wall"): continue
            p=disp(c[None,:])[0]; col=LCOL.get(lab,"#444")
            ax.scatter([p[0]],[p[1]],[p[2]],s=34,c=col,edgecolors="white",linewidths=1.0,depthshade=False,zorder=20)
            ax.text(p[0],p[1],p[2]+0.05,lab,fontsize=7,color="#111",ha="center",zorder=21,
                    bbox=dict(facecolor="white",edgecolor=col,linewidth=0.5,alpha=0.9,pad=0.4,boxstyle="round,pad=0.22"))
    fig.savefig(a.out,dpi=a.dpi,bbox_inches="tight",pad_inches=0.02); print("wrote",a.out,"points",len(P))

if __name__=="__main__": main()
