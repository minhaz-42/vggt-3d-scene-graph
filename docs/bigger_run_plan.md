# Bigger Run Plan

Plan for scaling the benchmark beyond the current 5-scene / 50-frame TUM RGB-D paper
subset. Two phases, sequenced by cost and dependency:

- **Phase 1 — Baseline ablations.** Code first, then cheap compute on the *existing*
  5 scenes by reusing cached features. Hits the top reviewer risk ("baselines discussed
  but not run", `docs/cviu_submission_checklist.md`).
- **Phase 2 — Scene expansion.** Acquire ~25 more sequences, run the full 3/5/8/10
  protocol on a **GPU** (Colab/Kaggle/cloud), regenerate all tables/figures.

Status when this plan was written: nothing scaffolded. No `data/benchmark/scenes/`, no
baseline/variant code anywhere in `src/` or `scripts/`, memory store empty.

---

## Critical finding: the "Proposed" variant is not what runs today

The experiment-plan variant table (`docs/experiment_plan.md:74-80`) lists the proposed
method as VGGT geometry + 2D semantics + **uncertainty** + graph fusion + relations. But
the wired pipeline does **not** use uncertainty in the fusion decision:

- `scripts/run_pipeline.py:93` calls `fuse_object_nodes(...)`.
- `fuse_object_nodes` → `build_geometry_fusion_graph` (`src/vggt_scene_graph/graph_builder.py:68-102`)
  fuses on **centroid distance ≤ threshold** plus an optional **feature-similarity gate**
  (`--fusion-feature-threshold 0.75`). Uncertainty never enters.
- `merge_score` + `build_candidate_graph` (`graph_builder.py:32-61`) — the only code that
  combines semantic + geometry + **uncertainty** — is **dead code**, not called anywhere.
- Uncertainty *is* computed per node (`src/vggt_scene_graph/lifting.py:192-194`:
  `0.7*conf + 0.3*compactness`) and only used to down-scale the fused node's uncertainty
  value (`graph_builder.py:140-142`). It does not influence which nodes merge.

**Implication:** what runs today is the "Graph fusion (no uncertainty)" row, not the
"Proposed" row. For the uncertainty ablation to be meaningful (Hypothesis 2 in the
experiment plan), uncertainty must be wired into the fusion decision. This is the single
most important design choice in Phase 1.

**Decision (locked, 2026-06-23):** wire uncertainty into the fusion gate (user chose this
over leaving it as-is, accepting that the "Proposed" numbers will shift from the current
manuscript). The mechanism — chosen via a design panel of 5 proposals + adversarial judging
— is an **uncertainty-modulated conservative fusion gate**: shrink the effective distance
threshold and raise the feature-similarity bar in proportion to joint pair uncertainty, plus
an anti-bridge veto, with `use_uncertainty=False` as the exact reproduction anchor for the
`graph-fusion` baseline. Full implementation spec: `docs/phase1_uncertainty_fusion_spec.md`.

---

## Reuse lever: `--stages`

`scripts/run_benchmark.py:19-24` already exposes
`--stages {geometry,proposals,clip,dinov2,graph,labels,figure}`. The expensive stages
(VGGT geometry, SAM, CLIP, DINOv2) are cached per scene/view-count under
`results/benchmark_tum_rgbd_paper_subset/<scene>/views_NN/`. Baselines only change the
**graph** stage, so each variant run is:

```bash
--stages graph labels figure --skip-existing
```

i.e. seconds-to-minutes per run, not the ~3.5 min/run that includes geometry. No GPU
needed for Phase 1.

---

## Phase 1 — Baseline ablations

### Variant definitions (mapped to concrete code behavior)

| Variant | Geometry | 2D semantics | Uncertainty | Graph fusion | Fusion behavior | Code status |
| --- | --- | --- | --- | --- | --- | --- |
| `2d-only` | No | Yes | No | feature-only | merge by feature cosine, ignore centroid distance | **new fusion mode** |
| `geometry-only` | Yes | No | No | distance-only | merge by centroid distance, no feature gate | **trivial** — pass `feature_similarity_threshold=None` |
| `semantic-lifting` | Yes | Yes | No | none | no cross-view fusion; each lifted candidate stays a node | **new** — skip `fuse_object_nodes` |
| `graph-fusion` | Yes | Yes | No | geometry+feature | current wired pipeline | **already implemented** (this is today's default) |
| `proposed` | Yes | Yes | Yes | geometry+feature+uncertainty | as `graph-fusion` + uncertainty term in merge gate | **new** — wire uncertainty into fusion |

So three of five variants need code: `2d-only`, `semantic-lifting`, `proposed`.
`geometry-only` is a one-line argument. `graph-fusion` already exists.

### Implementation steps

1. **`src/vggt_scene_graph/graph_builder.py`** — add a single fusion entry point that
   takes a `variant` (or explicit `use_geometry / use_semantics / use_fusion /
   use_uncertainty` booleans):
   - `2d-only`: build edges from feature cosine ≥ threshold, no distance constraint.
   - `geometry-only`: current distance path with `feature_similarity_threshold=None`.
   - `semantic-lifting`: return candidate nodes unfused (one fused node per candidate).
   - `graph-fusion`: current behavior.
   - `proposed`: extend the merge gate so high joint uncertainty raises the effective
     distance/feature bar (e.g. require tighter distance or higher feature-sim when
     `(u_left+u_right)/2` is high). Reuse the existing `merge_score` formulation rather
     than inventing a new one.
   - Keep all current defaults so `graph-fusion` reproduces today's numbers exactly
     (regression guard: re-run one scene and diff against the existing
     `scene_graph.json`).

2. **`scripts/run_pipeline.py`** — add `--variant` (default `graph-fusion` =
   backward-compatible) and thread it into the new fusion entry point. Record the variant
   in the output `pipeline` block (`run_pipeline.py:107`).

3. **`scripts/run_benchmark.py`** — add `--variant`, write per-variant output dirs
   (e.g. `results/baselines/<variant>/<scene>/views_NN/`), and pass `--variant` to the
   `graph` stage command (`run_benchmark.py:215-235`). Geometry/proposals/feature stages
   should **symlink or skip-existing against** the existing paper-subset cache so they are
   not recomputed.

4. **Evaluation + tables** — for each variant run:
   - `scripts/summarize_scene_graph.py` → structural stats per variant.
   - `scripts/evaluate_scene_graph.py` → proxy + (where applicable) checked metrics.
   - New/extended export: a comparison table with rows = variant, columns = view-count,
     cells = object/relation F1 (and structural counts). Extend
     `scripts/export_sparse_view_tables.py` with a `--variant-column`, or add a small
     `scripts/export_baseline_comparison.py`.
   - Caveat to handle: checked annotations exist only for the `proposed`/current 10-view
     graphs and key on node ids that differ across variants. Cross-variant comparison is
     cleanest on **structural** + **pseudo-reference-vs-10-view** metrics; checked-F1
     stays a `proposed`-only number unless we re-map node identities.

### Phase 1 estimated effort

- Code: ~0.5–1 day (graph_builder fusion modes + arg threading + comparison export).
- Compute: minutes total (5 scenes × 4 views × 5 variants = 100 graph-stage runs on
  cached features).
- Risk: low. All reversible; cached features untouched; `graph-fusion` is a regression
  anchor.

---

## Phase 2 — Scene expansion (GPU)

Decision already made: run the heavy expansion on a GPU (Colab/Kaggle/cloud), not the Mac
(MPS unavailable per `docs/mac_feasibility.md:63`; ~120 CPU runs ≈ 4–6 h).

### Prep deliverables (done locally, no GPU)

1. **Scene acquisition list** — `scripts/download_tum_rgbd_subset.py --discover` to list
   mirror sequences; pick ~25 more to reach ~30 scenes. Keep 10 frames/scene, stride 10
   (match current subset for protocol consistency).
2. **Manifest** — `scripts/build_dataset_manifest.py --dataset-root data/benchmark/scenes
   --images-subdir images --max-scenes 30 --max-images-per-scene 10 --output
   configs/datasets/benchmark_subset.json`.
3. **GPU run package** — a self-contained script/notebook that:
   - clones/syncs the repo + `.venv` requirements,
   - downloads SAM checkpoint + caches CLIP/DINOv2/VGGT weights,
   - runs `run_benchmark.py --geometry-device cuda --feature-device cuda --view-counts
     3 5 8 10 --skip-existing` (and, if Phase 1 landed, loops `--variant` over all five),
   - tars `results/` back for download.
4. **`--dry-run` first** to emit the index and verify planned commands before burning GPU
   time.

### Post-run (back on Mac)

Regenerate everything via the existing rebuild commands in
`docs/dataset_protocol.md:136-195`: summary CSV → proxy/pseudo-reference metrics → LaTeX/MD
tables → diagrams → qualitative figure. Update `docs/paper_ready_status.md` and the
results table in `docs/dataset_protocol.md`.

### Phase 2 estimated effort

- Local prep: ~0.5 day.
- GPU compute: ~30 scenes × 4 views (× up to 5 variants if combined with Phase 1) — order
  of 1–3 h on a single modern GPU vs 4–6 h CPU for the proposed-only sweep.

---

## Phase 1 implementation status (2026-06-23)

Phase 1 is **implemented and locally verified** (branch `phase1-uncertainty-fusion`):

- `graph_builder.py`: uncertainty-modulated gate + bridge veto + 6-way `variant` dispatch,
  monotonicity guards, feature-cap fix. `proposed` forces `use_uncertainty=True`.
- `run_pipeline.py` / `run_benchmark.py`: `--variant` + uncertainty knobs; variants reuse the
  shared upstream feature cache and write graphs to `results/.../variants/<variant>/` (the
  default `graph-fusion` keeps the legacy path, so existing baseline tables/globs are
  unaffected — this supersedes the spec §6.C literal `output_root/<variant>/` template).
- `evaluate_sparse_view_annotations.py`: `--variant` (repeatable) + per-variant path routing
  + an anti-fabrication guard (refuses to score a graph whose stamped variant disagrees).
- New `scripts/export_variant_comparison.py` + committed `variant_structural_comparison.{md,csv}`.

Verified by execution: `graph-fusion` reproduces prior output byte-for-byte (8/8);
`--variant proposed` alone now engages uncertainty (81→86 objects); guard + validation fire.

An adversarial review (12 confirmed findings) drove these fixes. **Structural result:**
`proposed` conservatively splits a few % more than baseline (less over-merging) but the
effect is modest (node uncertainties ~0.04), and the `fixed-shrink` control splits more — so
the *informativeness* of uncertainty needs the **labeled object-F1 eval** (CLIP labelling +
checked annotations), which is exactly what the Colab run produces.

**Deferred (follow-on):** a dose-response sweep *driver* over `uncertainty_weight ∈
{0,0.25,0.5,0.75,1.0}`. The knobs are wired, but a clean weight=0 anchor requires also zeroing
`feature_uncertainty_weight` and disabling the veto at that point (spec §4) — not yet scripted.

## Open questions for the user

1. ~~Uncertainty-in-fusion~~ **RESOLVED (2026-06-23):** wire it in. Mechanism + code spec
   locked in `docs/phase1_uncertainty_fusion_spec.md`.
2. **Which extra sequences** for Phase 2 (any TUM scene preferences, or just take the next
   ~25 by the discover list?). The Colab notebook (`notebooks/bigger_run_colab.ipynb`)
   defaults to the 5 paper-subset scenes and expands by editing one `SEQUENCES` list.
3. **Combine Phase 1 variants into the Phase 2 GPU sweep**, or keep Phase 2 proposed-only
   to control cost?

## Colab / GPU execution

Phase 2 runs on a Colab GPU. See `docs/colab_run.md` and `notebooks/bigger_run_colab.ipynb`:
clone repo → install (keep Colab's CUDA torch, add VGGT + SAM) → download SAM checkpoint →
deterministic TUM download (regenerates the manifest with Colab paths) → `run_benchmark.py
--geometry-device cuda --feature-device cuda` → rebuild tables → download results bundle.
The notebook runs the current pipeline today; once Phase 1 lands, add a `--variant` loop.
