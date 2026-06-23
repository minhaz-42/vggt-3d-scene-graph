from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a paper-ready qualitative scene graph montage.")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--view-count", type=int, default=10)
    parser.add_argument("--scene-id", action="append", default=[], help="Scene id to include. Repeat as needed.")
    parser.add_argument("--rgb-width", type=int, default=360)
    parser.add_argument("--graph-width", type=int, default=760)
    parser.add_argument("--panel-height", type=int, default=290)
    parser.add_argument("--padding", type=int, default=26)
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _short_scene(scene_id: str) -> str:
    return scene_id.removeprefix("tum_rgbd_").replace("_", " ")


def _fit_image(path: Path, size: tuple[int, int], *, fill: tuple[int, int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, fill)
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def _first_image_path(scene: dict[str, Any]) -> Path:
    scene_dir = Path(str(scene["scene_dir"]))
    images = scene.get("images", [])
    if not images:
        raise ValueError(f"Scene {scene.get('scene_id')} has no images in manifest.")
    return scene_dir / str(images[0])


def main() -> None:
    args = parse_args()
    manifest = _load_json(args.dataset)
    selected_scene_ids = set(args.scene_id)
    scenes = [
        scene
        for scene in manifest.get("scenes", [])
        if not selected_scene_ids or str(scene.get("scene_id")) in selected_scene_ids
    ]
    if selected_scene_ids:
        found = {str(scene.get("scene_id")) for scene in scenes}
        missing = sorted(selected_scene_ids - found)
        if missing:
            raise ValueError(f"Scene ids not found in manifest: {missing}")
    if not scenes:
        raise SystemExit("No scenes selected.")

    padding = args.padding
    header_height = 78
    label_height = 34
    row_height = args.panel_height + label_height + padding
    width = args.rgb_width + args.graph_width + padding * 3
    height = header_height + row_height * len(scenes) + padding
    background = (247, 248, 250)
    panel = (255, 255, 255)
    ink = (24, 32, 42)
    muted = (91, 103, 115)
    line = (214, 221, 228)

    canvas = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(canvas)
    title_font = _font(28, bold=True)
    subtitle_font = _font(17)
    label_font = _font(17, bold=True)
    small_font = _font(14)

    draw.text((padding, 20), "TUM RGB-D sparse-view qualitative results", fill=ink, font=title_font)
    draw.text(
        (padding, 52),
        "Each row shows one input RGB frame and the corresponding 10-view fused 3D scene graph.",
        fill=muted,
        font=subtitle_font,
    )

    y = header_height
    rgb_size = (args.rgb_width, args.panel_height)
    graph_size = (args.graph_width, args.panel_height)
    for scene in scenes:
        scene_id = str(scene["scene_id"])
        rgb_path = _first_image_path(scene)
        graph_path = args.results_root / scene_id / f"views_{args.view_count:02d}" / "scene_graph.png"
        if not rgb_path.exists():
            raise FileNotFoundError(f"Missing RGB image: {rgb_path}")
        if not graph_path.exists():
            raise FileNotFoundError(f"Missing scene graph figure: {graph_path}")

        row_top = y
        draw.rounded_rectangle(
            (padding, row_top, width - padding, row_top + args.panel_height + label_height),
            radius=8,
            fill=panel,
            outline=line,
            width=1,
        )
        draw.text((padding * 2, row_top + 9), _short_scene(scene_id), fill=ink, font=label_font)
        draw.text((padding * 2 + args.rgb_width + padding, row_top + 9), f"{args.view_count}-view scene graph", fill=ink, font=label_font)

        rgb_image = _fit_image(rgb_path, rgb_size, fill=(18, 22, 28))
        graph_image = _fit_image(graph_path, graph_size, fill=(255, 255, 255))
        rgb_xy = (padding * 2, row_top + label_height)
        graph_xy = (padding * 2 + args.rgb_width + padding, row_top + label_height)
        canvas.paste(rgb_image, rgb_xy)
        canvas.paste(graph_image, graph_xy)
        draw.rectangle(
            (rgb_xy[0], rgb_xy[1], rgb_xy[0] + rgb_size[0], rgb_xy[1] + rgb_size[1]),
            outline=line,
            width=1,
        )
        draw.rectangle(
            (graph_xy[0], graph_xy[1], graph_xy[0] + graph_size[0], graph_xy[1] + graph_size[1]),
            outline=line,
            width=1,
        )
        draw.text((rgb_xy[0] + 8, rgb_xy[1] + 8), "RGB input", fill=(245, 247, 250), font=small_font)
        y += row_height

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output)
    print(f"Wrote qualitative figure to {args.output}")


if __name__ == "__main__":
    main()
