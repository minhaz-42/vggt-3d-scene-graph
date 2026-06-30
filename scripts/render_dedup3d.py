#!/usr/bin/env python3
"""Real 3D before/after duplicate-aware merge, overlaid on the actual VGGT point cloud.
Left: graph-fusion leaves the same physical object as many same-label nodes (over-counting).
Right: duplicate-aware merge collapses them to one node per object."""
import argparse, json, os
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
os.environ.setdefault("MPLCONFIGDIR","/tmp/vggt_mpl"); Path("/tmp/vggt_mpl").mkdir(exist_ok=True)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

LCOL={"monitor":"#3D5A80","desk":"#D9822B","keyboard":"#2E7D5B","book":"#7B4FA3","chair":"#C0392B",
      "floor":"#9AA0A6","wall":"#B0A48F","lamp":"#E0A800","box":"#5B8C5A","trash can":"#8C6D5B",
      "cup":"#1F9E9E","bottle":"#C2569B","person":"#D81B60","bag":"#6A8CAF","door":"#A0671F"}

def D(P): return np.column_stack([P[:,0],P[:,2],-P[:,1]])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("npz"); ap.add_argument("graph")
    ap.add_argument("--out",default="paper/figures/fig_dedup3d.png")
    ap.add_argument("--elev",type=float,default=32); ap.add_argument("--azim",type=float,default=-120)
    ap.add_argument("--conf-pct",type=float,default=60); ap.add_argument("--maxpts",type=int,default=90000)
    a=ap.parse_args()
    d=np.load(a.npz,allow_pickle=True)
    wp=d["world_points"][0]; im=np.transpose(d["images"][0],(0,2,3,1)); cf=d["world_points_conf"][0]
    P=wp.reshape(-1,3); C=im.reshape(-1,3); K=cf.reshape(-1)
    m=K>=np.percentile(K,a.conf_pct); P,C=P[m],C[m]
    lo,hi=np.percentile(P,[1.5,98.5],axis=0); k=np.all((P>=lo-0.1)&(P<=hi+0.1),axis=1); P,C=P[k],C[k]
    r=np.random.default_rng(0)
    if len(P)>a.maxpts: i=r.choice(len(P),a.maxpts,replace=False); P,C=P[i],C[i]
    Pd=D(P)
    # desaturate cloud so colored markers pop
    lum=C@np.array([0.299,0.587,0.114]); Cf=np.clip(0.55*C+0.45*lum[:,None],0,1)

    g=json.load(open(a.graph)); nodes=g["nodes"]; cz=[np.array(n["centroid_xyz"]) for n in nodes]; lb=[n["label"] for n in nodes]
    par=list(range(len(nodes)))
    def f(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for i in range(len(nodes)):
        for j in range(i+1,len(nodes)):
            if lb[i]==lb[j] and np.linalg.norm(cz[i]-cz[j])<1.25: par[f(i)]=f(j)
    grp=defaultdict(list)
    for i in range(len(nodes)): grp[f(i)].append(i)
    merged=[(lb[mm[0]],np.mean([cz[c] for c in mm],axis=0)) for mm in grp.values()]
    cnt=Counter(lb)
    cc=np.array(cz); clo,chi=np.percentile(cc,[3,96],axis=0)  # skip spatial-outlier nodes (e.g. far lamp)
    def inb(c): return bool(np.all(c>=clo-1e-6) and np.all(c<=chi+1e-6))

    plt.rcParams.update({"font.family":"serif"})
    fig=plt.figure(figsize=(7.4,3.6))
    def setup(ax,title):
        ax.scatter(Pd[:,0],Pd[:,1],Pd[:,2],c=Cf,s=2.2,marker=".",depthshade=False,edgecolors="none",linewidths=0,alpha=0.45,rasterized=True)
        ax.view_init(elev=a.elev,azim=a.azim); ax.set_axis_off()
        ax.set_box_aspect((np.ptp(Pd[:,0]),np.ptp(Pd[:,1]),np.ptp(Pd[:,2])))
        ax.set_xlim(np.percentile(Pd[:,0],[1,99])); ax.set_ylim(np.percentile(Pd[:,1],[1,99])); ax.set_zlim(np.percentile(Pd[:,2],[1,99]))
        ax.set_title(title,fontsize=9.5,y=0.99)
    # LEFT: before
    axA=fig.add_subplot(1,2,1,projection="3d"); setup(axA,f"graph-fusion: {len(nodes)} object nodes")
    for i in range(len(nodes)):
        if lb[i] in ("floor","wall") or not inb(cz[i]): continue
        p=D(cz[i][None,:])[0]
        axA.scatter([p[0]],[p[1]],[p[2]],s=26,c=LCOL.get(lb[i],"#555"),edgecolors="white",linewidths=0.5,depthshade=False,zorder=20,alpha=0.95)
    for lab in ("monitor","desk"):
        if cnt[lab]>=3:
            ctr=D(np.mean([cz[i] for i in range(len(nodes)) if lb[i]==lab],axis=0)[None,:])[0]
            off=0.50 if lab=="desk" else 0.20
            axA.text(ctr[0],ctr[1],ctr[2]+off,f"{lab}$\\times${cnt[lab]}",fontsize=9,color=LCOL[lab],fontweight="bold",
                     ha="center",zorder=22,bbox=dict(facecolor="white",edgecolor=LCOL[lab],linewidth=0.7,alpha=1.0,boxstyle="round,pad=0.28"))
    # RIGHT: after
    axB=fig.add_subplot(1,2,2,projection="3d"); setup(axB,f"+ duplicate-aware merge: {len(merged)} nodes")
    for lab,c in merged:
        if lab in ("floor","wall") or not inb(c): continue
        p=D(c[None,:])[0]; col=LCOL.get(lab,"#555")
        axB.scatter([p[0]],[p[1]],[p[2]],s=54,c=col,edgecolors="white",linewidths=1.0,depthshade=False,zorder=20)
        axB.text(p[0],p[1],p[2]+0.08,lab,fontsize=7.2,color="#111",ha="center",zorder=21,
                 bbox=dict(facecolor="white",edgecolor=col,linewidth=0.5,alpha=1.0,boxstyle="round,pad=0.22"))
    fig.tight_layout(w_pad=0.5); fig.savefig(a.out,dpi=300,bbox_inches="tight",pad_inches=0.02)
    print("wrote",a.out,"| before",len(nodes),dict(cnt.most_common(4)),"| after",len(merged))

if __name__=="__main__": main()
