from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np


def select_torch_device(preferred: str = "auto") -> str:
    """Pick a practical PyTorch device for local VGGT inference."""

    import torch

    if preferred != "auto":
        return preferred
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _as_numpy(value: Any) -> Any:
    """Recursively convert tensors inside VGGT outputs to NumPy arrays."""

    try:
        import torch
    except ImportError:
        torch = None

    if torch is not None and isinstance(value, torch.Tensor):
        return value.detach().cpu().float().numpy()
    if isinstance(value, dict):
        return {key: _as_numpy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_as_numpy(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_as_numpy(item) for item in value)
    return value


def _flatten_arrays(prefix: str, value: Any, output: dict[str, np.ndarray]) -> None:
    if isinstance(value, np.ndarray):
        output[prefix] = value
        return

    if isinstance(value, dict):
        for key, item in value.items():
            _flatten_arrays(f"{prefix}.{key}" if prefix else str(key), item, output)
        return

    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _flatten_arrays(f"{prefix}.{index}" if prefix else str(index), item, output)


def _decode_pose_encoding(arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    pose_enc = arrays.get("pose_enc")
    images = arrays.get("images")
    if pose_enc is None or images is None or images.ndim < 5:
        return {}

    try:
        import torch
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
    except ImportError:
        return {}

    image_size_hw = (int(images.shape[-2]), int(images.shape[-1]))
    pose_tensor = torch.from_numpy(pose_enc)
    extrinsics, intrinsics = pose_encoding_to_extri_intri(pose_tensor, image_size_hw=image_size_hw)
    return {
        "camera_extrinsics": extrinsics.detach().cpu().float().numpy(),
        "camera_intrinsics": intrinsics.detach().cpu().float().numpy(),
    }


class VGGTRunner:
    """Thin wrapper around the official `facebookresearch/vggt` package."""

    def __init__(
        self,
        model_name: str = "facebook/VGGT-1B",
        device: str = "auto",
    ) -> None:
        self.model_name = model_name
        self.device = select_torch_device(device)
        self._model = None
        self._load_and_preprocess_images = None

    def load(self) -> None:
        try:
            import torch
            from vggt.models.vggt import VGGT
            from vggt.utils.load_fn import load_and_preprocess_images
        except ImportError as exc:
            raise RuntimeError(
                "VGGT is not installed. Install the official package first, for example: "
                "`pip install git+https://github.com/facebookresearch/vggt.git`."
            ) from exc

        self._model = VGGT.from_pretrained(self.model_name).to(self.device)
        self._model.eval()
        self._load_and_preprocess_images = load_and_preprocess_images

        # Store torch after import so inference can use it without a module-level dependency.
        self._torch = torch

    def run(self, image_paths: Sequence[Path | str]) -> dict[str, Any]:
        if not image_paths:
            raise ValueError("At least one image is required for VGGT inference.")
        if self._model is None or self._load_and_preprocess_images is None:
            self.load()

        torch = self._torch
        path_strings = [str(path) for path in image_paths]
        images = self._load_and_preprocess_images(path_strings).to(self.device)

        # VGGT expects a scene batch. The official helper commonly returns
        # [num_views, channels, height, width], so add batch when needed.
        if images.ndim == 4:
            images = images[None]

        with torch.inference_mode():
            predictions = self._model(images)

        return _as_numpy(predictions)

    def run_flat(self, image_paths: Sequence[Path | str]) -> dict[str, np.ndarray]:
        predictions = self.run(image_paths)
        arrays: dict[str, np.ndarray] = {}
        _flatten_arrays("", predictions, arrays)
        arrays.update(_decode_pose_encoding(arrays))
        return arrays
