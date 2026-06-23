# Phase 1 Results — Uncertainty-Aware Fusion (GPU run, 5-scene subset)

Labeled object/relation F1 vs the 10-view pseudo-reference annotation, mean over the 5 TUM
RGB-D paper-subset scenes. Generated on Colab GPU by `notebooks/bigger_run_colab.ipynb`
(`scripts/evaluate_sparse_view_annotations.py` → `variant_checked_metrics.csv`, 120 rows).

## object_label_f1

| variant | v3 | v5 | v8 | v10 |
|---|---|---|---|---|
| 2d-only | 0.4584 | 0.4914 | 0.5386 | 0.5869 |
| geometry-only | 0.4399 | 0.5112 | 0.6062 | 0.6165 |
| semantic-lifting | 0.7715 | 0.7592 | 0.6626 | 0.5785 |
| fixed-shrink (control) | 0.6340 | 0.7790 | 0.9221 | 0.9500 |
| graph-fusion (baseline) | 0.6222 | 0.7509 | 0.9141 | 1.0000 |
| proposed | 0.6317 | 0.7587 | 0.9184 | 0.9752 |

(precision/recall and relation_triplet_f1 in `variant_checked_metrics.csv`.)

## Honest interpretation

**The uncertainty signal is not demonstrably informative.** `proposed` beats `graph-fusion`
at sparse views only marginally (+0.010/+0.008/+0.004 at v3/v5/v8), and the **`fixed-shrink`
control — uniform threshold tightening with zero uncertainty information — beats `proposed`
at v3/v5/v8**. Same in `relation_triplet_f1`. So the small gains over baseline come from
tightening the merge gate, NOT from uncertainty being informative. Hypothesis 2 is **not
supported** as currently operationalized. (The control was added precisely to test this; it
fired.)

**The v10 column is a measurement artifact.** The checked annotation is prediction-seeded
from the 10-view `graph-fusion` output, so `graph-fusion` scores 1.0000 at v10 by
construction, and any method that alters the 10-view graph (`proposed`) is penalized. The
comparison is measured against a baseline-derived reference — circular.

## Root causes (both fixable)

1. **Near-zero uncertainty range** — mean node uncertainty ~0.04 (VGGT confidence is high),
   so the modulation `1 − w·u` ≈ 0.98 barely engages; `proposed` ≈ `graph-fusion`.
2. **Circular pseudo-reference** — cannot fairly test "proposed vs baseline" when the GT is
   the baseline's own prediction.

## Next steps before any uncertainty claim

1. Recalibrate uncertainty for real dynamic range (per-scene normalization), or use a
   higher-variance signal (cross-view feature disagreement, multi-view support count).
2. Replace/augment the circular pseudo-reference with independent GT (small hand-labeled set,
   or TUM depth-based geometric IoU) — also the CVIU reviewer risk already flagged.
3. If the effect still doesn't separate from `fixed-shrink`, report a careful **null result**.

## Notes

- `2d-only` / `geometry-only`: high precision, very low recall (over-merge → few objects).
- `semantic-lifting`: no fusion → high recall early, precision collapses with more views
  (0.4289 at v10); strong at v3 (0.7715) but degenerate.
