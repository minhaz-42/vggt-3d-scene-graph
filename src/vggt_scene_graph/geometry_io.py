from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def list_scene_images(scene_dir: Path, limit: int | None = None) -> list[Path]:
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    image_paths: list[Path] = []
    for extension in extensions:
        image_paths.extend(scene_dir.glob(extension))

    image_paths = sorted(image_paths)
    if limit is not None:
        return image_paths[:limit]
    return image_paths


def save_geometry_npz(
    output_npz: Path,
    arrays: dict[str, np.ndarray],
    image_paths: list[Path],
    metadata: dict[str, object] | None = None,
) -> None:
    output_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_npz, **arrays)

    meta_payload = {
        "image_paths": [str(path) for path in image_paths],
        "array_keys": sorted(arrays),
        "array_shapes": {key: list(value.shape) for key, value in arrays.items()},
    }
    if metadata:
        meta_payload.update(metadata)

    output_npz.with_suffix(".json").write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")


def load_geometry_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        return {key: data[key] for key in data.files}


def load_geometry_metadata(path: Path) -> dict[str, object]:
    metadata_path = path.with_suffix(".json")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing geometry metadata file: {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))
