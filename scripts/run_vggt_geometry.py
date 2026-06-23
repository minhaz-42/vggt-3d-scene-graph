from __future__ import annotations

import argparse
from pathlib import Path

from vggt_scene_graph.backbones import VGGTRunner
from vggt_scene_graph.geometry_io import list_scene_images, save_geometry_npz


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VGGT geometry inference on a sparse-view scene.")
    parser.add_argument("--scene-dir", type=Path, required=True, help="Directory containing RGB scene images.")
    parser.add_argument("--output", type=Path, default=Path("results/vggt_geometry.npz"))
    parser.add_argument("--max-views", type=int, default=5)
    parser.add_argument(
        "--image-name",
        action="append",
        default=[],
        help=(
            "Specific image filename to include. Pass multiple times to run a selected subset, "
            "for example --image-name frame_000001.png --image-name frame_000002.png."
        ),
    )
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--model-name", default="facebook/VGGT-1B")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.image_name:
        image_paths = [args.scene_dir / image_name for image_name in args.image_name]
        missing_paths = [path for path in image_paths if not path.exists()]
        if missing_paths:
            missing = ", ".join(str(path) for path in missing_paths)
            raise SystemExit(f"Selected image files do not exist: {missing}")
    else:
        image_paths = list_scene_images(args.scene_dir, limit=args.max_views)

    if not image_paths:
        raise SystemExit(f"No images found in {args.scene_dir}")

    runner = VGGTRunner(model_name=args.model_name, device=args.device)
    arrays = runner.run_flat(image_paths)
    save_geometry_npz(
        args.output,
        arrays,
        image_paths,
        metadata={
            "backend": "vggt",
            "model_name": args.model_name,
            "device": runner.device,
            "num_views": len(image_paths),
        },
    )
    print(f"Saved VGGT geometry arrays to {args.output}")
    print(f"Saved metadata to {args.output.with_suffix('.json')}")


if __name__ == "__main__":
    main()
