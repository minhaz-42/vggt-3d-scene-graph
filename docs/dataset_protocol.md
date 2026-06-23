# Dataset Protocol

## Purpose

The project uses dataset manifests to make experiments reproducible. A manifest records
scene ids, image folders, selected sparse views, split labels, and sparse-view counts.
Generated VGGT geometry, SAM proposals, CLIP+DINOv2 features, scene graphs, labels, and
figures are written under `results/`.

## Current Proper Datasets

Completed single-scene validation manifest:

```text
configs/datasets/tum_rgbd_freiburg1_room.json
```

It contains one public benchmark scene:

- dataset: TUM RGB-D benchmark
- scene id: `tum_rgbd_freiburg1_room`
- image folder: `data/benchmark/tum_rgbd_freiburg1_room/images`
- input views: `frame_000001.png` through `frame_000010.png`
- sparse-view counts: 3, 5, 8, 10

Completed multi-scene paper subset:

```text
configs/datasets/tum_rgbd_paper_subset.json
data/benchmark/tum_rgbd_paper_subset/
```

It contains five public TUM RGB-D sequences, each with 10 selected RGB frames and local
provenance in `DATASET.md`:

| Scene ID | Source sequence | Frames | Sparse views |
| --- | --- | ---: | --- |
| `tum_rgbd_freiburg1_room` | `rgbd_dataset_freiburg1_room` | 10 | 3/5/8/10 |
| `tum_rgbd_freiburg1_desk` | `rgbd_dataset_freiburg1_desk` | 10 | 3/5/8/10 |
| `tum_rgbd_freiburg1_desk2` | `rgbd_dataset_freiburg1_desk2` | 10 | 3/5/8/10 |
| `tum_rgbd_freiburg2_xyz` | `rgbd_dataset_freiburg2_xyz` | 10 | 3/5/8/10 |
| `tum_rgbd_freiburg3_long_office_household` | `rgbd_dataset_freiburg3_long_office_household` | 10 | 3/5/8/10 |

Inspect the paper subset with:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_dataset.py \
  --dataset configs/datasets/tum_rgbd_paper_subset.json
```

Create sparse-view split records with:

```bash
PYTHONPATH=src .venv/bin/python scripts/evaluate_sparse_views.py \
  --dataset configs/datasets/tum_rgbd_paper_subset.json \
  --output results/benchmark_tum_rgbd_paper_subset/sparse_view_splits.json
```

## Completed Sparse-View Runs

Single-scene validation command:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_benchmark.py \
  --dataset configs/datasets/tum_rgbd_freiburg1_room.json \
  --output-root results/benchmark_tum_rgbd \
  --view-counts 3 5 8 10 \
  --sam-checkpoint models/sam_vit_b_01ec64.pth \
  --sam-points-per-side 12 \
  --sam-max-proposals-per-image 20 \
  --label-vocab configs/label_vocab/indoor_open_vocab.json \
  --label-local-files-only
```

Paper-subset benchmark command:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_benchmark.py \
  --dataset configs/datasets/tum_rgbd_paper_subset.json \
  --output-root results/benchmark_tum_rgbd_paper_subset \
  --view-counts 3 5 8 10 \
  --sam-checkpoint models/sam_vit_b_01ec64.pth \
  --sam-points-per-side 12 \
  --sam-max-proposals-per-image 20 \
  --label-vocab configs/label_vocab/indoor_open_vocab.json \
  --label-local-files-only \
  --skip-existing
