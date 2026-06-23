# Benchmark Data Status

## Current Dataset

The four local sample photos were removed from `data/`. Current data lives in:

```text
data/benchmark/tum_rgbd_freiburg1_room/images/
```

The folder contains 10 RGB frames from the public TUM RGB-D `freiburg1_room` sequence:

- `frame_000001.png`
- `frame_000002.png`
- `frame_000003.png`
- `frame_000004.png`
- `frame_000005.png`
- `frame_000006.png`
- `frame_000007.png`
- `frame_000008.png`
- `frame_000009.png`
- `frame_000010.png`

Manifest:

```text
configs/datasets/tum_rgbd_freiburg1_room.json
```

## Completed Sparse-View Runs

Command:

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

Each view-count directory contains:

- `vggt_geometry.npz`
- `sam_proposals.json`
- `sam_clip_dinov2_features.json`
- `scene_graph.json`
- `scene_graph_labeled.json`
- `scene_graph.png`

Current results:

| Views | Candidates | Fused Objects | Multi-View Objects | Relations | Labeled Nodes | Mean Uncertainty |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | 58 | 27 | 18 | 466 | 27 | 0.014525 |
| 5 | 98 | 32 | 24 | 628 | 32 | 0.014585 |
| 8 | 158 | 30 | 26 | 580 | 30 | 0.011999 |
| 10 | 198 | 32 | 28 | 636 | 32 | 0.011513 |

## Next Runs

## Annotation Packet

Current pseudo-reference packet:

```text
results/benchmark_tum_rgbd/annotations/tum_rgbd_freiburg1_room_pseudo_from_10view/
```

It contains:

- `node_review.csv`
- `relation_review.csv`
- `annotation_draft.json`

Pseudo-reference consistency against the 10-view predicted graph:

| Views | Object F1 | Relation Triplet F1 |
| --- | --- | --- |
| 3 | 0.915254 | 0.791289 |
| 5 | 0.968750 | 0.876582 |
| 8 | 0.967742 | 0.894737 |
| 10 | 1.000000 | 1.000000 |

These are not ground-truth scores. They are a consistency check until manual or dataset
annotations are added.

## Next Runs

Add more benchmark scenes under `data/benchmark/scenes/`, then run the same 3/5/8/10
view protocol across the expanded manifest.
