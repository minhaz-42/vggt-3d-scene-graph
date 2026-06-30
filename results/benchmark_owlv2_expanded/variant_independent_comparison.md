# Variant comparison on the INDEPENDENT reference — `object_label_f1`

Source: `results/benchmark_owlv2_expanded/variant_independent_metrics.csv`  ·  mean over scenes  ·  views [3, 5, 8, 10]
n_scenes = 28

| variant | v3 | v5 | v8 | v10 |
|---|---|---|---|---|
| 2d-only | 0.5120 | 0.5003 | 0.4867 | 0.4753 |
| geometry-only | 0.4617 | 0.4605 | 0.4594 | 0.4493 |
| semantic-lifting | 0.3752 | 0.2881 | 0.2123 | 0.1797 |
| fixed-shrink | 0.5048 | 0.4715 | 0.4448 | 0.4189 |
| graph-fusion | 0.5129 | 0.4895 | 0.4664 | 0.4502 |
| **proposed** | 0.4801 | 0.4370 | 0.3841 | 0.3544 |
| graph-fusion-dedup | 0.5696 | 0.5723 | 0.5860 | 0.5725 |

## `proposed` − `fixed-shrink` (object_label_f1)
- mean delta — v3: -0.0247, v5: -0.0346, v8: -0.0607, v10: -0.0645
- per-scene wins — v3: 0W/21L/7T (p=0.000), v5: 3W/21L/4T (p=0.000), v8: 1W/25L/2T (p=0.000), v10: 0W/26L/2T (p=0.000)

## `proposed` − `graph-fusion` (object_label_f1)
- mean delta — v3: -0.0328, v5: -0.0526, v8: -0.0823, v10: -0.0958
- per-scene wins — v3: 2W/22L/4T (p=0.000), v5: 0W/26L/2T (p=0.000), v8: 0W/26L/2T (p=0.000), v10: 0W/27L/1T (p=0.000)

## recall / precision (mean over scenes)
| variant | metric | v3 | v5 | v8 | v10 |
|---|---|---|---|---|---|
| 2d-only | recall | 0.4542 | 0.4680 | 0.4769 | 0.4770 |
| 2d-only | precision | 0.6462 | 0.6020 | 0.5455 | 0.5258 |
| geometry-only | recall | 0.3769 | 0.4066 | 0.4405 | 0.4404 |
| geometry-only | precision | 0.6581 | 0.6087 | 0.5500 | 0.5452 |
| semantic-lifting | recall | 0.5421 | 0.5804 | 0.6118 | 0.6179 |
| semantic-lifting | precision | 0.3055 | 0.2010 | 0.1315 | 0.1072 |
| fixed-shrink | recall | 0.5139 | 0.5444 | 0.5884 | 0.5904 |
| fixed-shrink | precision | 0.5286 | 0.4508 | 0.3862 | 0.3528 |
| graph-fusion | recall | 0.5104 | 0.5397 | 0.5810 | 0.5870 |
| graph-fusion | precision | 0.5560 | 0.4945 | 0.4203 | 0.3989 |
| proposed | recall | 0.5160 | 0.5560 | 0.5960 | 0.6018 |
| proposed | precision | 0.4784 | 0.3883 | 0.2992 | 0.2661 |
| graph-fusion-dedup | recall | 0.5021 | 0.5289 | 0.5760 | 0.5807 |
| graph-fusion-dedup | precision | 0.7135 | 0.6613 | 0.6221 | 0.5930 |
