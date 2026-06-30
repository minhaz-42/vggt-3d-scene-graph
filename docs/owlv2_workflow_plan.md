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
| 2 | Integrate into the pipeline (replace proposal + labeling stages), re-run (geometry cached), get real objects. | ✅ **Done** |
| 3 | Build independent GT for all 5 scenes (now meaningful) → re-run the variant comparison on real objects: does uncertainty fusion actually help? | ✅ **Done — NO** |
| 4–5 | Scene expansion (~30-scene run, statistical power) + ablations. | ⬜ Next (see Week-3 finding) |
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

## Week 2 — pipeline integration ✅

- [x] Read `graph_builder.fuse_object_nodes`: the fused label is a **plain count majority vote** over
      each cluster node's `.label`, and `lifting.lift_proposal_record` already maps `label_hint` →
      `ObjectNode.label`. So OWLv2 labels flow through fusion with no code change; the new labels
      stage just refines the vote to be score-weighted.
- [x] Wire `run_owlv2_proposals.py` into `run_benchmark.py` via `--proposal-backend {owlv2,sam}`
      (default **owlv2**) + knobs `--owlv2-model/-threshold/-nms-iou/-max-detections/-device` and
      `--proposal-local-files-only`. Optional masks reuse the existing `--sam-checkpoint`. Proposal/
      feature filenames are **backend-namespaced** (`owlv2_*.json`) so OWLv2 never clobbers the
      legacy SAM cache. `--label-vocab` is now required for the owlv2 backend (supplies queries).
- [x] Kept `clip`/`dinov2` feature stages — they now crop real OWLv2 boxes (the original `owlv2_label`/
      `owlv2_score` fields are preserved through `extract_proposal_features.py`).
- [x] Replaced the `labels` stage: new **`scripts/assign_detector_labels.py`** does a score-weighted
      majority vote over each fused node's constituent `owlv2_label`s (ties broken by vote count).
      Output schema matches `assign_open_vocab_labels.py` so figure + eval consume
      `scene_graph_labeled.json` unchanged. `run_benchmark.py` dispatches to it for the owlv2 backend.
- [x] Re-ran `freiburg1_desk` end-to-end on cached geometry (`results/owlv2_smoke/`). **Real objects:**
      - **v3:** 20 proposals → 12 fused → `keyboard:1, monitor:2, desk:6, book:2, floor:1`
      - **v5:** 39 proposals → 16 fused → `keyboard:2, monitor:4, desk:5, book:1, floor:1, lamp:1, wall:1, cup:1`
      vs the old SAM+CLIP soup (`floor:54, curtain:13, bed:6`). The 2 monitors + keyboard + books are
      correctly recovered; v5 adds lamp/cup.
- [x] Verified per-frame over-detection collapses in 3D fusion (v3: 20→12, v5: 39→16). The keyboard
      detected in all 3 v3 frames fuses to a **single** node (`num_views=3`).
- **Decision made:** default to **SAM box-prompted masks** (`--sam-checkpoint` passed) — used for the
      desk re-run; cleaner 3D nodes, runs fine on MPS.

### Week-2 observations (feed into Week 3 tuning, not blockers)
- The **desk surface over-splits** (6 nodes at v3, 5 at v5) — a large planar "stuff" surface fragments
  across views. All fragments are now correctly labeled `desk` (not bed/curtain). Whether to keep
  wall/floor/desk "stuff" as nodes or filter them for the object-F1 metric is the open Week-3 decision.
- **monitor/keyboard over-split at v5** (monitor→4, keyboard→2): more views = more boxes that don't
  always fuse. This is exactly the regime the uncertainty/`proposed` variant targets — revisit once the
  variant comparison runs on real labels.
- **book recall is low** (1–2 nodes) as flagged in Week 1; may want a per-class lower threshold.

## Week 3 — independent GT + variant re-eval ✅ (finding: uncertainty does NOT help)

- [x] Extended `configs/evaluation/independent_labels.json` to all 5 scenes. Object multisets drafted
      + **adversarially verified** by two independent passes over the raw RGB frames (workflow
      `independent-reference-draft`). Provenance + corrections: `docs/independent_reference_worklist.md`.
      Now `vlm-drafted-human-verified` (human pass 2026-06-30).
- [x] Built packets via `scripts/build_independent_reference.py` → `results/benchmark_owlv2/annotations/`.
- [x] Ran the full OWLv2 benchmark — 5 scenes × {3,5,8,10} views × 6 variants — on cached geometry
      (`scripts/run_owlv2_benchmark.sh` → `results/benchmark_owlv2/`).
- [x] Re-ran the variant comparison on real objects vs the independent reference
      (`scripts/aggregate_variant_f1.py`).
- [x] **Answer: NO.** `proposed` (rank, w=0.3) is slightly *worse* than both `graph-fusion` and
      `fixed-shrink` at every view count (proposed − graph-fusion: −0.013/−0.029/−0.058/−0.061 at
      v3/v5/v8/v10; 5/5 scene losses at v5–v10). The Phase-1 sparse-view "win" was a **circular-reference
      artifact**. Holds under 3 reference filterings and across a weight sweep (0.1–0.8 — none rescue it).
      Mechanism: uncertainty modulation lifts recall but over-splits → larger precision loss. Full
      write-up: **`docs/phase1_results_independent.md`** (supersedes `phase1_results.md`).

### Week-3 implications → DECISION (2026-06-30)
- **Direction chosen: reframe the contribution around the OWLv2 open-vocab sparse-view 3D scene-graph
  system + the de-circularized benchmark.** Uncertainty-aware fusion is reported as an honest negative
  ablation (it lifts recall but over-splits → no net F1 gain on real labels, at any weight).
- **POSITIVE method contribution found: `graph-fusion-dedup`.** A post-fusion duplicate-instance merge
  (same-label nodes with 3D-box IoU > 0.1) beats `graph-fusion` at every view count by +0.06 → +0.14,
  winning in every scene (5W/0L at v8/v10), gain growing at dense views, F1 rising not falling with
  views. Targets the measured over-counting weakness — the opposite axis from the (failed) uncertainty
  gate. Wired as a variant in `graph_builder.py`/`run_pipeline.py`/`run_benchmark.py`. Numbers in
  `phase1_results_independent.md`; the system weakness it fixes is in `owlv2_system_characterization.md`.
- **Reference human-verified (2026-06-30) ✅.** Done via the contact-sheet verification page; human
  removed ambiguous detections (window in room/desk/desk2; cup/bottle/picture in desk2; door/trash can
  in fr3). Re-ran the full eval on the verified GT: **both findings unchanged** — uncertainty still
  loses (proposed − graph-fusion −0.014/−0.031/−0.056/−0.057), dedup still wins (+0.068/+0.089/+0.145/
  +0.146, 4–5W/0L every view). The circular/unverified-GT reviewer risk is now closed.
- If uncertainty is ever revisited: make it *prune/select* nodes or weight label confidence, not
  tighten the merge gate.

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
- ~~Independent GT must be human-verified~~ — **DONE (2026-06-30)**; findings unchanged. The
  remaining GT risk is scale (n=5) → the ~30-scene expansion.
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
