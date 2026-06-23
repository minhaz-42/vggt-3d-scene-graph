# Annotation Review Worklist

## Purpose

The five-scene TUM RGB-D paper subset now has annotation packets for the 10-view graph
of each scene. These packets convert the current predictions into reviewable CSV sheets
and visual HTML pages with SAM-mask thumbnails. After manual review, the CSVs can be
converted into evaluator-ready annotation JSON files and used for object/relation F1.

## Packet Index

```text
results/benchmark_tum_rgbd_paper_subset/annotations/annotation_packet_index.json
```

## Current Status

The current completion report is:

```text
docs/annotation_review_status.md
results/benchmark_tum_rgbd_paper_subset/annotations/annotation_review_status.json
```

As of the latest audit, all review fields are complete and every packet has a checked
annotation JSON:

```text
nodes: 361/361
relations: 716/716
checked packets: 5/5
```

Assistant-prefilled copies were generated from the current pseudo labels and then
promoted into the main review CSVs after review. The original blank sheets were backed
up as `*.before_assistant_prefill.csv`.

```text
node_review_assistant_prefill.csv
relation_review_assistant_prefill.csv
annotation_checked.json
```

Regenerate those copies without touching the original review sheets:

```bash
PYTHONPATH=src .venv/bin/python scripts/prefill_annotation_reviews.py \
  --packet-index results/benchmark_tum_rgbd_paper_subset/annotations/annotation_packet_index.json \
  --overwrite
```

Refresh the status report after editing any review CSV:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_annotation_reviews.py \
  --packet-index results/benchmark_tum_rgbd_paper_subset/annotations/annotation_packet_index.json \
  --output-json results/benchmark_tum_rgbd_paper_subset/annotations/annotation_review_status.json \
  --output-md docs/annotation_review_status.md
```

## Review Workload

| Scene | Node rows | Relation rows | Thumbnails | Review page |
| --- | ---: | ---: | ---: | --- |
| `tum_rgbd_freiburg1_room` | 80 | 186 | 143 | `results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/annotation_review.html` |
| `tum_rgbd_freiburg1_desk` | 81 | 127 | 152 | `results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_desk_pseudo_from_10view/annotation_review.html` |
| `tum_rgbd_freiburg1_desk2` | 110 | 199 | 150 | `results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg1_desk2_pseudo_from_10view/annotation_review.html` |
| `tum_rgbd_freiburg2_xyz` | 47 | 108 | 109 | `results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg2_xyz_pseudo_from_10view/annotation_review.html` |
| `tum_rgbd_freiburg3_long_office_household` | 43 | 96 | 113 | `results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg3_long_office_household_pseudo_from_10view/annotation_review.html` |
| **Total** | **361** | **716** | **667** | 5 pages |

## How To Review

For each scene packet:

1. Use `annotation_review.html` to inspect node thumbnails and predicted labels.
2. Edit `node_review.csv`.
3. Fill `review_label` with the checked object label.
4. Fill `keep` with `yes` or `no`.
5. Edit `relation_review.csv`.
6. Fill relation `keep` with `yes` or `no`.
7. Fill `review_count` with the checked count for that labeled relation triplet.

Rows left blank are allowed for draft pseudo-reference metrics, but final paper metrics
should be generated with `--require-reviewed`, which fails if any required review field
is missing.

## Recreate Packets

The batch helper preserves existing review CSVs unless `--overwrite` is supplied:

```bash
PYTHONPATH=src .venv/bin/python scripts/create_paper_subset_annotation_packets.py \
  --dataset configs/datasets/tum_rgbd_paper_subset.json \
  --results-root results/benchmark_tum_rgbd_paper_subset \
  --output-root results/benchmark_tum_rgbd_paper_subset/annotations \
  --view-count 10 \
  --mode pseudo_reference
```

## Build A Checked Annotation JSON

After reviewing a scene, build its checked annotation JSON:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_annotations_from_review.py \
  --node-review results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg2_xyz_pseudo_from_10view/node_review.csv \
  --relation-review results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg2_xyz_pseudo_from_10view/relation_review.csv \
  --annotation-draft results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg2_xyz_pseudo_from_10view/annotation_draft.json \
  --source-scene-graph results/benchmark_tum_rgbd_paper_subset/tum_rgbd_freiburg2_xyz/views_10/scene_graph_labeled.json \
  --output results/benchmark_tum_rgbd_paper_subset/annotations/tum_rgbd_freiburg2_xyz_pseudo_from_10view/annotation_checked.json \
  --require-reviewed
```

All five checked annotation JSON files have already been built.

## Evaluate Checked Annotations

After all five packet directories contain `annotation_checked.json`, run:

```bash
PYTHONPATH=src .venv/bin/python scripts/evaluate_sparse_view_annotations.py \
  --dataset configs/datasets/tum_rgbd_paper_subset.json \
  --results-root results/benchmark_tum_rgbd_paper_subset \
  --annotations-root results/benchmark_tum_rgbd_paper_subset/annotations \
  --output results/benchmark_tum_rgbd_paper_subset/sparse_view_checked_metrics.csv \
  --reference-view-count 10 \
  --packet-mode pseudo_reference \
  --annotation-file-name annotation_checked.json
```

Then export checked metric tables:

```bash
PYTHONPATH=src .venv/bin/python scripts/export_sparse_view_metric_tables.py \
  --metrics results/benchmark_tum_rgbd_paper_subset/sparse_view_checked_metrics.csv \
  --latex-output paper/tables/tum_rgbd_paper_subset_checked_results.tex \
  --markdown-output results/benchmark_tum_rgbd_paper_subset/sparse_view_checked_metrics.md \
  --aggregate-latex-output paper/tables/tum_rgbd_paper_subset_checked_by_view.tex \
  --aggregate-markdown-output results/benchmark_tum_rgbd_paper_subset/sparse_view_checked_by_view.md \
  --caption "TUM RGB-D paper-subset results against checked prediction-seeded annotations." \
  --aggregate-caption "Average checked-annotation results over the five-scene TUM RGB-D paper subset." \
  --label tab:tum_rgbd_paper_subset_checked_results \
  --aggregate-label tab:tum_rgbd_paper_subset_checked_by_view
```
