# VGGT 3D Scene Graph Project

Working project for a Q1 / CVPR-level research direction:

**Uncertainty-Guided Language-Grounded 3D Scene Graphs from Sparse Views**

The goal is to build a sparse-view 3D scene understanding framework that uses frozen geometry and vision-language foundation models, then trains a lightweight graph reasoning module to produce object-level 3D segmentation and scene graphs.

## Core Idea

Existing 2025 methods are strong at either:

- feed-forward 3D geometry, such as VGGT, or
- open-vocabulary 3D segmentation, such as CUA-O3D and OpenSplat3D.

The gap is reliable **language-grounded 3D object and relationship understanding from only a few casual images**.

This project targets that gap by combining:

- **VGGT** for camera, depth, point maps, and tracks,
- **SAM / SAM2** for 2D object proposals,
- **CLIP / DINOv2** for open-vocabulary semantics,
- **Gaussian Splatting or point maps** for 3D representation,
- **graph reasoning** for object consistency and spatial relations.

## Documents

- `docs/research_proposal.md` - main proposal and contribution.
- `docs/novelty_gap.md` - what previous papers did and what this project adds.
- `docs/literature_map.md` - key 2025-2026 anchors and links.
- `docs/experiment_plan.md` - datasets, baselines, metrics, and milestones.
- `docs/dataset_protocol.md` - manifest format and benchmark subset protocol.
- `docs/paper_ready_status.md` - current artifacts, benchmark next steps, and paper checklist.
- `docs/annotation_review_worklist.md` - five-scene annotation packet review workload.
- `docs/paper_outline.md` - manuscript structure.
- `docs/manuscript_starter.md` - draftable abstract, method, and benchmark result text.
- `docs/mac_feasibility.md` - realistic Apple Silicon strategy.
- `docs/vggt_integration.md` - how to run and save VGGT geometry outputs.
- `paper/main.tex` - active manuscript draft.

## Code Scaffold

- `src/vggt_scene_graph/types.py` - shared dataclasses.
- `src/vggt_scene_graph/graph_builder.py` - object graph construction utilities.
- `src/vggt_scene_graph/image_matching.py` - lightweight image overlap sanity checks.
- `src/vggt_scene_graph/proposals.py` - lightweight local 2D proposal scaffold.
- `src/vggt_scene_graph/datasets.py` - dataset manifest loading and sparse-view records.
- `src/vggt_scene_graph/lifting.py` - 2D proposal to VGGT world-point lifting.
- `src/vggt_scene_graph/scene_graph_io.py` - scene graph serialization.
- `src/vggt_scene_graph/relations.py` - spatial relation heuristics.
- `src/vggt_scene_graph/metrics.py` - sparse-view evaluation helpers.
- `scripts/run_vggt_geometry.py` - VGGT geometry extraction entry point.
- `scripts/build_dataset_manifest.py` - scan benchmark image folders into a manifest.
- `scripts/download_tum_rgbd_subset.py` - download a sparse RGB-only multi-scene TUM RGB-D subset.
- `scripts/inspect_dataset.py` - dataset manifest inspection.
- `scripts/check_scene_matches.py` - ORB matching sanity check for candidate scene images.
- `scripts/run_2d_proposals.py` - OpenCV proposal extraction for local pipeline testing.
- `scripts/run_sam_proposals.py` - SAM automatic mask proposal extraction when optional dependencies/checkpoints are installed.
- `scripts/extract_proposal_features.py` - proposal-level handcrafted, CLIP, or DINO-style feature extraction.
- `scripts/run_pipeline.py` - end-to-end scene graph generation.
- `scripts/run_benchmark.py` - manifest-driven benchmark runner for all sparse-view stages.
- `scripts/assign_open_vocab_labels.py` - CLIP text-similarity labeling for fused object nodes.
- `scripts/create_annotation_packet.py` - node/relation review sheets and pseudo-reference annotation drafts.
- `scripts/create_paper_subset_annotation_packets.py` - batch annotation packet generation for the paper subset.
- `scripts/render_annotation_review.py` - static visual review page with per-node SAM crop thumbnails.
- `scripts/build_annotations_from_review.py` - convert reviewed CSV sheets into evaluator-ready annotation JSON.
- `scripts/evaluate_scene_graph.py` - graph quality metrics and optional annotation-based F1.
- `scripts/evaluate_sparse_view_annotations.py` - batch sparse-view evaluation with per-scene annotation packets.
- `scripts/summarize_scene_graph.py` - CSV summary of generated scene graphs.
- `scripts/export_paper_tables.py` - export CSV summaries to LaTeX/Markdown paper tables.
- `scripts/export_sparse_view_tables.py` - export multi-scene sparse-view benchmark tables.
- `scripts/export_sparse_view_metric_tables.py` - export sparse-view F1 metrics to paper tables.
- `scripts/visualize_scene_graph.py` - simple 3D graph figure for qualitative inspection.
- `scripts/create_paper_diagrams.py` - generate method and benchmark protocol diagrams.
- `scripts/create_qualitative_figure.py` - assemble RGB/scene-graph qualitative paper figures.

