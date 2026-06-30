# Open-vocabulary front-end fix: SAM-auto-mask + CLIP → OWLv2 detector

**Status:** Week 3 (independent re-eval) — **complete.** OWLv2 runs end-to-end on real objects
(Week 2), and the variant comparison was re-run on an independent reference. **Key finding: the
uncertainty-aware fusion does NOT help on real labels** — the Phase-1 win was a circular-reference
artifact. Full write-up: `docs/phase1_results_independent.md`. Tracker: `docs/owlv2_workflow_plan.md`.

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

## Week 2 — pipeline integration (done)

1. **Proposals backend.** `run_benchmark.py` now takes `--proposal-backend {owlv2,sam}` (default
   `owlv2`) and dispatches to `run_owlv2_proposals.py`. Knobs: `--owlv2-model/-threshold/-nms-iou/
   -max-detections/-device`, `--proposal-local-files-only`; optional box-prompted SAM masks reuse
   the existing `--sam-checkpoint`. `--label-vocab` is required (it supplies the text queries).
   Proposal/feature files are backend-namespaced (`owlv2_proposals.json`,
   `owlv2_clip_dinov2_features.json`, …) so an OWLv2 run never clobbers the legacy SAM cache.
2. **Feature stages kept.** `clip`/`dinov2` now crop the real OWLv2 boxes; `extract_proposal_features.py`
   preserves the per-proposal `owlv2_label`/`owlv2_score` fields, so the label survives to the vote.
3. **Labeling replaced.** New `scripts/assign_detector_labels.py` sets each fused node's label by a
   **score-weighted majority vote** over its constituent proposals' `owlv2_label`s (ties broken by
   count). It writes the same `scene_graph_labeled.json` schema as the old CLIP-text labeler, so the
   figure + eval are unchanged. (Note: `fuse_object_nodes` already does a plain count vote over the
   `label_hint`-derived labels during fusion; the new stage refines that to score-weighted.)
4. **Desk re-run (cached geometry, `results/owlv2_smoke/`).** Real objects end-to-end:
   | views | proposals | fused | labels |
   |---|---|---|---|
   | v3 | 20 | 12 | keyboard:1, monitor:2, desk:6, book:2, floor:1 |
   | v5 | 39 | 16 | keyboard:2, monitor:4, desk:5, book:1, floor:1, lamp:1, wall:1, cup:1 |
   Over-detection collapses in 3D fusion (v3 20→12, v5 39→16); the v3 keyboard fuses across all 3
   frames into one node. Compare the old `floor:54, curtain:13, bed:6` soup — none of the real objects.

## Week 3 — independent re-eval (done)

Built an independent 5-scene reference (draft + adversarial verify over raw frames, then
**human-verified 2026-06-30**), ran the full OWLv2 benchmark (5 scenes × {3,5,8,10} × 6 variants),
and re-ran the variant comparison on real objects. **The rank-normalized uncertainty fusion does NOT beat the
no-uncertainty baseline or the control** — slightly worse at every view count, 5/5 scene losses at
v5–v10, robust under 3 reference filterings and a weight sweep (0.1–0.8). The Phase-1 sparse-view
"win" was a circular-reference artifact. The real win is the OWLv2 open-vocab system + the
de-circularized benchmark. Full write-up + tables: `docs/phase1_results_independent.md`.
