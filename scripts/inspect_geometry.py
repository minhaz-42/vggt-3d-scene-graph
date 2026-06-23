from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect saved VGGT geometry arrays.")
    parser.add_argument("geometry_npz", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with np.load(args.geometry_npz) as data:
        for key in sorted(data.files):
            array = data[key]
            print(f"{key}: shape={array.shape}, dtype={array.dtype}")


if __name__ == "__main__":
    main()