## Current End-To-End Pipeline

```bash
PYTHONPATH=src .venv/bin/python scripts/run_pipeline.py \
  --scene-id tum_rgbd_freiburg1_room \
  --scene-dir data/benchmark/tum_rgbd_freiburg1_room/images \
  --geometry results/benchmark_tum_rgbd/tum_rgbd_freiburg1_room/views_03/vggt_geometry.npz \
  --proposals results/benchmark_tum_rgbd/tum_rgbd_freiburg1_room/views_03/sam_clip_dinov2_features.json \
  --output results/benchmark_tum_rgbd/tum_rgbd_freiburg1_room/views_03/scene_graph.json
```

The current run uses a 3-view TUM RGB-D `freiburg1_room` subset and produces a 3D scene graph
with SAM mask-aware lifted object candidates, CLIP+DINOv2 feature vectors, fused object
nodes, uncertainty metadata, and spatial relations.

The current code runs an end-to-end sparse-view scene graph pipeline. The proposal format supports RLE masks
and multiple feature vectors, so SAM/SAM2 masks plus CLIP/DINO features can be swapped
without changing the 3D lifting or graph code.

## Benchmark Runner

Current proper data is in:

```text
data/benchmark/tum_rgbd_freiburg1_room/images/
```

The completed paper-scale TUM subset is:

```text
data/benchmark/tum_rgbd_paper_subset/
configs/datasets/tum_rgbd_paper_subset.json
results/benchmark_tum_rgbd_paper_subset/benchmark_index.json
results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_summary.csv
results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_metrics.csv
results/benchmark_tum_rgbd_paper_subset/sparse_view_pseudo_reference_metrics.csv
```

It contains five public TUM RGB-D sequences with 10 RGB frames per scene:
`freiburg1_room`, `freiburg1_desk`, `freiburg1_desk2`, `freiburg2_xyz`, and
`freiburg3_long_office_household`.

Create another manifest from a real benchmark subset laid out as one folder per scene:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_dataset_manifest.py \
  --dataset-root data/benchmark/scenes \
  --images-subdir images \
  --max-scenes 30 \
  --max-images-per-scene 10 \
  --output configs/datasets/benchmark_subset.json
```

Then use the benchmark runner. The current TUM manifest is
`configs/datasets/tum_rgbd_freiburg1_room.json`:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_benchmark.py \
  --dataset configs/datasets/tum_rgbd_freiburg1_room.json \
  --output-root results/benchmark_tum_rgbd \
  --view-counts 3 5 8 10 \
  --sam-checkpoint models/sam_vit_b_01ec64.pth \
  --label-vocab configs/label_vocab/indoor_open_vocab.json \
  --label-local-files-only
```

For a command-only check before spending compute, add `--dry-run`.

Run or resume the full 5-scene paper subset with:

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

To validate or resume one scene at a time, add `--scene-id`, for example:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_benchmark.py \
  --dataset configs/datasets/tum_rgbd_paper_subset.json \
  --scene-id tum_rgbd_freiburg1_desk \
  --output-root results/benchmark_tum_rgbd_paper_subset \
  --view-counts 3 \
  --sam-checkpoint models/sam_vit_b_01ec64.pth \
  --sam-points-per-side 12 \
  --sam-max-proposals-per-image 20 \
  --label-vocab configs/label_vocab/indoor_open_vocab.json \
  --label-local-files-only \
  --skip-existing
