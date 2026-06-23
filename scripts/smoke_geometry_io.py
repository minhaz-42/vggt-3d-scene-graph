from __future__ import annotations

from pathlib import Path

import numpy as np

from vggt_scene_graph.geometry_io import load_geometry_npz, save_geometry_npz


def main() -> None:
    output = Path("results/smoke_geometry.npz")
    arrays = {
        "depth": np.zeros((1, 2, 4, 4), dtype=np.float32),
        "confidence": np.ones((1, 2, 4, 4), dtype=np.float32),
    }
    image_paths = [Path("frame_000001.png"), Path("frame_000002.png")]
    save_geometry_npz(output, arrays, image_paths, metadata={"backend": "smoke"})
    loaded = load_geometry_npz(output)
    assert sorted(loaded) == ["confidence", "depth"]
    assert loaded["depth"].shape == (1, 2, 4, 4)
    print(f"Smoke geometry IO passed: {output}")


if __name__ == "__main__":
    main()
