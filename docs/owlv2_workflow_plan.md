# Workflow plan — open-vocab front-end fix (SAM-auto+CLIP → OWLv2)

Living tracker for the 8-week sprint. Update the status boxes as we go. Week-1 evidence and
the detailed write-up live in [`docs/owlv2_migration.md`](owlv2_migration.md).

## Goal

Replace **only** the broken front-end — SAM automatic masks + CLIP-per-patch labeling — with a
real open-vocabulary **detector** (OWLv2). Everything downstream is reused unchanged:

- VGGT 3D lifting (`src/vggt_scene_graph/lifting.py`)
- uncertainty-aware fusion (`src/vggt_scene_graph/graph_builder.py`)
- the scene graph + relations
- the variant/control harness (`scripts/run_benchmark.py`, `scripts/run_pipeline.py`)
- the independent-eval tooling (`scripts/build_independent_reference.py`, `evaluate_*`)

This makes the "open-vocab 3D scene graph" claim actually true and de-circularizes the eval.

**Why it was broken:** SAM auto-masks on blurry low-res TUM RGB → surface/background fragments;
CLIP mislabels them as room-scale categories (floor/curtain/bed); `object_label_f1` graded CLIP
against CLIP (~1.0 at v10 by construction, ~3% vs an independent reference). See the
`critical-labeling-broken` memory.

## Schedule

| Wk | Work | Status |
|----|------|--------|
| 1 | **GO/NO-GO**: confirm a detector finds real objects → pick detector. Build new proposal stage (detector boxes + labels; optionally SAM box-prompted masks). | ✅ **Done — GO** |
| 2 | Integrate into the pipeline (replace proposal + labeling stages), re-run (geometry cached), get real objects. | ⬜ Next |
| 3 | Build independent GT for all 5 scenes (now meaningful) → re-run the variant comparison on real objects: does uncertainty fusion actually help? | ⬜ |
| 4–5 | Scene expansion (~30-scene run, statistical power) + ablations. | ⬜ |
| 6–7 | Write-up + figures + venue formatting. | ⬜ |
| 8 | Buffer → submit. | ⬜ |

Legend: ✅ done · 🟡 in progress · ⬜ not started

---

## Week 1 — GO/NO-GO + new proposal stage ✅

- [x] Confirm OWLv2 finds real objects on the desk frames (**7/7** reference objects;
      keyboard ~0.8, monitor/desk ~0.6, vs the old `floor:54/curtain:13` soup).
- [x] **Pick detector: OWLv2** (`google/owlv2-base-patch16-ensemble`). Cached, `transformers`-native
      (no custom-op compile), runs on MPS ~3.3 s/frame. GroundingDINO rejected (CUDA/C++ op compile).
- [x] Settle operating point: `threshold=0.2`, per-class NMS `iou=0.5`.
- [x] Build proposal stage: [`scripts/run_owlv2_proposals.py`](../scripts/run_owlv2_proposals.py)
      — drop-in for `run_sam_proposals.py`; label in `label_hint`; optional `--sam-checkpoint`
      for box-prompted masks.
- [x] Validate end-to-end on `freiburg1_desk` (records parse, labels populate, masks decode/are
      tighter than boxes).
- [x] Record results in `docs/owlv2_migration.md` + memory.

## Week 2 — pipeline integration ⬜

- [ ] Read `graph_builder.fuse_object_nodes` to see how the fused node's `label` is currently set
      (single proposal vs aggregate).
- [ ] Wire `run_owlv2_proposals.py` into `run_benchmark.py` proposals stage (replace the SAM-auto
      call; add an OWLv2 backend + knobs: `--threshold`, `--nms-iou`, `--owlv2-model`, masks on/off).
- [ ] Keep `clip`/`dinov2` feature stages (now crop **real object boxes** → sound embeddings; the
      old failure was CLIP *labeling* of fragments, not embeddings).
- [ ] Replace the `labels` stage (`assign_open_vocab_labels.py`, CLIP-text similarity) with
      **score-weighted majority vote over each fused node's `owlv2_label`s**.
- [ ] Re-run the desk scene (geometry cached) end-to-end → confirm real objects in the scene graph.
- [ ] Spot-check that per-frame over-detection (4–6 monitor boxes) collapses to ~2 nodes after
      3D fusion.
- **Decision needed:** default to SAM box-prompted masks (better 3D nodes, modestly slower) vs
      box-only (faster). Leaning SAM-masks.

## Week 3 — independent GT + variant re-eval ⬜

- [ ] Extend `configs/evaluation/independent_labels.json` from the desk-only pilot to all 5 scenes
      (currently `vlm-drafted-pending-human-verification`; must be human-verified before paper use).
- [ ] Build packets via `scripts/build_independent_reference.py`.
- [ ] Re-run the variant comparison (graph-fusion / proposed / fixed-shrink control / baselines) on
      **real objects** against the independent reference.
- [ ] Answer the core question: **does rank-normalized uncertainty fusion actually help** once
      labels are real (revisit the `phase1-results-null` sparse-view win, which was measured against
      wrong labels)?

## Week 4–5 — scene expansion + ablations ⬜

- [ ] Expand ~5 → ~30 TUM sequences (full 3/5/8/10 view protocol). Detection runs locally; VGGT
      geometry on GPU (Colab) per the `colab-run-package` memory.
- [ ] Ablations: detection threshold, NMS, masks vs box-only, uncertainty weight/normalize sweep.

## Week 6–7 — write-up ⬜

- [ ] Figures (qualitative scene graphs, per-class F1, sparse-view curves), tables, venue formatting.

## Week 8 — buffer → submit ⬜

---

## Key decisions log

- **2026-06-24** — Detector = **OWLv2** (decisive GO; cached + no compile + MPS-capable).
  GroundingDINO rejected (custom-op compile burden).
- **2026-06-24** — Operating point `threshold=0.2`, per-class NMS `iou=0.5`. Per-frame
  over-detection is acceptable — it collapses in 3D fusion; don't over-tighten 2D.
- **2026-06-24** — Label path: detector label via `label_hint` → `ObjectNode.label`; no
  CLIP-text labeling stage. Node-level vote to be added in Week 2.

## Open questions / risks

- Books are recall-limited (small/stacked) — may need a lower per-class threshold or it just
  caps `book` recall in the eval.
- Independent GT is still VLM-drafted / unverified — **must be human-verified** before any paper
  claim (top-reviewer risk; this is what sank the circular eval before).
- "stuff" classes (wall/floor/ceiling) are in the vocab and detectable but arguably not objects —
  decide whether to keep them as nodes or filter for the object-F1 metric.
- Does the uncertainty-fusion win survive real labels? (The whole Phase-1 result was measured
  against wrong labels.)

## Artifact index

- `scripts/run_owlv2_proposals.py` — new OWLv2 proposal stage (this sprint).
- `docs/owlv2_migration.md` — Week-1 GO/NO-GO evidence + detail.
- `docs/owlv2_workflow_plan.md` — this tracker.
- `scripts/run_sam_proposals.py` — old SAM-auto proposal stage (being replaced).
- `scripts/assign_open_vocab_labels.py` — old CLIP-text labeling (being replaced).
- `configs/label_vocab/indoor_open_vocab.json` — 30-label indoor open vocab (detector queries).
- `configs/evaluation/independent_labels.json` — independent reference (desk pilot; expand Wk3).
