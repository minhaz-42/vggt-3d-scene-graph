# Open-vocabulary front-end fix: SAM-auto-mask + CLIP → OWLv2 detector

**Status:** Week 1 (GO/NO-GO + new proposal stage) — **GO, complete.**

## Why

The old front-end produced the project's central scientific flaw (see
`docs/` Phase-1 notes and the `critical-labeling-broken` finding): SAM *automatic* masks on
blurry low-res TUM RGB yielded surface/background fragments, and CLIP-per-patch then labeled
those fragments as room-scale categories. On `freiburg1_desk` (a desk with 2 monitors, a
keyboard, books, a chair) graph-fusion v10 predicted `floor:54, curtain:13, bed:6, door:3, …`
— none of the real objects. The `object_label_f1` headline was circular (CLIP graded against
CLIP), and against an independent reference the system scored ~3% F1.

The fix swaps **only the broken front-end** for a genuine open-vocabulary *detector*. Everything
downstream is unchanged and reused: VGGT 3D lifting, uncertainty-aware fusion, the scene graph,
the variant/control harness, and the independent-eval tooling.

## GO/NO-GO result (freiburg1_desk, 10 frames)

OWLv2 (`google/owlv2-base-patch16-ensemble`) queried with the project's indoor open-vocab
vocabulary finds the real objects, with high confidence and on every frame:

| | Old SAM-auto + CLIP (v10) | OWLv2 (now) |
|---|---|---|
| Top labels | floor:54, curtain:13, bed:6, door:3 | **keyboard ~0.8, monitor ~0.6, desk ~0.6** |
| Reference objects found | ~1/7 (only "floor") | **7/7** (monitor, keyboard, desk, book, chair, wall, floor) |

This is a decisive GO.

## Detector decision: OWLv2

- **OWLv2** — chosen. Already in the local HF cache; runs natively through `transformers`
  (no custom op compilation); runs on Apple MPS at **~3.3 s/frame** (50-frame subset ≈ 3 min,
  so the detection stage runs locally on the Mac — only VGGT geometry needed a GPU, and that
  is already cached). Genuine text-query open-vocab detector → the "open-vocab 3D scene graph"
  claim becomes true.
- **GroundingDINO** — rejected. Requires compiling custom CUDA/C++ ops (painful on macOS),
  not installed, and offers no advantage here over OWLv2 for this vocabulary.

## Operating point

- `threshold = 0.2`, **per-class NMS** `iou = 0.5` (the NMS mainly cleans the large "desk"
  surface, which otherwise gets many overlapping boxes).
- Per-frame over-detection (e.g. 4–6 "monitor" boxes for 2 real monitors) is **expected and
  acceptable**: overlapping boxes on the same physical object lift to the same 3D points and
  collapse in the downstream 3D fusion. So we do not over-tighten the 2D threshold.
- **Books are the recall-limited class** (small, stacked); lower thresholds recover more at the
  cost of noise. Worth a per-class look during eval.

## New proposal stage: `scripts/run_owlv2_proposals.py`

Drop-in for the `proposals` stage — same output JSON schema as `run_sam_proposals.py`, so
`lifting.load_proposal_records` and the `clip`/`dinov2` feature stages consume it unchanged.

- OWLv2 → boxes + labels + scores, threshold + per-class NMS.
- Carries the detector label in **`label_hint`**, which `lifting.lift_proposal_record` maps to
  `ObjectNode.label`. So the real open-vocab label flows through with **no CLIP-text labeling
  step**. Also stores `owlv2_label` / `owlv2_score` for downstream node-level label voting.
- Optional **`--sam-checkpoint`**: box-prompted SAM (`vit_b`, already in `models/`) turns each
  detection box into a clean instance mask (`mask_rle`), so lifting selects only object pixels.
  Verified that masks are tighter than their boxes (e.g. a full-frame "desk" box → mask is ~20%
  of it: background dropped). Without a checkpoint, lifting falls back to the bbox rectangle.

Validated end-to-end on `freiburg1_desk`: 94 proposals (box-only) / 16 on a 2-frame SAM run;
records parse via `load_proposal_records`; `label_hint` populated; masks decode and are tighter
than boxes.

## Week 2 plan — pipeline integration

1. Wire `run_owlv2_proposals.py` into `run_benchmark.py` as the proposals backend (replace the
   SAM-auto call; keep the `clip`/`dinov2` feature stages — they now crop **real object boxes**,
   so the embeddings are sound; the old failure was CLIP *labeling* of fragments, not embeddings).
2. Replace the `labels` stage (`assign_open_vocab_labels.py`, CLIP-text similarity) with
   **OWLv2-label aggregation per fused node**: score-weighted majority vote over each fused
   node's constituent proposals' `owlv2_label`s. (`label_hint` already seeds per-proposal labels;
   need the node-level vote because fusion merges proposals that may disagree. Check how
   `graph_builder.fuse_object_nodes` currently sets the fused label.)
3. Re-run the desk scene (geometry cached) → real objects end-to-end.
4. **Week 3:** build the independent GT for all 5 scenes (now meaningful) and re-run the
   variant comparison on real objects — does uncertainty fusion actually help?
