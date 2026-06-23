# Mac Feasibility

This project is ambitious, but it can start on Apple Silicon if the heavy models are frozen.

## What To Freeze

Freeze:

- VGGT,
- SAM or SAM2,
- CLIP,
- DINOv2.

Train or tune only:

- graph fusion weights,
- uncertainty calibration,
- relation classifier.

## Practical Device Strategy

Use:

- CPU/MPS for small tensor processing,
- precomputed features,
- small scene subsets,
- small graph modules.

Avoid:

- training VGGT,
- training SAM,
- full dataset-scale Gaussian Splatting at the beginning,
- large 3D foundation model fine-tuning.

## Suggested Environment

Use Python 3.11 or 3.12.

Base dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "numpy<2" scipy pandas scikit-learn networkx pydantic pillow "opencv-python<4.12" matplotlib tqdm
pip install torch torchvision
```

Optional later:

```bash
pip install open3d trimesh plotly
```

VGGT, SAM/SAM2, and CLIP should be integrated after the local scaffold is stable.

Current project environment note:

- The project venv was created with Python 3.11.
- VGGT imports successfully.
- PyTorch was installed successfully.
- On this machine, `torch.backends.mps.is_built()` is true but `torch.backends.mps.is_available()` is false, so the current VGGT adapter falls back to CPU.

## First Dataset Strategy

Start with:

- your own 3-5 images of a desk/room scene, or
- a tiny accessible subset from ARKitScenes.

Then move to:

- ScanNet++,
- HM3D/Matterport if access is approved.

## Why This Is Still Publishable

The Mac is for development and small experiments. Final large-scale experiments can be run later on:

- a university GPU,
- Google Colab,
- Kaggle,
- rented cloud GPU.

The important research contribution is the method and sparse-view protocol, not that everything was trained locally.
