# OWLv2 open-vocab 3D scene-graph system — characterization

What the system actually gets right and wrong on real objects, against the independent 5-scene
reference (drop `unknown object`, which OWLv2 never predicts). Variant = `graph-fusion` (the
strongest fusion variant on real labels; see `phase1_results_independent.md`). This is the substance
of the benchmark contribution. Data: `results/benchmark_owlv2/per_class_object_accuracy.txt`.

## Overall (micro-averaged over 5 scenes, per view count)

| views | precision | recall | F1 |
|---|---|---|---|
| 3 | 0.554 | 0.614 | **0.583** |
| 5 | 0.491 | 0.651 | 0.560 |
| 8 | 0.405 | 0.795 | 0.537 |
| 10 | 0.361 | 0.795 | 0.496 |

**Signature: recall rises with views (0.61 → 0.80), precision falls (0.55 → 0.36).** The system
finds *more* of the true objects as it sees more frames, but it also emits more duplicate/fragment
detections, so precision — and net F1 — degrade. F1 is best at the sparse end. (Note this is the
opposite of the circular reference, where F1 rose to 1.0 at v10 by construction.)

## Per-class precision / recall (graph-fusion)

| class | ref | v3 P/R | v5 P/R | v8 P/R | v10 P/R |
|---|---|---|---|---|---|
| book | 11 | 1.00/0.82 | 0.67/0.73 | 0.64/0.82 | 0.53/0.73 |
| monitor | 9 | 0.55/0.67 | 0.54/0.78 | 0.38/1.00 | 0.33/1.00 |
| cup | 9 | 1.00/0.44 | 0.83/0.56 | 0.67/0.67 | 0.64/0.78 |
| bottle | 7 | 0.78/1.00 | 0.71/0.71 | 0.71/0.71 | 0.71/0.71 |
| desk | 6 | 0.25/1.00 | 0.25/1.00 | 0.19/1.00 | 0.17/1.00 |
| box | 6 | 0.40/0.33 | 0.38/0.50 | 0.46/1.00 | 0.35/1.00 |
| floor | 5 | 0.50/0.40 | 0.75/0.60 | 0.57/0.80 | 0.44/0.80 |
| chair | 5 | 1.00/0.40 | 0.67/0.40 | 0.50/0.80 | 0.44/0.80 |
| keyboard | 5 | 0.56/1.00 | 0.42/1.00 | 0.31/1.00 | 0.26/1.00 |
| wall | 4 | 1.00/0.75 | 0.57/1.00 | 0.40/1.00 | 0.36/1.00 |
| door | 4 | 1.00/0.25 | 1.00/0.25 | 0.67/0.50 | 0.67/0.50 |
| window | 3 | 0.25/0.33 | 0.20/0.33 | 0.14/0.33 | 0.14/0.33 |
| cabinet | 2 | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| bag | 2 | 1.00/0.50 | 1.00/0.50 | 1.00/0.50 | 1.00/0.50 |
| picture | 2 | 0.00/0.00 | 1.00/0.50 | 1.00/0.50 | 1.00/0.50 |
| lamp | 1 | 0.33/1.00 | 0.20/1.00 | 0.20/1.00 | 0.20/1.00 |
| plant | 1 | 0.50/1.00 | 1.00/1.00 | 0.33/1.00 | 0.50/1.00 |
| trash can | 1 | 0.00/0.00 | 0.00/0.00 | 0.50/1.00 | 0.33/1.00 |

### Three behavioral groups
- **Found reliably but over-counted** (recall → 1.0, precision collapses with views): `desk`
  (0.25 → 0.17), `keyboard` (0.56 → 0.26), `monitor` (0.55 → 0.33), `wall`, `lamp`, `box`. These are
  always detected; the 3D fusion does not collapse the multiple detections of the *same* physical
  object, so they are over-counted — the dominant precision sink.
- **Clean wins** (high precision *and* recall): `book`, `bottle`, `bag`, `chair`, `picture`, `plant`.
  Distinct, well-separated objects that fuse correctly.
- **Genuine misses**: `cabinet` (never detected at any view), `window` (P/R ≈ 0.14–0.33), `door`
  (recall 0.25–0.50). OWLv2 under-fires on these classes on blurry low-res TUM frames.

## The sharp implication for the technical story

The precision loss is **over-counting of correctly-found objects**, not mislabeling. More views →
more duplicate detections of the same instance that 3D fusion fails to merge. This says the system's
main lever is **better duplicate-instance merging in 3D** (raise precision), not splitting.

This is the same axis the uncertainty-aware fusion acted on — but in the **wrong direction**: it
*tightened* the merge gate for uncertain pairs (more splitting), which is exactly what hurts here.
That independently explains the Week-3 negative result and points any future uncertainty work toward
*encouraging* duplicate merges / pruning fragments, not preventing merges.

## Caveats
- Reference is VLM-drafted (pending human verification); per-class counts (esp. small classes like
  `cabinet`, `picture`, `window` with ref ≤ 3) are the most sensitive to verification.
- n = 5 scenes; per-class precision/recall is aggregated (micro) over them.
- "Stuff" classes (desk/wall/floor) are kept here; they over-split and could be reported separately.
