# Phase 1 re-evaluated on an INDEPENDENT reference — uncertainty fusion does not help

**This supersedes the positive sparse-view read in [`phase1_results.md`](phase1_results.md).** That
result was measured against a *circular* pseudo-reference (seeded from the 10-view graph-fusion
prediction, so graph-fusion scored 1.0 at v10 by construction). Week 2 replaced the broken
SAM-auto + CLIP front-end with the OWLv2 detector (real open-vocab objects), and Week 3 built an
**independent** reference and re-ran the full variant comparison. On real objects against a fair
reference, the headline flips.

## Headline

**The rank-normalized uncertainty-aware fusion (`proposed`) provides no benefit over the
no-uncertainty baseline (`graph-fusion`) or the uninformed control (`fixed-shrink`) — it is
slightly worse at every view count, and no uncertainty weight in [0.1, 0.8] rescues it.** The
Phase-1 "sparse-view win" was an artifact of the circular reference.

**Positive result (the replacement contribution): a post-fusion duplicate-instance merge
(`graph-fusion-dedup`) beats `graph-fusion` at every view count by +0.06 → +0.14, winning in
every scene (no losses), with the gain growing at dense views.** It targets the system's true
weakness (over-counting, see `owlv2_system_characterization.md`) — the opposite direction from
the uncertainty gate. See "Positive result" below.

## Setup

- **Front-end:** OWLv2 (`google/owlv2-base-patch16-ensemble`), box-prompted SAM masks, score
  threshold 0.2, per-class NMS 0.5. Real open-vocab objects (Week 2).
- **Reference:** independent per-scene object multiset for all 5 paper-subset scenes, enumerated by
  two independent passes (draft + adversarial verify) over the raw RGB frames — independent of
  SAM/CLIP/VGGT/graph-fusion — and then **human-verified (2026-06-30)**.
  `configs/evaluation/independent_labels.json` (`label_source: vlm-drafted-human-verified`);
  provenance + corrections in `docs/independent_reference_worklist.md`. Human verification removed
  ambiguous detections (window in room/desk/desk2; cup/bottle/picture in desk2; door/trash can in
  fr3); all numbers below are on the verified reference. Both findings were unchanged by verification.
- **Metric:** `object_label_f1` = multiset precision/recall/F1 of fused-node labels vs the reference
  multiset, mean over the 5 scenes. Driver: `scripts/run_owlv2_benchmark.sh`; eval:
  `scripts/evaluate_sparse_view_annotations.py`; aggregation: `scripts/aggregate_variant_f1.py`.
  Raw: `results/benchmark_owlv2/variant_independent_metrics.csv`.

## object_label_f1 on the independent reference (mean over 5 scenes)

| variant | v3 | v5 | v8 | v10 |
|---|---|---|---|---|
| 2d-only | 0.4897 | 0.4940 | 0.4820 | 0.4647 |
| geometry-only | 0.4578 | 0.4843 | 0.4834 | 0.4833 |
| semantic-lifting | 0.4168 | 0.3326 | 0.2548 | 0.2148 |
| fixed-shrink (control) | 0.5165 | 0.4849 | 0.4471 | 0.4008 |
| graph-fusion (baseline) | 0.5126 | 0.5038 | 0.4688 | 0.4324 |
| proposed (rank, w=0.3) | 0.4982 | 0.4725 | 0.4132 | 0.3749 |
| **graph-fusion-dedup (ours)** | **0.5804** | **0.5923** | **0.6137** | **0.5787** |

`proposed − fixed-shrink`: −0.018 (v3), −0.012 (v5), −0.034 (v8), −0.026 (v10).
`proposed − graph-fusion`: −0.014 (v3), −0.031 (v5), −0.056 (v8), −0.057 (v10).
Per-scene: `proposed` < `graph-fusion` in **3/5 at v3 and 5/5 at v5, v8, v10**. The sign of the
Phase-1 result (proposed > controls, 5/5 at v3/v5) is reversed.

## Why the Phase-1 win was an artifact

The Phase-1 reference was prediction-seeded from the 10-view graph-fusion output, so it *encoded
graph-fusion's own splitting pattern*. `proposed` keeps more uncertain proposals unmerged → splits
more → produced more of the same fragments the circular reference contained → looked better. An
independent reference fixes the true object count, so over-splitting is correctly penalized, and the
apparent gain disappears.

## Robustness — the negative result holds under every reference filtering

The reference includes `unknown object` (which OWLv2 never predicts) and "stuff" (wall/floor/
ceiling). Removing them raises every variant's F1 but does **not** change the ranking:

| reference filtering | proposed − graph-fusion (v3 / v5 / v8 / v10) |
|---|---|
| full | −0.013 / −0.029 / −0.058 / −0.061 |
| drop `unknown object` | −0.023 / −0.052 / −0.078 / −0.082 |
| objects-only (drop unknown + wall/floor/ceiling) | −0.019 / −0.041 / −0.058 / −0.058 |

## Weight sweep — no setting rescues it

`proposed` (rank) swept over uncertainty weight ∈ {0.1, 0.2, 0.3, 0.5, 0.8} (dropping `unknown
object`), vs the baseline `graph-fusion = 0.594 / 0.594 / 0.556 / 0.515`:

