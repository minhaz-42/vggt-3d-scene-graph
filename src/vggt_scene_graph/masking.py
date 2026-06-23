from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def encode_binary_mask_rle(mask: np.ndarray) -> dict[str, Any]:
    """Encode a binary mask as simple row-major run lengths."""

    binary = np.asarray(mask, dtype=np.uint8) > 0
    flat = binary.astype(np.uint8).reshape(-1)
    if flat.size == 0:
        counts: list[int] = []
    else:
        change_indices = np.flatnonzero(flat[1:] != flat[:-1]) + 1
        run_starts = np.concatenate([np.array([0]), change_indices])
        run_ends = np.concatenate([change_indices, np.array([flat.size])])
        counts = (run_ends - run_starts).astype(int).tolist()
        if int(flat[0]) == 1:
            counts = [0] + counts
    return {
        "size": [int(binary.shape[0]), int(binary.shape[1])],
        "counts": counts,
        "order": "C",
    }


def decode_binary_mask_rle(payload: dict[str, Any]) -> np.ndarray:
    height, width = int(payload["size"][0]), int(payload["size"][1])
    counts = [int(value) for value in payload["counts"]]
    values = []
    current = 0
    for count in counts:
        if count:
            values.append(np.full(count, current, dtype=np.uint8))
        current = 1 - current
    if values:
        flat = np.concatenate(values)
    else:
        flat = np.zeros(height * width, dtype=np.uint8)
    if flat.size != height * width:
        raise ValueError(f"RLE size mismatch: decoded {flat.size}, expected {height * width}.")
    return flat.reshape((height, width)).astype(bool)


def resize_mask(mask: np.ndarray, target_size_wh: tuple[int, int]) -> np.ndarray:
    target_w, target_h = target_size_wh
    resized = cv2.resize(mask.astype(np.uint8), (target_w, target_h), interpolation=cv2.INTER_NEAREST)
    return resized > 0
