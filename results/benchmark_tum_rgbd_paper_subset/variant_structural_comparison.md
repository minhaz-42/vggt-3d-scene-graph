# Fusion Variant Structural Comparison

Results root: `results/benchmark_tum_rgbd_paper_subset`  ·  view counts: [3, 5, 8, 10]

Structural (annotation-free) statistics, averaged over scenes. Object/relation
F1 require the labelling + checked-annotation stages (run on GPU/Colab).

## Fused objects — higher = more split / less merge
| variant | views=3 | views=5 | views=8 | views=10 |
|---|---|---|---|---|
| graph-fusion | 31.8 | 42.8 | 61.4 | 72.2 |
| 2d-only | 19.8 | 21.6 | 25.0 | 29.0 |
| fixed-shrink | 33.2 | 45.6 | 67.2 | 79.8 |
| geometry-only | 19.8 | 24.2 | 31.8 | 32.6 |
| proposed | 32.6 | 44.0 | 63.4 | 75.2 |
| semantic-lifting | 54.0 | 88.6 | 140.2 | 173.6 |

## Multi-view objects — objects seen in >=2 views
| variant | views=3 | views=5 | views=8 | views=10 |
|---|---|---|---|---|
| graph-fusion | 11.8 | 16.8 | 24.2 | 28.2 |
| 2d-only | 9.6 | 10.8 | 11.0 | 11.8 |
| fixed-shrink | 11.6 | 17.4 | 23.4 | 28.0 |
| geometry-only | 10.0 | 12.6 | 15.4 | 17.0 |
| proposed | 11.2 | 16.8 | 23.8 | 27.4 |
| semantic-lifting | 0.0 | 0.0 | 0.0 | 0.0 |

## Mean source nodes/obj — avg candidates fused per object (higher = more merging)
| variant | views=3 | views=5 | views=8 | views=10 |
|---|---|---|---|---|
| graph-fusion | 1.7650 | 2.2243 | 2.5466 | 2.7815 |
| 2d-only | 2.7356 | 4.2825 | 5.8904 | 6.6405 |
| fixed-shrink | 1.7042 | 2.1026 | 2.3734 | 2.5262 |
| geometry-only | 2.8964 | 3.9640 | 5.1117 | 6.3192 |
| proposed | 1.7284 | 2.1616 | 2.4696 | 2.6312 |
| semantic-lifting | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Relations — #spatial relations
| variant | views=3 | views=5 | views=8 | views=10 |
|---|---|---|---|---|
| graph-fusion | 585.2 | 912.8 | 1472.4 | 2104.0 |
| 2d-only | 232.0 | 265.2 | 285.2 | 414.0 |
| fixed-shrink | 646.0 | 1062.8 | 1798.4 | 2536.0 |
| geometry-only | 188.0 | 219.2 | 262.0 | 255.6 |
| proposed | 610.8 | 958.4 | 1543.6 | 2219.6 |
| semantic-lifting | 1962.4 | 4987.2 | 11509.2 | 17192.4 |

## Mean uncertainty — avg node uncertainty
| variant | views=3 | views=5 | views=8 | views=10 |
|---|---|---|---|---|
| graph-fusion | 0.0264 | 0.0359 | 0.0366 | 0.0342 |
| 2d-only | 0.0268 | 0.0313 | 0.0347 | 0.0293 |
| fixed-shrink | 0.0276 | 0.0365 | 0.0397 | 0.0400 |
| geometry-only | 0.0287 | 0.0439 | 0.0489 | 0.0485 |
| proposed | 0.0273 | 0.0358 | 0.0368 | 0.0386 |
| semantic-lifting | 0.0346 | 0.0376 | 0.0382 | 0.0387 |