| weight | v3 | v5 | v8 | v10 |
|---|---|---|---|---|
| 0.1 | 0.5647 | 0.5308 | 0.4760 | 0.4274 |
| 0.2 | 0.5713 | 0.5394 | 0.4757 | 0.4244 |
| 0.3 | 0.5713 | 0.5417 | 0.4780 | 0.4335 |
| 0.5 | 0.5762 | 0.5236 | 0.4590 | 0.4069 |
| 0.8 | 0.5656 | 0.5050 | 0.4298 | 0.3860 |

Best `proposed` at each view still loses to `graph-fusion`: −0.018 (v3), −0.052 (v5), −0.078 (v8),
−0.082 (v10). Larger weights are worse at dense views. Raw: `results/benchmark_owlv2/uncertainty_weight_sweep.txt`.

## Positive result — duplicate-instance merge (`graph-fusion-dedup`)

The per-class characterization (`owlv2_system_characterization.md`) showed the system's only real
weakness is **over-counting**: the same physical object survives as several fused nodes (desk 9×,
monitor 10× at v10) because OWLv2 over-detects and same-view detections can never form a fusion edge.
`graph-fusion-dedup` adds one post-fusion step: union same-label fused nodes whose axis-aligned 3D
boxes have IoU > 0.1 and re-fuse each group (`merge_duplicate_instances` in `graph_builder.py`).

| variant | v3 | v5 | v8 | v10 |
|---|---|---|---|---|
| graph-fusion | 0.5126 | 0.5038 | 0.4688 | 0.4324 |
| **graph-fusion-dedup** | **0.5804** | **0.5923** | **0.6137** | **0.5787** |
| Δ vs graph-fusion | +0.068 | +0.089 | +0.145 | +0.146 |

- **Wins in every scene, never loses:** 4W/0L/1T (v3), 4W/0L/1T (v5), **5W/0L (v8, v10)**; same
  story vs `fixed-shrink` (+0.06 → +0.18). (n=5 → sign-test floor p=0.062.)
- **The gain grows with views** (+0.06 at v3 → +0.14 at v8/v10), and dedup is the **only** variant
  whose F1 rises rather than falls with more views — it removes the duplicate detections that
  accumulate as views are added. Precision is restored (desk v10 multiset: monitor 10→4, desk 9→1).
- Recall is essentially preserved for almost every class; precision jumps on the over-counted classes
  (monitor 0.38→1.00, desk 0.19→0.83, keyboard 0.31→0.62 at v8). The win is robust across IoU ∈ [0, 0.2]
  and under all 3 reference filterings; 3D-box IoU alone beats adding a centroid term. The one honest
  cost: closely-packed same-class instances (2–3 monitors on a desk) over-merge (monitor recall −0.33,
  desk −0.17). Full sweep + per-class table + limitation: **`docs/dedup_ablation.md`**.
- This is the **opposite axis** from the uncertainty gate (which *tightened* merging → more splitting
  → worse precision), which is why uncertainty failed and dedup succeeds. It is a clean candidate for
  the paper's positive method contribution.

## Mechanism (why, precisely)

The uncertainty modulation does exactly what it was designed to — it **lifts recall** by not
over-merging uncertain proposals (`proposed` recall 0.475/0.541/0.632/0.637 vs graph-fusion
0.466/0.494/0.594/0.590). But the same behavior **costs more precision** by fragmenting correct
objects (`proposed` precision 0.531/0.438/0.336/0.295 vs 0.587/0.563/0.443/0.405). On a fixed-count
reference the precision loss outweighs the recall gain → net F1 is lower. The signal is not noise
(recall genuinely improves), but as a *merge-gate modulation* it splits indiscriminately rather than
only where splitting is correct.

## Implications

1. **The uncertainty-aware fusion is not a defensible paper contribution as formulated.** Honest
   options: report it as a negative result / ablation, or redirect the novelty.
2. **The OWLv2 migration is the real win.** The system now produces genuine open-vocabulary 3D
   objects, and the eval is de-circularized — a sound footing the circular version never had. The
   paper can stand on the open-vocab sparse-view 3D scene-graph system + a fair benchmark.
3. **`graph-fusion` is the strongest fusion variant** on real labels at every view count; F1 falls
   with more views for all fusion variants (more proposals → more over-detection → precision drops
   against a fixed reference) — the opposite of the circular reference's monotone rise.
4. **If uncertainty is pursued further**, the recall gain hints it should *select/prune* nodes or
   weight *label confidence*, not just tighten the merge gate (which only adds fragments).

## Caveats

- **The independent reference is human-verified (2026-06-30).** It began as a two-pass VLM draft and
  was then corrected by a human against the frames (removing ambiguous detections). Re-running both
  analyses on the verified reference left every conclusion unchanged (proposed − graph-fusion moved
  −0.013/−0.029/−0.058/−0.061 → −0.014/−0.031/−0.056/−0.057; dedup − graph-fusion +0.063/.../+0.142 →
  +0.068/.../+0.146). The top former reviewer risk (circular / unverified GT) is closed.
- **n = 5 scenes.** Consistent (5/5 at v5–v10) but small — the ~30-scene expansion is the remaining
  statistical-power step.
- Reference is a scene-level multiset over the 10 frames; sparse-view predictions are recall-limited
  by construction — fair across variants, but absolute F1 is depressed.
