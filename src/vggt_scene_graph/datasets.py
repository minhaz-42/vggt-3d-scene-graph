from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .geometry_io import list_scene_images


@dataclass(slots=True)
class SceneRecord:
    scene_id: str
    scene_dir: Path
    image_paths: list[Path]
    split: str = "prototype"
    geometry_path: Path | None = None
    proposals_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DatasetManifest:
    name: str
    version: str
    root: Path
    scenes: list[SceneRecord]
    sparse_view_counts: list[int] = field(default_factory=lambda: [2, 3, 5, 8, 10])
    metadata: dict[str, Any] = field(default_factory=dict)


def _resolve_path(root: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def _scene_from_payload(root: Path, payload: dict[str, Any]) -> SceneRecord:
    scene_dir = _resolve_path(root, payload.get("scene_dir"))
    if scene_dir is None:
        raise ValueError("Each scene needs a scene_dir.")

    image_values = payload.get("images")
    if image_values:
        image_paths = []
        for image_value in image_values:
            image_path = Path(image_value)
            image_paths.append(image_path if image_path.is_absolute() else scene_dir / image_path)
    else:
        image_paths = list_scene_images(scene_dir)

    return SceneRecord(
        scene_id=str(payload["scene_id"]),
        scene_dir=scene_dir,
        image_paths=image_paths,
        split=str(payload.get("split", "prototype")),
        geometry_path=_resolve_path(root, payload.get("geometry_path")),
        proposals_path=_resolve_path(root, payload.get("proposals_path")),
        metadata=dict(payload.get("metadata", {})),
    )


def load_dataset_manifest(path: Path) -> DatasetManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    root = _resolve_path(path.parent, payload.get("root")) or path.parent
    scenes = [_scene_from_payload(root, scene_payload) for scene_payload in payload.get("scenes", [])]
    return DatasetManifest(
        name=str(payload["name"]),
        version=str(payload.get("version", "0.1")),
        root=root,
        scenes=scenes,
        sparse_view_counts=[int(value) for value in payload.get("sparse_view_counts", [2, 3, 5, 8, 10])],
        metadata=dict(payload.get("metadata", {})),
    )


def get_scene(manifest: DatasetManifest, scene_id: str) -> SceneRecord:
    for scene in manifest.scenes:
        if scene.scene_id == scene_id:
            return scene
    raise KeyError(f"Scene {scene_id!r} not found in dataset manifest {manifest.name!r}.")


def sparse_view_split(image_paths: list[Path], view_count: int) -> list[Path]:
    if view_count <= 0:
        raise ValueError("view_count must be positive.")
    return image_paths[: min(view_count, len(image_paths))]


def manifest_summary(manifest: DatasetManifest) -> dict[str, Any]:
    return {
        "name": manifest.name,
        "version": manifest.version,
        "root": str(manifest.root),
        "num_scenes": len(manifest.scenes),
        "sparse_view_counts": manifest.sparse_view_counts,
        "scenes": [
            {
                "scene_id": scene.scene_id,
                "split": scene.split,
                "scene_dir": str(scene.scene_dir),
                "num_images": len(scene.image_paths),
                "geometry_path": str(scene.geometry_path) if scene.geometry_path else None,
                "proposals_path": str(scene.proposals_path) if scene.proposals_path else None,
            }
            for scene in manifest.scenes
        ],
    }