```

Each view-count directory contains:

- `vggt_geometry.npz`
- `sam_proposals.json`
- `sam_clip_dinov2_features.json`
- `scene_graph.json`
- `scene_graph_labeled.json`
- `scene_graph.png`

Paper-subset output files:

```text
results/benchmark_tum_rgbd_paper_subset/benchmark_index.json
results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_summary.csv
results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_metrics.csv
results/benchmark_tum_rgbd_paper_subset/sparse_view_pseudo_reference_metrics.csv
paper/tables/tum_rgbd_paper_subset_by_view.tex
paper/tables/tum_rgbd_paper_subset_results.tex
paper/tables/tum_rgbd_paper_subset_pseudo_reference_by_view.tex
paper/figures/method_pipeline.png
paper/figures/evaluation_protocol.png
paper/figures/tum_rgbd_paper_subset_qualitative.png
```

Paper-subset average structural statistics:

| Views | Scenes | Candidates | Fused objects | Multi-view objects | Relations | Mean uncertainty |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 5 | 54.00 | 31.80 | 11.80 | 585.20 | 0.026421 |
| 5 | 5 | 88.60 | 42.80 | 16.80 | 912.80 | 0.035933 |
| 8 | 5 | 140.20 | 61.40 | 24.20 | 1472.40 | 0.036613 |
| 10 | 5 | 173.60 | 72.20 | 28.20 | 2104.00 | 0.034249 |

These are structural/proxy metrics. Checked object and relation annotations are needed
for final precision, recall, and F1.

Current pseudo-reference consistency averages, using each scene's 10-view prediction as
the reference:

| Views | Scenes | Object F1 | Relation F1 |
| --- | ---: | ---: | ---: |
| 3 | 5 | 0.622 | 0.434 |
| 5 | 5 | 0.751 | 0.561 |
| 8 | 5 | 0.914 | 0.799 |
| 10 | 5 | 1.000 | 1.000 |

## Rebuilding Tables

After regenerating scene graphs, rebuild the summary, proxy metrics, and paper tables:

```bash
PYTHONPATH=src .venv/bin/python scripts/summarize_scene_graph.py \
  results/benchmark_tum_rgbd_paper_subset/*/views_*/scene_graph_labeled.json \
  --output results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_summary.csv
```

```bash
PYTHONPATH=src .venv/bin/python scripts/evaluate_scene_graph.py \
  results/benchmark_tum_rgbd_paper_subset/*/views_*/scene_graph_labeled.json \
  --output results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_metrics.csv
```

```bash
PYTHONPATH=src .venv/bin/python scripts/evaluate_sparse_view_annotations.py \
  --dataset configs/datasets/tum_rgbd_paper_subset.json \
  --results-root results/benchmark_tum_rgbd_paper_subset \
  --annotations-root results/benchmark_tum_rgbd_paper_subset/annotations \
  --output results/benchmark_tum_rgbd_paper_subset/sparse_view_pseudo_reference_metrics.csv \
  --reference-view-count 10 \
  --packet-mode pseudo_reference \
  --annotation-file-name annotation_draft.json
```

```bash
PYTHONPATH=src .venv/bin/python scripts/export_sparse_view_tables.py \
  --summary results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_summary.csv \
  --latex-output paper/tables/tum_rgbd_paper_subset_results.tex \
  --markdown-output paper/tables/tum_rgbd_paper_subset_results.md \
  --aggregate-latex-output paper/tables/tum_rgbd_paper_subset_by_view.tex \
  --aggregate-markdown-output paper/tables/tum_rgbd_paper_subset_by_view.md
```

```bash
PYTHONPATH=src .venv/bin/python scripts/export_sparse_view_metric_tables.py \
  --metrics results/benchmark_tum_rgbd_paper_subset/sparse_view_pseudo_reference_metrics.csv \
  --latex-output paper/tables/tum_rgbd_paper_subset_pseudo_reference_results.tex \
  --markdown-output paper/tables/tum_rgbd_paper_subset_pseudo_reference_results.md \
  --aggregate-latex-output paper/tables/tum_rgbd_paper_subset_pseudo_reference_by_view.tex \
  --aggregate-markdown-output paper/tables/tum_rgbd_paper_subset_pseudo_reference_by_view.md
```

```bash
PYTHONPATH=src .venv/bin/python scripts/create_paper_diagrams.py \
  --output-dir paper/figures
```

```bash
PYTHONPATH=src .venv/bin/python scripts/create_qualitative_figure.py \
  --dataset configs/datasets/tum_rgbd_paper_subset.json \
  --results-root results/benchmark_tum_rgbd_paper_subset \
  --output paper/figures/tum_rgbd_paper_subset_qualitative.png \
  --scene-id tum_rgbd_freiburg1_room \
  --scene-id tum_rgbd_freiburg1_desk2 \
  --scene-id tum_rgbd_freiburg3_long_office_household \
  --view-count 10
