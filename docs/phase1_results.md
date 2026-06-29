# Phase 1 Results — Uncertainty-Aware Fusion (GPU runs, 5-scene subset)

> ⚠️ **SUPERSEDED — read [`phase1_results_independent.md`](phase1_results_independent.md) first.**
> The "sparse-view win" below was measured against a **circular** pseudo-reference (seeded from the
> 10-view graph-fusion prediction). Re-evaluated on real OWLv2 objects against an **independent**
> reference (Week 3), the win disappears: `proposed` is slightly *worse* than both `graph-fusion`
> and `fixed-shrink` at every view count, and no uncertainty weight rescues it. The numbers here are
> retained only as the record of the circular-reference artifact.

Labeled object/relation F1 vs the 10-view pseudo-reference annotation, mean over the 5 TUM
RGB-D paper-subset scenes. Numbers in `results/benchmark_tum_rgbd_paper_subset/variant_checked_metrics.csv`.

## Headline

- **Raw uncertainty → null result.** With the unnormalized signal (mean ~0.04, no dynamic
  range) the modulation barely fired: `proposed` ≈ `graph-fusion`, and the `fixed-shrink`
  control matched or beat it. No evidence uncertainty was informative.
- **Rank-normalized uncertainty → real sparse-view win.** After per-scene rank normalization
  (`--uncertainty-normalize rank`, weight 0.3, bridge-tau 0.85), `proposed` **beats both the
  baseline and the no-uncertainty control at the sparse views the paper is about**, and the
  win is consistent across scenes. At dense views it over-splits and underperforms.

## object_label_f1 (recalibrated `proposed`, rank-normalized)

| variant | v3 | v5 | v8 | v10 |
|---|---|---|---|---|
| 2d-only | 0.4584 | 0.4914 | 0.5386 | 0.5869 |
| geometry-only | 0.4399 | 0.5112 | 0.6062 | 0.6165 |
| semantic-lifting | 0.7715 | 0.7592 | 0.6626 | 0.5785 |
| fixed-shrink (control) | 0.6340 | 0.7790 | 0.9221 | 0.9500 |
| graph-fusion (baseline) | 0.6222 | 0.7509 | 0.9141 | 1.0000 |
| **proposed (rank)** | **0.6739** | **0.7997** | 0.8832 | 0.8731 |

`proposed − fixed-shrink` (object_label_f1): **+0.040 (v3), +0.021 (v5)**, −0.039 (v8), −0.077 (v10).
`proposed − graph-fusion`: +0.052 (v3), +0.049 (v5), −0.031 (v8), −0.127 (v10).

## Why this is a real (sparse-view) result, not an artifact

1. **It beats the uninformed control.** `fixed-shrink` applies the *same kind* of gate
   tightening with **zero uncertainty information**. `proposed` beats it at v3/v5, so the gain
   is attributable to the uncertainty signal being informative — not to merely tightening the
   merge gate. (This control was added on the adversarial review's insistence; it is what makes
   the claim defensible.)
2. **It is consistent across scenes.** `proposed` > `fixed-shrink` in **5/5 scenes at v3** and
   **4/5 at v5** (tied in the 5th); `proposed` > `graph-fusion` in **5/5 at both**. Not a
   single-scene fluke.
3. **The mechanism matches Hypothesis 2 + 4.** `proposed` lifts recall at every view count
   (0.538 vs 0.467 baseline at v3) by not over-merging uncertain proposals, with the largest
   F1 gain at the *fewest* views — i.e. uncertainty helps most exactly where geometry is
   weakest.

## Honest limitations

- **Dense-view over-splitting.** At v8/v10 `proposed` loses (precision drops: 0.856/0.780 vs
  baseline 0.984/1.000). With many views, merges are well-supported, so the extra splitting
  fragments correct objects. → motivates **view-count-adaptive** uncertainty weight (strong at
  sparse views, off at dense).
- **The v10 column is a circular-reference artifact.** The checked annotation is
  prediction-seeded from the 10-view `graph-fusion` output, so `graph-fusion` scores 1.0000 at
  v10 by construction and any deviating method is penalized. v8 is partly affected too. The
  v3/v5 wins are the most trustworthy (furthest from the dense reference). **Independent GT is
  still needed** to make the dense-view comparison fair (and it is the top CVIU reviewer risk).
- **n = 5 scenes.** Margins over the control are small (+0.02–0.04); the 5/5 consistency is
  encouraging (sign-test p≈0.03 at v3) but more scenes would solidify it.

## Config

`proposed` = `--variant proposed --uncertainty-normalize rank --uncertainty-weight 0.3
--feature-uncertainty-weight 0.3 --bridge-tau 0.85`. `none` reproduces the null result;
`graph-fusion` is byte-identical to the pre-Phase-1 pipeline (reproduction anchor verified 8/8).

## Next steps

1. **View-count-adaptive weight** — scale the uncertainty weight down as view count rises (or
   apply `proposed` only in the sparse regime). Cheapest path to a clean win across all views.
2. **More scenes** (the Phase 2 expansion) — statistical power for the sparse-view claim.
3. **Independent reference** — break the circular pseudo-reference (hand-labeled GT or TUM
   depth-based geometric IoU) so v8/v10 are fair and the reviewer risk is closed.
4. **Weight dose-response sweep** — characterize robustness vs `uncertainty_weight`.
