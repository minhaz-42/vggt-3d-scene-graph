# `graph-fusion-dedup` ablation

Tuning + robustness for the post-fusion duplicate-instance merge (the positive contribution; see
`phase1_results_independent.md`). Metric is `object_label_f1` macro-averaged over the 5 scenes vs the
independent reference (same as the headline table). Raw: `results/benchmark_owlv2/dedup_ablation.txt`.
Baseline `graph-fusion`: 0.505 / 0.505 / 0.490 / 0.458 (v3/v5/v8/v10).

## IoU threshold sweep (the merge criterion: merge same-label nodes with 3D-box IoU > t)

| IoU t | v3 | v5 | v8 | v10 | avg Δ vs graph-fusion |
|---|---|---|---|---|---|
| 0.0 (any overlap) | 0.576 | 0.586 | 0.653 | 0.626 | **+0.121** |
| 0.05 | 0.568 | 0.582 | 0.630 | 0.608 | +0.107 |
| **0.1 (default)** | **0.568** | **0.589** | **0.635** | **0.603** | **+0.109** |
| 0.15 | 0.565 | 0.586 | 0.619 | 0.580 | +0.098 |
| 0.2 | 0.555 | 0.574 | 0.603 | 0.571 | +0.086 |
| 0.3 | 0.541 | 0.550 | 0.560 | 0.539 | +0.058 |
| 0.5 | 0.516 | 0.524 | 0.524 | 0.498 | +0.026 |

**The win is robust** across the whole low-IoU range (avgΔ +0.086 → +0.121 for t ∈ [0, 0.2]); it only
fades when the threshold gets strict enough to stop merging duplicates (t ≥ 0.5). `t = 0.1` (the wired
default) is within noise of the optimum and slightly more conservative than "any overlap" (see the
recall trade-off below), so we keep it.

## Merge-criterion ablation

Adding a centroid-distance OR-term on top of IoU does **not** help (v8: 0.653 → 0.647/0.651 for
dist < 0.1 / 0.2). **3D-box IoU alone is the right, simplest criterion.**

## Robustness across reference filterings (dedup − graph-fusion, at t=0.1-class behavior, shown at t=0)

| filtering | v3 | v5 | v8 | v10 |
|---|---|---|---|---|
| full reference | +0.070 | +0.081 | +0.163 | +0.168 |
| drop `unknown object` | +0.101 | +0.110 | +0.211 | +0.217 |
| objects-only (drop unknown + wall/floor/ceiling) | +0.106 | +0.100 | +0.199 | +0.210 |

Dedup wins under every filtering, with larger margins on the cleaner (object-only) metrics.

## Per-class mechanism (v8, micro over scenes) — precision up, recall mostly preserved

| class | baseline P/R | dedup P/R | Δrecall |
|---|---|---|---|
| monitor | 0.38/1.00 | 1.00/0.67 | −0.33 |
| desk | 0.19/1.00 | 0.83/0.83 | −0.17 |
| keyboard | 0.31/1.00 | 0.62/1.00 | 0.00 |
| wall | 0.40/1.00 | 1.00/1.00 | 0.00 |
| floor | 0.57/0.80 | 1.00/0.80 | 0.00 |
| book | 0.64/0.82 | 1.00/0.82 | 0.00 |
| chair | 0.50/0.80 | 0.80/0.80 | 0.00 |
| cup | 0.67/0.67 | 0.86/0.67 | 0.00 |
| window | 0.14/0.33 | 0.50/0.33 | 0.00 |
| plant | 0.33/1.00 | 1.00/1.00 | 0.00 |

Dedup sharply raises precision on the over-counted classes (`monitor`, `desk`, `keyboard`, `wall`,
`floor`, `book`, `window`, …) while leaving recall unchanged for almost every class.

### Honest limitation
`monitor` (−0.33 recall) and `desk` (−0.17) are the only classes that lose recall: a desk holds
2–3 monitors physically close together whose axis-aligned 3D boxes overlap, so box-IoU merges them
into one. Box geometry alone cannot separate closely-packed same-class instances. The net is still a
large F1 gain (monitor precision 0.38 → 1.00 dwarfs the recall cost), but **appearance/feature-based
instance separation** (split a merged group back apart when its members are visually distinct) is the
clear future-work hook — and exactly where the recall the uncertainty signal *could* contribute might
finally pay off, applied as a split-decision rather than a merge-gate.

## Default
`--dedup-iou 0.1`, 3D-box IoU only. Near-optimal, robust, and more recall-conservative than any-overlap.