```

## Expanding The Benchmark

The current paper subset was downloaded with:

```bash
PYTHONPATH=src .venv/bin/python scripts/download_tum_rgbd_subset.py \
  --num-frames 10 \
  --sample-mode stride \
  --frame-stride 10 \
  --output-root data/benchmark/tum_rgbd_paper_subset \
  --manifest-output configs/datasets/tum_rgbd_paper_subset.json
```

To inspect available TUM RGB-D mirror folders before changing the subset:

```bash
PYTHONPATH=src .venv/bin/python scripts/download_tum_rgbd_subset.py --discover
```

For a larger paper subset, place one folder per scene under `data/benchmark/scenes/`,
with RGB files in an `images/` subfolder, then build a manifest:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_dataset_manifest.py \
  --dataset-root data/benchmark/scenes \
  --images-subdir images \
  --max-scenes 30 \
  --max-images-per-scene 10 \
  --output configs/datasets/benchmark_subset.json
```

Then run:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_benchmark.py \
  --dataset configs/datasets/benchmark_subset.json \
  --output-root results/benchmark \
  --view-counts 3 5 8 10 \
  --sam-checkpoint models/sam_vit_b_01ec64.pth \
  --label-vocab configs/label_vocab/indoor_open_vocab.json \
  --label-local-files-only
```

Use `--dry-run` first to write an index and inspect planned commands without model
inference.

## Evaluation Annotations

Annotation template:

```text
configs/evaluation/annotation_template.json
```

Create or refresh all five paper-subset 10-view review packets with:

```bash
PYTHONPATH=src .venv/bin/python scripts/create_paper_subset_annotation_packets.py \
  --dataset configs/datasets/tum_rgbd_paper_subset.json \
  --results-root results/benchmark_tum_rgbd_paper_subset \
  --output-root results/benchmark_tum_rgbd_paper_subset/annotations \
  --view-count 10 \
  --mode pseudo_reference
```

This writes the packet index and per-scene review directories:

```text
results/benchmark_tum_rgbd_paper_subset/annotations/annotation_packet_index.json
results/benchmark_tum_rgbd_paper_subset/annotations/*_pseudo_from_10view/
```

The review workload is summarized in `docs/annotation_review_worklist.md`.

Create a review packet from a 10-view graph:

```bash
PYTHONPATH=src .venv/bin/python scripts/create_annotation_packet.py \
  --scene-graph results/benchmark_tum_rgbd_paper_subset/tum_rgbd_freiburg1_room/views_10/scene_graph_labeled.json \
  --output-dir results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view \
  --mode pseudo_reference
```

Render a visual sheet with representative SAM-mask crops for each fused 3D node:

```bash
PYTHONPATH=src .venv/bin/python scripts/render_annotation_review.py \
  --scene-graph results/benchmark_tum_rgbd_paper_subset/tum_rgbd_freiburg1_room/views_10/scene_graph_labeled.json \
  --proposals results/benchmark_tum_rgbd_paper_subset/tum_rgbd_freiburg1_room/views_10/sam_proposals.json \
  --scene-dir data/benchmark/tum_rgbd_paper_subset/tum_rgbd_freiburg1_room/images \
  --node-review results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/node_review.csv \
  --relation-review results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/relation_review.csv \
  --output-dir results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view
```

After manually filling object `review_label`, object `keep`, relation `keep`, and
relation `review_count` fields, build the evaluator annotation JSON:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_annotations_from_review.py \
  --node-review results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/node_review.csv \
  --relation-review results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/relation_review.csv \
  --annotation-draft results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/annotation_draft.json \
  --source-scene-graph results/benchmark_tum_rgbd_paper_subset/tum_rgbd_freiburg1_room/views_10/scene_graph_labeled.json \
  --output results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/annotation_checked.json \
  --require-reviewed
```

The evaluator accepts object label counts and labeled relation triplets. Without
annotations it reports quality/proxy metrics; with annotations it also reports object
label and relation triplet precision, recall, and F1:

```bash
PYTHONPATH=src .venv/bin/python scripts/evaluate_scene_graph.py \
  results/benchmark_tum_rgbd_paper_subset/tum_rgbd_freiburg1_room/views_03/scene_graph_labeled.json \
  --annotations results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/annotation_checked.json \
  --output results/benchmark_tum_rgbd_paper_subset/tum_rgbd_freiburg1_room_checked_metrics.csv
```
