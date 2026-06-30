#!/usr/bin/env python3
"""Render real RGB frames with OWLv2 open-vocabulary detection boxes + labels overlaid.
Demonstrates that the detector front-end recovers real, named objects on the actual frames."""
import argparse, json, os
from collections import defaultdict
from pathlib import Path
import numpy as np
os.environ.setdefault("MPLCONFIGDIR", "/tmp/vggt_mpl"); Path("/tmp/vggt_mpl").mkdir(exist_ok=True)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.image as mpimg

LCOL = {"monitor":"#3D5A80","desk":"#D9822B","keyboard":"#2E7D5B","book":"#7B4FA3","chair":"#C0392B",
        "floor":"#9AA0A6","wall":"#B0A48F","lamp":"#E0A800","box":"#5B8C5A","trash can":"#8C6D5B",
        "cup":"#1F9E9E","bottle":"#C2569B","person":"#D81B60","bag":"#6A8CAF","door":"#A0671F",
        "plant":"#3C8C3C","picture":"#9C27B0","teddy bear":"#C97B3C","globe":"#2E86C1"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("proposals"); ap.add_argument("frames_dir")
    ap.add_argument("--out", default="paper/figures/fig_detections.pdf")
    ap.add_argument("--nframes", type=int, default=3)
    ap.add_argument("--score", type=float, default=0.30)
    ap.add_argument("--max-per-frame", type=int, default=7)
    a=ap.parse_args()
    pj=json.load(open(a.proposals)); props=pj["proposals"]
    by=defaultdict(list)
    for p in props:
        if p["owlv2_score"]>=a.score: by[p["view_id"]].append(p)
    # pick frames with the most confident, diverse detections
    order=sorted(by.keys(), key=lambda v:-len({pp["owlv2_label"] for pp in by[v]}))
    frames=order[:a.nframes]
    plt.rcParams.update({"font.family":"serif"})
    fig,axs=plt.subplots(1,len(frames),figsize=(3.0*len(frames),2.5))
    if len(frames)==1: axs=[axs]
    for ax,vid in zip(axs,frames):
        img=mpimg.imread(str(Path(a.frames_dir)/f"{vid}.png"))
        ax.imshow(img); ax.set_xticks([]); ax.set_yticks([])
        dets=sorted(by[vid], key=lambda p:-p["owlv2_score"])[:a.max_per_frame]
        for p in dets:
            x0,y0,x1,y1=p["bbox_xyxy"]; lab=p["owlv2_label"]; col=LCOL.get(lab,"#E07B39")
            ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor=col,linewidth=1.6))
            ax.text(x0+1,max(y0-2,8),f"{lab} {p['owlv2_score']:.2f}",fontsize=6.0,color="white",
                    va="bottom",ha="left",bbox=dict(facecolor=col,edgecolor="none",pad=0.6,alpha=0.92))
        for s in ax.spines.values(): s.set_edgecolor("#888"); s.set_linewidth(0.8)
    fig.tight_layout(w_pad=0.6)
    fig.savefig(a.out, dpi=200, bbox_inches="tight", pad_inches=0.02)
    print("wrote", a.out, "frames:", frames)

if __name__=="__main__": main()
