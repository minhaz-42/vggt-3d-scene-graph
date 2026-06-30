# Variant comparison on the INDEPENDENT reference — `object_label_f1`

Source: `results/benchmark_owlv2/variant_independent_metrics.csv`  ·  mean over scenes  ·  views [3, 5, 8, 10]
n_scenes = 5

| variant | v3 | v5 | v8 | v10 |
|---|---|---|---|---|
| 2d-only | 0.4897 | 0.4940 | 0.4820 | 0.4647 |
| geometry-only | 0.4578 | 0.4843 | 0.4834 | 0.4833 |
| semantic-lifting | 0.4168 | 0.3326 | 0.2548 | 0.2148 |
| fixed-shrink | 0.5165 | 0.4849 | 0.4471 | 0.4008 |
| graph-fusion | 0.5126 | 0.5038 | 0.4688 | 0.4324 |
| **proposed** | 0.4982 | 0.4725 | 0.4132 | 0.3749 |
| graph-fusion-dedup | 0.5804 | 0.5923 | 0.6137 | 0.5787 |

## `proposed` − `fixed-shrink` (object_label_f1)
- mean delta — v3: -0.0183, v5: -0.0124, v8: -0.0340, v10: -0.0259
- per-scene wins — v3: 0W/3L/2T (p=0.250), v5: 1W/4L/0T (p=0.375), v8: 1W/4L/0T (p=0.375), v10: 0W/5L/0T (p=0.062)

## `proposed` − `graph-fusion` (object_label_f1)
- mean delta — v3: -0.0144, v5: -0.0313, v8: -0.0556, v10: -0.0574
- per-scene wins — v3: 1W/3L/1T (p=0.625), v5: 0W/5L/0T (p=0.062), v8: 0W/5L/0T (p=0.062), v10: 0W/5L/0T (p=0.062)

## recall / precision (mean over scenes)
| variant | metric | v3 | v5 | v8 | v10 |
|---|---|---|---|---|---|
| 2d-only | recall | 0.4167 | 0.4494 | 0.5184 | 0.5268 |
| 2d-only | precision | 0.6647 | 0.6484 | 0.5289 | 0.4907 |
| geometry-only | recall | 0.3552 | 0.4075 | 0.4935 | 0.4935 |
| geometry-only | precision | 0.6757 | 0.6330 | 0.5138 | 0.5439 |
| semantic-lifting | recall | 0.5360 | 0.5957 | 0.6643 | 0.6643 |
| semantic-lifting | precision | 0.3574 | 0.2372 | 0.1602 | 0.1299 |
| fixed-shrink | recall | 0.5054 | 0.5265 | 0.6141 | 0.6030 |
| fixed-shrink | precision | 0.5573 | 0.4893 | 0.3822 | 0.3257 |
| graph-fusion | recall | 0.4954 | 0.5170 | 0.6046 | 0.5935 |
| graph-fusion | precision | 0.5673 | 0.5435 | 0.4132 | 0.3735 |
| proposed | recall | 0.5054 | 0.5667 | 0.6448 | 0.6432 |
| proposed | precision | 0.5124 | 0.4210 | 0.3140 | 0.2724 |
| graph-fusion-dedup | recall | 0.4759 | 0.5070 | 0.6046 | 0.5935 |
| graph-fusion-dedup | precision | 0.7995 | 0.7489 | 0.6503 | 0.5963 |
