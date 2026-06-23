from __future__ import annotations

import importlib.metadata
import platform

import torch

from vggt_scene_graph.backbones import select_torch_device


def version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def main() -> None:
    print(f"platform: {platform.platform()}")
    print(f"machine: {platform.machine()}")
    print(f"torch: {torch.__version__}")
    print(f"torch mps built: {torch.backends.mps.is_built()}")
    print(f"torch mps available: {torch.backends.mps.is_available()}")
    print(f"selected device: {select_torch_device()}")
    print(f"vggt: {version('vggt')}")
    print(f"numpy: {version('numpy')}")
    print(f"opencv-python: {version('opencv-python')}")


if __name__ == "__main__":
    main()
