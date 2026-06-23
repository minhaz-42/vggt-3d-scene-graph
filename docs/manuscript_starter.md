# Manuscript Starter

## Working Title

Uncertainty-Guided Language-Grounded 3D Scene Graphs from Sparse Views

## Draft Abstract

We study language-grounded 3D scene graph construction from a small number of casual
RGB views. Recent feed-forward 3D models can recover camera, depth, and point-map
geometry without per-scene optimization, while 2D foundation models provide strong
open-vocabulary object proposals. However, converting sparse 2D evidence into
consistent 3D object identities and spatial relations remains difficult when views are
limited and proposal quality varies. We propose a framework that combines VGGT geometry,
SAM mask proposals, CLIP+DINOv2 proposal features, mask-aware 2D-to-3D lifting,
uncertainty scoring, cross-view graph fusion, open-vocabulary node labeling, and
rule-based relation inference. On a five-sequence TUM RGB-D sparse-view benchmark with
20 completed runs, the number of lifted proposals increases from 54.0 to 173.6 on
average as views increase from 3 to 10. Fused object nodes increase from 31.8 to 72.2,
multi-view object nodes from 11.8 to 28.2, and inferred spatial relations from 585.2 to
2104.0. Against scene-specific 10-view pseudo references, object-label F1 improves from
0.622 to 0.914 and relation-triplet F1 from 0.434 to 0.799 between 3 and 8 views. These
results establish a working end-to-end pipeline and a reproducible protocol for checked
object and relation annotation.

## Method Paragraph

Given sparse RGB views, we first run VGGT to obtain per-view camera parameters, depth,
confidence maps, and world-point maps. We then generate 2D object candidates with SAM
and encode each proposal using CLIP and DINOv2 visual features. Each mask is lifted into
3D by selecting the VGGT world points that fall inside the resized proposal mask, after
filtering low-confidence geometry. The lifted candidate stores its 3D point sample,
centroid, 3D bounding box, feature embedding, proposal confidence, world-point
confidence, and compactness-based uncertainty. Cross-view candidates are fused with a
geometry graph whose edges require centroid proximity and, when available, visual
feature agreement. Fused nodes inherit aggregated 3D points, averaged normalized
features, view coverage, and uncertainty. Finally, an open-vocabulary labeling module
assigns CLIP text-similarity labels and a spatial relation module predicts near,
left/right, above/below, and front/behind relations from fused object centroids.

## Local Validation Paragraph

We first validate the pipeline on `tum_rgbd_freiburg1_room`, a TUM RGB-D benchmark
sequence registered through `configs/datasets/tum_rgbd_freiburg1_room.json`. VGGT
geometry, SAM `vit_b` proposals, CLIP+DINOv2 proposal features, labeled scene graphs,
and qualitative figures are saved under:

```text
results/benchmark_tum_rgbd/tum_rgbd_freiburg1_room/views_03
results/benchmark_tum_rgbd/tum_rgbd_freiburg1_room/views_05
results/benchmark_tum_rgbd/tum_rgbd_freiburg1_room/views_08
results/benchmark_tum_rgbd/tum_rgbd_freiburg1_room/views_10
```

The single-scene run gives a quick sanity curve: lifted SAM proposals increase from 58
to 198 between 3 and 10 views, while multi-view object support increases from 18 to 28.

## Paper Benchmark Paragraph

For paper-scale evaluation, we use a five-sequence TUM RGB-D subset registered through
`configs/datasets/tum_rgbd_paper_subset.json`. It contains 10 RGB frames each from
`freiburg1_room`, `freiburg1_desk`, `freiburg1_desk2`, `freiburg2_xyz`, and
`freiburg3_long_office_household`. The completed benchmark evaluates each scene at 3,
5, 8, and 10 views, producing 20 labeled scene graphs and 20 qualitative figures under:

```text
results/benchmark_tum_rgbd_paper_subset/
```

Aggregate statistics and proxy metrics are stored in:

```text
results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_summary.csv
results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_metrics.csv
results/benchmark_tum_rgbd_paper_subset/sparse_view_pseudo_reference_metrics.csv
```

Qualitative figure assets are stored in:

```text
paper/figures/method_pipeline.png
paper/figures/evaluation_protocol.png
paper/figures/tum_rgbd_paper_subset_qualitative.png
paper/figures/tum_rgbd_paper_subset_qualitative_all.png
```

Compiled manuscript:

```text
paper/main.pdf
```

## Current Benchmark Table

Average structural statistics over the five-scene paper subset:

| Views | Scenes | Candidates | Fused Objects | Multi-View Objects | Relations | Mean Uncertainty |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 5 | 54.00 | 31.80 | 11.80 | 585.20 | 0.026421 |
| 5 | 5 | 88.60 | 42.80 | 16.80 | 912.80 | 0.035933 |
| 8 | 5 | 140.20 | 61.40 | 24.20 | 1472.40 | 0.036613 |
| 10 | 5 | 173.60 | 72.20 | 28.20 | 2104.00 | 0.034249 |

Per-scene results are available in:

```text
paper/tables/tum_rgbd_paper_subset_results.md
paper/tables/tum_rgbd_paper_subset_results.tex
```

## Pseudo-Reference Consistency Table

Each scene's 10-view prediction is converted into an annotation draft and used as a
pseudo reference for the same scene's 3/5/8-view predictions:

| Views | Scenes | Object F1 | Relation F1 |
| --- | ---: | ---: | ---: |
| 3 | 5 | 0.622 | 0.434 |
| 5 | 5 | 0.751 | 0.561 |
| 8 | 5 | 0.914 | 0.799 |
| 10 | 5 | 1.000 | 1.000 |

## Prepared Paper Subset

| Scene | Frames | Sparse views |
| --- | ---: | --- |
| tum_rgbd_freiburg1_room | 10 | 3/5/8/10 |
| tum_rgbd_freiburg1_desk | 10 | 3/5/8/10 |
| tum_rgbd_freiburg1_desk2 | 10 | 3/5/8/10 |
| tum_rgbd_freiburg2_xyz | 10 | 3/5/8/10 |
| tum_rgbd_freiburg3_long_office_household | 10 | 3/5/8/10 |

## Immediate Paper Gaps

1. Create checked annotation packets for the 10-view graph of each paper-subset scene.
2. Report object-label and relation-triplet precision, recall, and F1 against checked
   annotations.
3. Add baseline or ablation results if compute allows.
4. Polish the method diagram and qualitative graph figure.
5. Verify bibliography formatting against the target venue style.
