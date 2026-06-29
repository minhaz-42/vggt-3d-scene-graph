# Variant comparison on the INDEPENDENT reference — `object_label_f1`

Source: `results/benchmark_owlv2/variant_independent_metrics.csv`  ·  mean over scenes  ·  views [3, 5, 8, 10]
n_scenes = 5

| variant | v3 | v5 | v8 | v10 |
|---|---|---|---|---|
| 2d-only | 0.4805 | 0.4944 | 0.5117 | 0.4986 |
| geometry-only | 0.4495 | 0.4768 | 0.5017 | 0.4956 |
| semantic-lifting | 0.4158 | 0.3395 | 0.2690 | 0.2315 |
| fixed-shrink | 0.5095 | 0.4868 | 0.4683 | 0.4253 |
| graph-fusion | 0.5054 | 0.5050 | 0.4903 | 0.4581 |
| **proposed** | 0.4922 | 0.4757 | 0.4326 | 0.3976 |

## `proposed` − `fixed-shrink` (object_label_f1)
- mean delta — v3: -0.0173, v5: -0.0111, v8: -0.0356, v10: -0.0276
- per-scene wins — v3: 0W/3L/2T (p=0.250), v5: 1W/4L/0T (p=0.375), v8: 1W/4L/0T (p=0.375), v10: 0W/5L/0T (p=0.062)

## `proposed` − `graph-fusion` (object_label_f1)
- mean delta — v3: -0.0133, v5: -0.0293, v8: -0.0577, v10: -0.0605
- per-scene wins — v3: 1W/3L/1T (p=0.625), v5: 0W/5L/0T (p=0.062), v8: 0W/5L/0T (p=0.062), v10: 0W/5L/0T (p=0.062)

## recall / precision (mean over scenes)
| variant | metric | v3 | v5 | v8 | v10 |
|---|---|---|---|---|---|
| 2d-only | recall | 0.3929 | 0.4317 | 0.5163 | 0.5296 |
| 2d-only | precision | 0.6897 | 0.6734 | 0.5928 | 0.5556 |
| geometry-only | recall | 0.3361 | 0.3858 | 0.4826 | 0.4752 |
| geometry-only | precision | 0.7043 | 0.6565 | 0.5531 | 0.5782 |
| semantic-lifting | recall | 0.5048 | 0.5653 | 0.6504 | 0.6578 |
| semantic-lifting | precision | 0.3717 | 0.2502 | 0.1730 | 0.1431 |
| fixed-shrink | recall | 0.4754 | 0.5029 | 0.6028 | 0.5991 |
| fixed-shrink | precision | 0.5773 | 0.5075 | 0.4095 | 0.3523 |
| graph-fusion | recall | 0.4659 | 0.4942 | 0.5941 | 0.5904 |
| graph-fusion | precision | 0.5873 | 0.5629 | 0.4432 | 0.4049 |
| proposed | recall | 0.4754 | 0.5409 | 0.6322 | 0.6371 |
| proposed | precision | 0.5314 | 0.4377 | 0.3362 | 0.2950 |
