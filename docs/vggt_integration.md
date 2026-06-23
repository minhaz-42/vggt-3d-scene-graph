# VGGT Integration

This project treats VGGT as a frozen external geometry backbone.

## Install VGGT

From inside the project environment:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install git+https://github.com/facebookresearch/vggt.git
```

The first real inference call will download the pretrained weights for:

```text
facebook/VGGT-1B
```

That download can be large. If local inference is too slow or memory-heavy on Apple Silicon, use a smaller released VGGT checkpoint if available, or run this stage on Colab/cloud and bring the saved `.npz` geometry outputs back to the Mac.

## Run Geometry Extraction

Use the current TUM RGB-D benchmark frames, then run:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_vggt_geometry.py \
  --scene-dir data/benchmark/tum_rgbd_freiburg1_room/images \
  --output results/benchmark_tum_rgbd/tum_rgbd_freiburg1_room/views_03/vggt_geometry.npz \
  --image-name frame_000001.png \
  --image-name frame_000002.png \
  --image-name frame_000003.png \
  --device auto
```

For a larger sparse-view run, include more `--image-name` values from
`frame_000001.png` through `frame_000010.png`.

The script writes:

- `vggt_geometry.npz` with raw VGGT NumPy arrays,
- `vggt_geometry.json` with metadata, array keys, and shapes.

When VGGT returns `pose_enc` and normalized `images`, the project adapter also decodes
camera matrices with VGGT's own `pose_encoding_to_extri_intri` utility and saves:

- `camera_extrinsics` with shape `[batch, views, 3, 4]`,
- `camera_intrinsics` with shape `[batch, views, 3, 3]`.

Inspect the saved arrays:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_geometry.py \
  results/benchmark_tum_rgbd/tum_rgbd_freiburg1_room/views_03/vggt_geometry.npz
```

## Why Save Raw Outputs First

VGGT is a fast-moving project and output key names may change. Saving all raw arrays lets us inspect actual outputs before writing fragile downstream object-lifting code.

The next step after successful extraction is:

1. lift 2D SAM or local proposal masks into `world_points`,
2. aggregate CLIP/DINO features for lifted object candidates,
3. build object nodes for the graph module.