```

## Current Local Artifacts

The single-scene TUM validation run creates 3/5/8/10-view outputs:

1. VGGT point/depth/camera outputs for 3, 5, 8, and 10 benchmark views.
2. SAM `vit_b` RLE masks plus CLIP and DINOv2 feature vectors.
3. Mask-aware lifted 3D object candidates from VGGT world points.
4. A fused 3D object graph.
5. A labeled JSON scene graph with nodes, uncertainty metadata, and relations.
6. Paper tables under `paper/tables/`.

Sparse-view curve:

| Views | Candidates | Fused Objects | Multi-View Objects | Relations | Mean Uncertainty |
| --- | --- | --- | --- | --- | --- |
| 3 | 58 | 27 | 18 | 466 | 0.014525 |
| 5 | 98 | 32 | 24 | 628 | 0.014585 |
| 8 | 158 | 30 | 26 | 580 | 0.011999 |
| 10 | 198 | 32 | 28 | 636 | 0.011513 |

The five-scene paper subset has completed all 20 planned sparse-view runs. Aggregate
results are exported to `paper/tables/tum_rgbd_paper_subset_by_view.*`, and the full
per-scene table is exported to `paper/tables/tum_rgbd_paper_subset_results.*`.

Paper-subset average sparse-view curve:

| Views | Scenes | Candidates | Fused Objects | Multi-View Objects | Relations | Mean Uncertainty |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 5 | 54.00 | 31.80 | 11.80 | 585.20 | 0.026421 |
| 5 | 5 | 88.60 | 42.80 | 16.80 | 912.80 | 0.035933 |
| 8 | 5 | 140.20 | 61.40 | 24.20 | 1472.40 | 0.036613 |
| 10 | 5 | 173.60 | 72.20 | 28.20 | 2104.00 | 0.034249 |

The next actual experiment step is checked annotation: review the generated 10-view
paper-subset packets, correct object labels and relation counts, then rerun
`scripts/evaluate_scene_graph.py` with annotation JSON files for object/relation
precision, recall, and F1. The paper-subset packets are now generated under:

```text
results/benchmark_tum_rgbd_paper_subset/annotations/
docs/annotation_review_worklist.md
```

Paper-subset annotation packet index:

```text
results/benchmark_tum_rgbd_paper_subset/annotations/annotation_packet_index.json
```

Current five-scene pseudo-reference consistency table:

| Views | Scenes | Object F1 | Relation F1 |
| --- | ---: | ---: | ---: |
| 3 | 5 | 0.622 | 0.434 |
| 5 | 5 | 0.751 | 0.561 |
| 8 | 5 | 0.914 | 0.799 |
| 10 | 5 | 1.000 | 1.000 |

This uses each scene's 10-view prediction-derived annotation draft as the reference. It
is a consistency result, not ground-truth evaluation.

Earlier single-scene validation annotation/evaluation packet:

```text
results/benchmark_tum_rgbd/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/
results/benchmark_tum_rgbd/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/annotation_review.html
results/benchmark_tum_rgbd/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/annotation_from_review.json
results/benchmark_tum_rgbd/sparse_view_pseudo_reference_metrics.csv
results/benchmark_tum_rgbd/sparse_view_review_draft_metrics.csv
```

The pseudo-reference metrics compare 3/5/8-view outputs against the 10-view predicted
graph. This is a consistency check, not ground-truth evaluation.

## Manual Annotation Loop

For the paper-subset review, follow:

```text
docs/annotation_review_worklist.md
```

Start with one of the smaller scenes:

```text
results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg3_long_office_household_pseudo_from_10view/annotation_review.html
results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg2_xyz_pseudo_from_10view/annotation_review.html
```

Use the visual review sheet while editing the matching CSV files:

```text
results/benchmark_tum_rgbd_paper_subset/annotations/<scene>_pseudo_from_10view/annotation_review.html
results/benchmark_tum_rgbd_paper_subset/annotations/<scene>_pseudo_from_10view/node_review.csv
results/benchmark_tum_rgbd_paper_subset/annotations/<scene>_pseudo_from_10view/relation_review.csv
```

After filling object `review_label` and `keep`, plus relation `keep` and
`review_count`, build checked annotations:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_annotations_from_review.py \
  --node-review results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg2_xyz_pseudo_from_10view/node_review.csv \
  --relation-review results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg2_xyz_pseudo_from_10view/relation_review.csv \
  --annotation-draft results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg2_xyz_pseudo_from_10view/annotation_draft.json \
  --source-scene-graph results/benchmark_tum_rgbd_paper_subset/tum_rgbd_freiburg2_xyz/views_10/scene_graph_labeled.json \
  --output results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg2_xyz_pseudo_from_10view/annotation_checked.json \
  --require-reviewed
```

After all five checked annotation files exist, rerun the batch evaluator with
`--annotation-file-name annotation_checked.json` and update the paper tables.
