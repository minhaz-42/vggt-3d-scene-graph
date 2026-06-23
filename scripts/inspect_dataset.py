from __future__ import annotations

import argparse
import json
from pathlib import Path

from vggt_scene_graph.datasets import load_dataset_manifest, manifest_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a dataset manifest.")
    parser.add_argument("--dataset", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = load_dataset_manifest(args.dataset)
    print(json.dumps(manifest_summary(manifest), indent=2))


if __name__ == "__main__":
    main()
