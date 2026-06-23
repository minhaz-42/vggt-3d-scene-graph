# Paper-Ready Status

## Current Claim Level

The project now uses proper public TUM RGB-D benchmark data instead of the original
local sample photos. It has:

- a completed single-scene `freiburg1_room` 3/5/8/10-view validation run,
- a completed five-sequence TUM RGB-D paper subset with 50 RGB frames total,
- 20 completed paper-subset sparse-view runs across 3, 5, 8, and 10 views,
- completed checked prediction-seeded annotation CSV/JSON files for all five scenes,
- checked object-label and relation-triplet metrics for all 20 sparse-view runs,
- generated LaTeX/Markdown tables and figures for the manuscript.

The remaining paper gap is not data collection, benchmark execution, or checked
sparse-view reference evaluation. The main remaining limitations are broader
independent scene annotations, stronger external baselines or ablations if compute
allows, and final venue-format polishing.

## Current Data And Artifacts

- Single-scene manifest: `configs/datasets/tum_rgbd_freiburg1_room.json`
- Paper subset manifest: `configs/datasets/tum_rgbd_paper_subset.json`
- Single-scene RGB frames: `data/benchmark/tum_rgbd_freiburg1_room/images/`
- Paper subset RGB frames: `data/benchmark/tum_rgbd_paper_subset/`
- Single-scene benchmark index: `results/benchmark_tum_rgbd/benchmark_index.json`
- Paper subset benchmark index: `results/benchmark_tum_rgbd_paper_subset/benchmark_index.json`
- Paper subset sparse-view split file: `results/benchmark_tum_rgbd_paper_subset/sparse_view_splits.json`
- Paper subset summary CSV: `results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_summary.csv`
- Paper subset proxy metrics CSV: `results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_metrics.csv`
- Paper subset pseudo-reference metrics CSV: `results/benchmark_tum_rgbd_paper_subset/sparse_view_pseudo_reference_metrics.csv`
- Paper subset checked metrics CSV: `results/benchmark_tum_rgbd_paper_subset/sparse_view_checked_metrics.csv`
- Paper subset aggregate table: `paper/tables/tum_rgbd_paper_subset_by_view.tex`
- Paper subset aggregate table, Markdown: `paper/tables/tum_rgbd_paper_subset_by_view.md`
- Paper subset per-scene table: `paper/tables/tum_rgbd_paper_subset_results.tex`
- Paper subset per-scene table, Markdown: `paper/tables/tum_rgbd_paper_subset_results.md`
- Paper subset pseudo-reference table: `paper/tables/tum_rgbd_paper_subset_pseudo_reference_by_view.tex`
- Paper subset pseudo-reference per-scene table: `paper/tables/tum_rgbd_paper_subset_pseudo_reference_results.tex`
- Paper subset checked aggregate table: `paper/tables/tum_rgbd_paper_subset_checked_by_view.tex`
- Paper subset checked per-scene table: `paper/tables/tum_rgbd_paper_subset_checked_results.tex`
- Main qualitative figure: `paper/figures/tum_rgbd_paper_subset_qualitative.png`
- All-scene qualitative figure: `paper/figures/tum_rgbd_paper_subset_qualitative_all.png`
- Method pipeline diagram: `paper/figures/method_pipeline.png`
- Evaluation protocol diagram: `paper/figures/evaluation_protocol.png`
- Compiled PDF: `paper/main.pdf`
- Paper subset annotation packet index: `results/benchmark_tum_rgbd_paper_subset/annotations/annotation_packet_index.json`
- Paper subset annotation worklist: `docs/annotation_review_worklist.md`
- Paper subset annotation status: `docs/annotation_review_status.md`
- Paper draft: `paper/main.tex`

Each completed paper-subset view directory contains:

- `vggt_geometry.npz`
- `sam_proposals.json`
- `sam_clip_dinov2_features.json`
- `scene_graph.json`
- `scene_graph_labeled.json`
- `scene_graph.png`

Current annotation/evaluation packet for the single-scene validation run:

- `results/benchmark_tum_rgbd/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/`
- `results/benchmark_tum_rgbd/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/annotation_review.html`
- `results/benchmark_tum_rgbd/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/annotation_from_review.json`
- `results/benchmark_tum_rgbd/sparse_view_pseudo_reference_metrics.csv`
- `results/benchmark_tum_rgbd/sparse_view_review_draft_metrics.csv`

The pseudo-reference metrics compare sparse-view outputs against the 10-view predicted
graph. They are consistency checks, not ground-truth evaluation.

## Completed Paper-Subset Command

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

## Completed Paper-Subset Results

Average structural scene-graph statistics over the five scenes:

| Views | Scenes | Candidates | Fused Objects | Multi-View Objects | Relations | Mean Uncertainty |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 5 | 54.00 | 31.80 | 11.80 | 585.20 | 0.026421 |
| 5 | 5 | 88.60 | 42.80 | 16.80 | 912.80 | 0.035933 |
| 8 | 5 | 140.20 | 61.40 | 24.20 | 1472.40 | 0.036613 |
| 10 | 5 | 173.60 | 72.20 | 28.20 | 2104.00 | 0.034249 |

Per-scene results are in:

```text
paper/tables/tum_rgbd_paper_subset_results.md
paper/tables/tum_rgbd_paper_subset_results.tex
```

## Method Section Can Now Describe

- Sparse RGB benchmark input
- VGGT geometry extraction
- Camera/depth/world-point output format
- Dataset manifest and sparse-view protocol
- SAM mask proposal extraction
- Mask-aware 2D-to-3D world-point lifting
- CLIP+DINOv2 proposal feature extraction and feature-aware fusion
- Confidence-aware uncertainty estimate
- Geometry-based cross-view object fusion
- CLIP text-similarity open-vocabulary node labeling
- Rule-based spatial relation inference
- Manifest-driven benchmark execution
- Checked sparse-view reference evaluation

## Tables Ready For The Paper

- `paper/tables/tum_rgbd_sparse_view.tex`: single-scene sparse-view validation
- `paper/tables/tum_rgbd_pseudo_reference.tex`: 10-view pseudo-reference consistency
  kept as backup/supplement material, not included in the main manuscript
- `paper/tables/tum_rgbd_paper_subset_plan.tex`: five-scene subset protocol
- `paper/tables/tum_rgbd_paper_subset_by_view.tex`: completed aggregate benchmark table
- `paper/tables/tum_rgbd_paper_subset_results.tex`: completed per-scene benchmark table
- `paper/tables/tum_rgbd_paper_subset_pseudo_reference_by_view.tex`: five-scene pseudo-reference consistency
- `paper/tables/tum_rgbd_paper_subset_pseudo_reference_results.tex`: per-scene pseudo-reference consistency
- `paper/tables/tum_rgbd_paper_subset_checked_by_view.tex`: checked aggregate object/relation F1
- `paper/tables/tum_rgbd_paper_subset_checked_results.tex`: checked per-scene object/relation F1
- `paper/figures/method_pipeline.png`: method pipeline diagram
- `paper/figures/evaluation_protocol.png`: benchmark and annotation protocol diagram
- `paper/figures/tum_rgbd_paper_subset_qualitative.png`: representative qualitative figure

## Next Work Needed Before Submission

1. Read the compiled PDF end to end for narrative flow and figure/table placement.
2. Add stronger baselines or ablations if compute allows.
3. Verify bibliography formatting against the target venue style.
4. Prepare a concise cover note explaining that checked metrics are
   prediction-seeded sparse-view references, not independent dense-scene ground truth.
