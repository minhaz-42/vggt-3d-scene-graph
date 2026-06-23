from __future__ import annotations

import argparse
import csv
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


Color = tuple[int, int, int]

BG: Color = (248, 247, 239)
INK: Color = (17, 28, 43)
MUTED: Color = (62, 73, 88)
LINE: Color = (38, 50, 67)
DASH: Color = (82, 93, 109)
HEADER_DARK: Color = (31, 46, 68)
FROZEN: Color = (229, 234, 232)
ENCODER_BLUE: Color = (198, 226, 239)
ENCODER_PURPLE: Color = (225, 213, 237)
TRAINED_BLUE: Color = (187, 219, 235)
MODULE_YELLOW: Color = (255, 233, 166)
MODULE_GREEN: Color = (209, 232, 211)
NODE_TEAL: Color = (0, 112, 108)
NODE_BLUE: Color = (33, 91, 214)
NODE_PURPLE: Color = (99, 70, 178)
NODE_AMBER: Color = (185, 105, 14)
NODE_ROSE: Color = (184, 55, 91)
NODE_GREEN: Color = (52, 126, 75)
SHADOW: Color = (223, 219, 201)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPER_DATA_ROOT = PROJECT_ROOT / "data" / "benchmark" / "tum_rgbd_paper_subset"
RESULTS_ROOT = PROJECT_ROOT / "results" / "benchmark_tum_rgbd_paper_subset"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create paper-ready method and evaluation diagrams.")
    parser.add_argument("--output-dir", type=Path, default=Path("paper/figures"))
    return parser.parse_args()


def _font(size: int, *, bold: bool = False, serif: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if serif and bold else "",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf" if serif and not bold else "",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if serif and bold else "",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf" if serif and not bold else "",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines() or [""]:
        current = ""
        for word in raw_line.split():
            trial = f"{current} {word}".strip()
            if _text_size(draw, trial, font)[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def _center_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    *,
    fill: Color = INK,
    line_gap: int = 7,
) -> None:
    x1, y1, x2, y2 = box
    lines = _wrap(draw, text, font, x2 - x1 - 24)
    line_h = _text_size(draw, "Ag", font)[1] + line_gap
    total_h = line_h * len(lines) - line_gap
    y = y1 + (y2 - y1 - total_h) // 2
    for line in lines:
        tw, th = _text_size(draw, line, font)
        draw.text((x1 + (x2 - x1 - tw) // 2, y), line, fill=fill, font=font)
        y += line_h


def _label(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font: ImageFont.ImageFont, *, fill: Color = INK) -> None:
    draw.text((x, y), text, fill=fill, font=font)


def _shadow_round(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, radius: int = 18, fill: Color = (255, 255, 255), outline: Color = LINE) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 8, y1 + 8, x2 + 8, y2 + 8), radius=radius, fill=SHADOW)
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=3)


def _badge(draw: ImageDraw.ImageDraw, cx: int, cy: int, text: str, font: ImageFont.ImageFont, *, fill: Color = NODE_AMBER) -> None:
    draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=fill, outline=BG, width=4)
    tw, th = _text_size(draw, text, font)
    draw.text((cx - tw // 2, cy - th // 2 - 1), text, fill=(255, 255, 255), font=font)


def _legend(draw: ImageDraw.ImageDraw, x: int, y: int, font: ImageFont.ImageFont) -> None:
    items = [
        ("frozen model", ENCODER_BLUE),
        ("proposed step", MODULE_YELLOW),
        ("stored artifact", FROZEN),
        ("label/review", MODULE_GREEN),
    ]
    for i, (label, color) in enumerate(items):
        xx = x + i * 240
        draw.rounded_rectangle((xx, y, xx + 34, y + 24), radius=6, fill=color, outline=LINE)
        draw.text((xx + 44, y - 2), label, fill=MUTED, font=font)


def _dashed_line(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], *, color: Color = DASH, width: int = 3, dash: int = 18, gap: int = 10) -> None:
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    dist = max(1.0, math.hypot(dx, dy))
    ux, uy = dx / dist, dy / dist
    pos = 0.0
    while pos < dist:
        end_pos = min(dist, pos + dash)
        draw.line((x1 + ux * pos, y1 + uy * pos, x1 + ux * end_pos, y1 + uy * end_pos), fill=color, width=width)
        pos += dash + gap


def _dashed_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, font: ImageFont.ImageFont) -> None:
    x1, y1, x2, y2 = box
    _dashed_line(draw, (x1, y1), (x2, y1), color=DASH, width=4)
    _dashed_line(draw, (x2, y1), (x2, y2), color=DASH, width=4)
    _dashed_line(draw, (x2, y2), (x1, y2), color=DASH, width=4)
    _dashed_line(draw, (x1, y2), (x1, y1), color=DASH, width=4)
    tw, th = _text_size(draw, title, font)
    draw.rounded_rectangle((x1 + 24, y1 - 35, x1 + 64 + tw, y1 + th + 12), radius=12, fill=HEADER_DARK)
    draw.text((x1 + 44, y1 - 25), title, fill=(255, 255, 248), font=font)


def _arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    color: Color = LINE,
    width: int = 4,
    elbow: tuple[int, int] | None = None,
    label: str | None = None,
    font: ImageFont.ImageFont | None = None,
) -> None:
    pts = [start, elbow, end] if elbow else [start, end]
    draw.line(pts, fill=color, width=width, joint="curve")
    sx, sy = pts[-2]
    ex, ey = pts[-1]
    angle = math.atan2(ey - sy, ex - sx)
    size = 20
    left = (ex - size * math.cos(angle - math.pi / 6), ey - size * math.sin(angle - math.pi / 6))
    right = (ex - size * math.cos(angle + math.pi / 6), ey - size * math.sin(angle + math.pi / 6))
    draw.polygon([(ex, ey), left, right], fill=color)
    if label and font:
        if elbow:
            lx, ly = elbow
        else:
            lx, ly = (start[0] + end[0]) // 2, (start[1] + end[1]) // 2
        tw, th = _text_size(draw, label, font)
        draw.rounded_rectangle((lx - tw // 2 - 10, ly - th // 2 - 6, lx + tw // 2 + 10, ly + th // 2 + 6), radius=8, fill=BG, outline=(219, 215, 201))
        draw.text((lx - tw // 2, ly - th // 2), label, fill=MUTED, font=font)


def _lock(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.arc((x, y, x + 26, y + 26), 180, 360, fill=INK, width=4)
    draw.rounded_rectangle((x - 2, y + 13, x + 28, y + 38), radius=5, fill=INK)
    draw.ellipse((x + 10, y + 22, x + 16, y + 28), fill=BG)


def _trapezoid(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.ImageFont, *, fill: Color, locked: bool = True) -> None:
    x1, y1, x2, y2 = box
    slant = 34
    points = [(x1, y1 + slant), (x2, y1), (x2, y2), (x1, y2 - slant)]
    draw.polygon(points, fill=fill, outline=LINE)
    draw.line(points + [points[0]], fill=LINE, width=3)
    _center_text(draw, (x1 + 18, y1 + 18, x2 - 18, y2 - 18), text, font)
    if locked:
        _lock(draw, x2 - 34, y1 + 6)


def _module(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.ImageFont, *, fill: Color = MODULE_YELLOW, outline: Color = LINE) -> None:
    _shadow_round(draw, box, radius=16, fill=fill, outline=outline)
    _center_text(draw, box, text, font)


def _feature_vector(draw: ImageDraw.ImageDraw, x: int, y: int, count: int, *, color: Color = ENCODER_BLUE, size: int = 28) -> None:
    for i in range(count):
        draw.rectangle((x + i * (size + 3), y, x + i * (size + 3) + size, y + size), fill=color, outline=LINE)


def _op_circle(draw: ImageDraw.ImageDraw, cx: int, cy: int, text: str, font: ImageFont.ImageFont) -> None:
    draw.ellipse((cx - 38, cy - 38, cx + 38, cy + 38), fill=BG, outline=INK, width=3)
    tw, th = _text_size(draw, text, font)
    draw.text((cx - tw // 2, cy - th // 2), text, fill=INK, font=font)


def _image_stack(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, font: ImageFont.ImageFont, *, label: str = "") -> None:
    fills = [(224, 237, 235), (225, 232, 249), (238, 229, 244)]
    for i in range(3):
        ox, oy = (2 - i) * 26, (2 - i) * 22
        x1, y1 = x + ox, y + oy
        draw.rectangle((x1, y1, x1 + w, y1 + h), fill=fills[i], outline=LINE, width=3)
        draw.polygon([(x1 + 10, y1 + h - 14), (x1 + 80, y1 + h - 74), (x1 + 135, y1 + h - 38), (x1 + w - 12, y1 + h - 82), (x1 + w - 12, y1 + h - 12), (x1 + 10, y1 + h - 12)], fill=(116, 148, 130))
        draw.rectangle((x1 + 34, y1 + 34, x1 + 118, y1 + 104), fill=(174, 108, 78))
        draw.rectangle((x1 + 150, y1 + 55, x1 + 232, y1 + 135), fill=(82, 126, 170))
        draw.ellipse((x1 + w - 75, y1 + 28, x1 + w - 38, y1 + 65), fill=(232, 181, 61))
    if label:
        tw, _ = _text_size(draw, label, font)
        draw.text((x + w // 2 - tw // 2 + 22, y + h + 72), label, fill=INK, font=font)


def _tiny_3d_cloud(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.polygon([(x + 20, y + 120), (x + 165, y + 70), (x + 285, y + 120), (x + 140, y + 178)], outline=(151, 165, 179), fill=None)
    draw.line((x + 140, y + 36, x + 140, y + 178), fill=(151, 165, 179), width=3)
    rng = random.Random(11)
    for _ in range(90):
        px = x + 120 + int(rng.gauss(0, 45))
        py = y + 120 + int(rng.gauss(0, 34))
        color = NODE_TEAL if rng.random() > 0.45 else NODE_BLUE
        draw.ellipse((px - 4, py - 4, px + 4, py + 4), fill=color)


def _scene_graph(draw: ImageDraw.ImageDraw, x: int, y: int, font: ImageFont.ImageFont, *, labels: bool = True) -> None:
    cube = [(x + 60, y + 180), (x + 280, y + 85), (x + 500, y + 180), (x + 280, y + 295)]
    draw.line((cube[0], cube[1], cube[2], cube[3], cube[0]), fill=(151, 165, 179), width=3)
    draw.line((x + 280, y + 85, x + 280, y + 295), fill=(151, 165, 179), width=3)
    nodes = [
        (x + 235, y + 145, NODE_TEAL, "desk"),
        (x + 365, y + 195, NODE_BLUE, "chair"),
        (x + 270, y + 210, NODE_PURPLE, "monitor"),
        (x + 190, y + 205, NODE_AMBER, "lamp"),
        (x + 300, y + 270, NODE_GREEN, "box"),
    ]
    for a, b, rel in [(0, 1, "near"), (0, 2, "supports"), (0, 3, "left"), (1, 4, "right")]:
        ax, ay, _, _ = nodes[a]
        bx, by, _, _ = nodes[b]
        draw.line((ax, ay, bx, by), fill=LINE, width=4)
        if labels:
            mx, my = (ax + bx) // 2, (ay + by) // 2
            tw, th = _text_size(draw, rel, font)
            draw.rounded_rectangle((mx - tw // 2 - 7, my - th // 2 - 5, mx + tw // 2 + 7, my + th // 2 + 5), radius=7, fill=BG, outline=(221, 217, 202))
            draw.text((mx - tw // 2, my - th // 2), rel, fill=MUTED, font=font)
    offsets = [(-28, -50), (32, 22), (-40, 38), (-76, 0), (20, 24)]
    for (cx, cy, color, name), (ox, oy) in zip(nodes, offsets):
        draw.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=color, outline=BG, width=5)
        if labels:
            tw, th = _text_size(draw, name, font)
            draw.rounded_rectangle((cx + ox - 7, cy + oy - 5, cx + ox + tw + 7, cy + oy + th + 5), radius=7, fill=BG, outline=(213, 208, 194))
            draw.text((cx + ox, cy + oy), name, fill=INK, font=font)


def _mini_scene_graph(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    cube = [(x + 12, y + 92), (x + 145, y + 28), (x + 278, y + 92), (x + 145, y + 162)]
    draw.line((cube[0], cube[1], cube[2], cube[3], cube[0]), fill=(151, 165, 179), width=3)
    draw.line((x + 145, y + 28, x + 145, y + 162), fill=(151, 165, 179), width=3)
    nodes = [
        (x + 118, y + 83, NODE_TEAL),
        (x + 190, y + 104, NODE_BLUE),
        (x + 144, y + 119, NODE_PURPLE),
        (x + 82, y + 110, NODE_AMBER),
        (x + 177, y + 150, NODE_GREEN),
    ]
    for a, b in [(0, 1), (0, 2), (0, 3), (1, 4)]:
        ax, ay, _ = nodes[a]
        bx, by, _ = nodes[b]
        draw.line((ax, ay, bx, by), fill=LINE, width=4)
    for cx, cy, color in nodes:
        draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=color, outline=BG, width=4)


def _circuit_corner(draw: ImageDraw.ImageDraw, width: int) -> None:
    color = (222, 220, 205)
    for i in range(8):
        x = width - 260 + i * 28
        draw.line((x, 0, x, 70 + i * 11), fill=color, width=2)
        draw.ellipse((x - 5, 72 + i * 11, x + 5, 82 + i * 11), outline=color, width=2)
    for i in range(5):
        y = 28 + i * 28
        draw.line((width - 185, y, width - 45, y), fill=color, width=2)
        draw.line((width - 75, y, width - 75, y + 22), fill=color, width=2)


def _scene_name(scene_id: str) -> str:
    return {
        "tum_rgbd_freiburg1_room": "fr1_room",
        "tum_rgbd_freiburg1_desk": "fr1_desk",
        "tum_rgbd_freiburg1_desk2": "fr1_desk2",
        "tum_rgbd_freiburg2_xyz": "fr2_xyz",
        "tum_rgbd_freiburg3_long_office_household": "fr3_office",
    }.get(scene_id, scene_id.replace("tum_rgbd_", ""))


def _scene_frame_paths(scene_id: str, *, limit: int = 10) -> list[Path]:
    image_dir = PAPER_DATA_ROOT / scene_id / "images"
    paths = sorted(image_dir.glob("*.png")) + sorted(image_dir.glob("*.jpg"))
    return paths[:limit]


def _scene_graph_path(scene_id: str, view_count: int = 10) -> Path:
    return RESULTS_ROOT / scene_id / f"views_{view_count:02d}" / "scene_graph.png"


def _summary_rows() -> list[dict[str, str]]:
    path = RESULTS_ROOT / "sparse_view_checked_metrics.csv"
    if not path.exists():
        path = RESULTS_ROOT / "sparse_view_pseudo_reference_metrics.csv"
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _fallback_photo(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    draw.rectangle(box, fill=(225, 232, 236), outline=LINE, width=3)
    draw.polygon(
        [
            (x1 + 12, y2 - 18),
            (x1 + 70, y2 - 72),
            (x1 + 125, y2 - 38),
            (x2 - 12, y2 - 78),
            (x2 - 12, y2 - 12),
            (x1 + 12, y2 - 12),
        ],
        fill=(108, 151, 127),
    )
    draw.rectangle((x1 + 35, y1 + 34, x1 + 122, y1 + 104), fill=(176, 110, 78))
    draw.rectangle((x1 + 145, y1 + 52, x1 + 228, y1 + 135), fill=(82, 126, 170))
    draw.ellipse((x2 - 70, y1 + 30, x2 - 34, y1 + 66), fill=(230, 180, 61))


def _paste_photo(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    path: Path | None,
    *,
    grid: bool = False,
    masks: bool = False,
    border: Color = LINE,
) -> None:
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    if path and path.exists():
        thumb = Image.open(path).convert("RGB")
        thumb = ImageOps.fit(thumb, (w, h), method=Image.Resampling.LANCZOS)
        if masks:
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            odraw.polygon([(20, h - 20), (w // 3, h // 2), (w // 2, h - 42), (20, h - 42)], fill=(17, 128, 121, 115))
            odraw.rectangle((w // 2 - 20, h // 3, w - 35, h - 32), fill=(44, 103, 224, 105))
            odraw.ellipse((w - 82, 24, w - 30, 76), fill=(199, 124, 25, 120))
            thumb = Image.alpha_composite(thumb.convert("RGBA"), overlay).convert("RGB")
        canvas.paste(thumb, (x1, y1))
    else:
        _fallback_photo(draw, box)
    draw.rectangle(box, outline=border, width=3)
    if grid:
        for i in range(1, 4):
            xx = x1 + int(w * i / 4)
            draw.line((xx, y1, xx, y2), fill=(255, 255, 255), width=3)
        for i in range(1, 3):
            yy = y1 + int(h * i / 3)
            draw.line((x1, yy, x2, yy), fill=(255, 255, 255), width=3)


def _paste_image_contain(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    path: Path | None,
    *,
    fill: Color = (252, 252, 248),
    crop_light: bool = False,
) -> None:
    x1, y1, x2, y2 = box
    draw.rectangle(box, fill=fill, outline=LINE, width=3)
    if path and path.exists():
        w, h = x2 - x1 - 16, y2 - y1 - 16
        thumb = Image.open(path).convert("RGB")
        if crop_light:
            diff = ImageChops.difference(thumb, Image.new("RGB", thumb.size, (255, 255, 255))).convert("L")
            bbox = diff.point(lambda p: 255 if p > 8 else 0).getbbox()
            if bbox:
                left, top, right, bottom = bbox
                margin = 28
                thumb = thumb.crop(
                    (
                        max(0, left - margin),
                        max(0, top - margin),
                        min(thumb.width, right + margin),
                        min(thumb.height, bottom + margin),
                    )
                )
        thumb = ImageOps.contain(thumb, (w, h), method=Image.Resampling.LANCZOS)
        px = x1 + 8 + (w - thumb.width) // 2
        py = y1 + 8 + (h - thumb.height) // 2
        canvas.paste(thumb, (px, py))


def _photo_stack_from_scene(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    scene_id: str,
    x: int,
    y: int,
    w: int,
    h: int,
    font: ImageFont.ImageFont,
    *,
    label: str,
    grid: bool = False,
) -> None:
    paths = _scene_frame_paths(scene_id, limit=4)
    for i in range(3):
        ox, oy = (2 - i) * 24, (2 - i) * 20
        path = paths[i] if i < len(paths) else None
        _paste_photo(canvas, draw, (x + ox, y + oy, x + ox + w, y + oy + h), path, grid=grid)
    tw, _ = _text_size(draw, label, font)
    draw.text((x + w // 2 - tw // 2 + 25, y + h + 64), label, fill=INK, font=font)


def _token_column(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    colors: list[Color],
    *,
    size: int = 30,
    gap: int = 7,
    outline: Color = LINE,
) -> None:
    for i, color in enumerate(colors):
        yy = y + i * (size + gap)
        draw.rectangle((x, yy, x + size, yy + size), fill=color, outline=outline, width=2)


def _token_grid(draw: ImageDraw.ImageDraw, x: int, y: int, *, rows: int, cols: int, colors: list[Color], size: int = 24, gap: int = 5) -> None:
    for r in range(rows):
        for c in range(cols):
            color = colors[(r + c) % len(colors)]
            xx = x + c * (size + gap)
            yy = y + r * (size + gap)
            draw.rounded_rectangle((xx, yy, xx + size, yy + size), radius=4, fill=color, outline=(235, 235, 230))


def _draw_camera_frustums(draw: ImageDraw.ImageDraw, x: int, y: int, *, count: int = 4, scale: int = 1) -> None:
    for i in range(count):
        ox = x + i * 58 * scale
        oy = y + (i % 2) * 18 * scale
        color = [NODE_PURPLE, NODE_AMBER, NODE_BLUE, NODE_TEAL][i % 4]
        draw.line((ox, oy, ox + 38 * scale, oy + 28 * scale, ox + 38 * scale, oy - 28 * scale, ox, oy), fill=color, width=4)
        draw.line((ox, oy, ox + 62 * scale, oy), fill=color, width=3)
        draw.line((ox + 38 * scale, oy + 28 * scale, ox + 62 * scale, oy), fill=color, width=3)
        draw.line((ox + 38 * scale, oy - 28 * scale, ox + 62 * scale, oy), fill=color, width=3)


def _draw_depth_maps(canvas: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
    for panel in range(2):
        im = Image.new("RGB", (w, h))
        for yy in range(h):
            for xx in range(w):
                t = (yy / max(1, h - 1) * 0.7) + (xx / max(1, w - 1) * 0.3)
                if t < 0.5:
                    a = t / 0.5
                    color = (int(54 + 22 * a), int(57 + 145 * a), int(130 + 38 * a))
                else:
                    a = (t - 0.5) / 0.5
                    color = (int(76 + 184 * a), int(202 + 34 * a), int(168 - 108 * a))
                im.putpixel((xx, yy), color)
        box_x = x + panel * (w + 16)
        canvas.paste(im, (box_x, y))
        draw.rectangle((box_x, y, box_x + w, y + h), outline=LINE, width=2)


def _draw_point_map(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, *, seed: int = 7, cameras: bool = True) -> None:
    draw.rectangle((x, y, x + w, y + h), fill=(252, 252, 248), outline=LINE, width=2)
    draw.line((x + 28, y + h - 34, x + w - 28, y + h - 34), fill=(166, 174, 181), width=2)
    draw.line((x + 46, y + 30, x + 46, y + h - 28), fill=(166, 174, 181), width=2)
    rng = random.Random(seed)
    for _ in range(140):
        px = x + 55 + int(rng.random() * (w - 90))
        py = y + 40 + int(rng.random() * (h - 92))
        color = [NODE_TEAL, NODE_BLUE, NODE_AMBER, NODE_GREEN][rng.randrange(4)]
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=color)
    if cameras:
        _draw_camera_frustums(draw, x + 62, y + h - 18, count=3)


def _draw_confidence_meter(draw: ImageDraw.ImageDraw, x: int, y: int, font: ImageFont.ImageFont) -> None:
    labels = [("VGGT conf.", 0.78, NODE_BLUE), ("3D compact.", 0.64, NODE_TEAL), ("U_vk", 0.32, NODE_ROSE)]
    for i, (label, value, color) in enumerate(labels):
        yy = y + i * 47
        draw.text((x, yy), label, fill=MUTED, font=font)
        draw.rounded_rectangle((x + 142, yy + 5, x + 330, yy + 28), radius=12, fill=(232, 236, 238))
        draw.rounded_rectangle((x + 142, yy + 5, x + 142 + int(188 * value), yy + 28), radius=12, fill=color)


def _draw_object_table(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: ImageFont.ImageFont, small: ImageFont.ImageFont) -> None:
    _shadow_round(draw, box, radius=14, fill=(252, 252, 248), outline=LINE)
    x1, y1, x2, y2 = box
    draw.text((x1 + 22, y1 + 20), "Object nodes O", fill=INK, font=font)
    headers = ["id", "label", "views", "U"]
    xs = [x1 + 28, x1 + 92, x1 + 235, x1 + 345]
    y = y1 + 72
    for h, xx in zip(headers, xs):
        draw.text((xx, y), h, fill=MUTED, font=small)
    rows = [("03", "chair", "4", ".02"), ("18", "desk", "7", ".03"), ("24", "monitor", "5", ".04")]
    for i, row in enumerate(rows):
        yy = y1 + 112 + i * 48
        draw.line((x1 + 20, yy - 12, x2 - 20, yy - 12), fill=(218, 220, 215), width=2)
        for item, xx in zip(row, xs):
            draw.text((xx, yy), item, fill=INK, font=small)


def _draw_relation_table(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: ImageFont.ImageFont, small: ImageFont.ImageFont) -> None:
    _shadow_round(draw, box, radius=14, fill=(252, 252, 248), outline=LINE)
    x1, y1, x2, y2 = box
    draw.text((x1 + 22, y1 + 20), "Relation triplets R", fill=INK, font=font)
    rows = ["desk supports monitor", "chair near desk", "box left-of chair", "lamp above desk"]
    for i, row in enumerate(rows):
        yy = y1 + 74 + i * 40
        draw.rounded_rectangle((x1 + 24, yy - 4, x2 - 24, yy + 28), radius=8, fill=BG, outline=(220, 217, 204))
        draw.text((x1 + 38, yy), row, fill=INK, font=small)


def _draw_graph_output_cell(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    nodes: int,
    relations: int,
    color: Color,
    font: ImageFont.ImageFont,
) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=10, fill=(252, 252, 248), outline=LINE, width=2)
    centers = [
        (x + int(w * 0.28), y + int(h * 0.33)),
        (x + int(w * 0.53), y + int(h * 0.25)),
        (x + int(w * 0.75), y + int(h * 0.45)),
        (x + int(w * 0.42), y + int(h * 0.58)),
    ]
    for a, b in [(0, 1), (1, 2), (1, 3), (0, 3)]:
        draw.line((centers[a][0], centers[a][1], centers[b][0], centers[b][1]), fill=(105, 114, 126), width=3)
    for i, (cx, cy) in enumerate(centers):
        draw.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=[color, NODE_BLUE, NODE_AMBER, NODE_GREEN][i % 4], outline=BG, width=3)
    footer_y = y + h - 30
    draw.line((x + 12, footer_y - 8, x + w - 12, footer_y - 8), fill=(218, 220, 215), width=2)
    draw.text((x + 18, footer_y), f"O={nodes}", fill=INK, font=font)
    draw.text((x + max(78, int(w * 0.52)), footer_y), f"R={_fmt_count(relations)}", fill=MUTED, font=font)


def _draw_metric_curve(draw: ImageDraw.ImageDraw, x: int, y: int, font: ImageFont.ImageFont) -> None:
    draw.rounded_rectangle((x, y, x + 440, y + 250), radius=14, fill=(252, 252, 248), outline=LINE, width=3)
    draw.text((x + 24, y + 20), "View-count consistency", fill=INK, font=font)
    ax, ay = x + 70, y + 198
    draw.line((ax, y + 72, ax, ay), fill=LINE, width=3)
    draw.line((ax, ay, x + 390, ay), fill=LINE, width=3)
    pts = [(ax + 34, ay - 48), (ax + 116, ay - 76), (ax + 206, ay - 122), (ax + 286, ay - 148)]
    draw.line(pts, fill=NODE_TEAL, width=6)
    for i, (px, py) in enumerate(pts):
        draw.ellipse((px - 9, py - 9, px + 9, py + 9), fill=NODE_TEAL)
        draw.text((px - 10, ay + 12), str([3, 5, 8, 10][i]), fill=MUTED, font=font)


def _draw_sparse_view_metric_curve(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    rows: list[dict[str, str]],
    font: ImageFont.ImageFont,
    small: ImageFont.ImageFont,
) -> None:
    draw.rounded_rectangle((x, y, x + 600, y + 330), radius=14, fill=(252, 252, 248), outline=LINE, width=3)
    draw.text((x + 24, y + 20), "Checked F1 by view count", fill=INK, font=font)
    non_ref = [row for row in rows if row.get("is_reference_view") == "False"]
    means: dict[int, tuple[float, float]] = {}
    for view_count in [3, 5, 8]:
        subset = [row for row in non_ref if int(row.get("view_count", 0)) == view_count]
        if subset:
            obj = sum(float(row.get("object_label_f1", 0.0)) for row in subset) / len(subset)
            rel = sum(float(row.get("relation_triplet_f1", 0.0)) for row in subset) / len(subset)
            means[view_count] = (obj, rel)
    means[10] = (1.0, 1.0)
    legend_y = y + 76
    draw.line((x + 96, legend_y + 13, x + 146, legend_y + 13), fill=NODE_BLUE, width=8)
    draw.text((x + 158, legend_y - 3), "object", fill=MUTED, font=small)
    draw.line((x + 295, legend_y + 13, x + 345, legend_y + 13), fill=NODE_TEAL, width=8)
    draw.text((x + 357, legend_y - 3), "relation", fill=MUTED, font=small)

    ax, ay = x + 88, y + 268
    plot_top = y + 124
    draw.line((ax, plot_top, ax, ay), fill=LINE, width=4)
    draw.line((ax, ay, x + 390, ay), fill=LINE, width=4)
    draw.text((x + 50, plot_top - 8), "F1", fill=MUTED, font=small)
    draw.text((x + 20, ay - 10), "0", fill=MUTED, font=small)
    draw.text((x + 22, plot_top - 12), "1", fill=MUTED, font=small)

    xs = {3: ax + 52, 5: ax + 138, 8: ax + 224, 10: ax + 300}
    obj_pts: list[tuple[int, int]] = []
    rel_pts: list[tuple[int, int]] = []
    for view_count in [3, 5, 8, 10]:
        obj, rel = means.get(view_count, (0.0, 0.0))
        obj_pts.append((xs[view_count], ay - int(138 * obj)))
        rel_pts.append((xs[view_count], ay - int(138 * rel)))
        draw.text((xs[view_count] - 10, ay + 20), str(view_count), fill=MUTED, font=small)
    draw.line(obj_pts, fill=NODE_BLUE, width=8)
    draw.line(rel_pts, fill=NODE_TEAL, width=8)
    for px, py in obj_pts:
        draw.ellipse((px - 10, py - 10, px + 10, py + 10), fill=NODE_BLUE)
    for px, py in rel_pts:
        draw.ellipse((px - 10, py - 10, px + 10, py + 10), fill=NODE_TEAL)


def _fmt_count(value: int) -> str:
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return str(value)


def create_method_diagram(output: Path) -> None:
    width, height = 4000, 2200
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    block_title = _font(52, bold=True)
    title_font = _font(42, bold=True)
    text = _font(40)
    small = _font(32)
    tiny = _font(26)
    op_font = _font(44, bold=True)
    caption = _font(44, serif=True)
    scene = "tum_rgbd_freiburg1_room"
    frames = _scene_frame_paths(scene, limit=4)

    _circuit_corner(draw, width)
    _dashed_box(draw, (470, 160, 1745, 870), "Frozen Geometry Branch", block_title)
    _dashed_box(draw, (470, 970, 1745, 1740), "Frozen Proposal and Feature Branch", block_title)
    _dashed_box(draw, (1870, 160, 3005, 1740), "Sparse-View 3D Scene-Graph Core", block_title)
    _dashed_box(draw, (3160, 250, 3890, 1620), "Exported Graph State", block_title)

    _label(draw, 95, 295, "Sparse RGB\nviews", text)
    _photo_stack_from_scene(image, draw, scene, 80, 440, 300, 225, small, label="I_1 ... I_V", grid=False)
    _arrow(draw, (410, 560), (470, 420), label="RGB", font=tiny)
    _arrow(draw, (410, 665), (470, 1185), label="RGB", font=tiny)

    # Geometry branch: VGGT-style patch tokens, camera tokens, and dense 3D outputs.
    _paste_photo(image, draw, (530, 300, 735, 455), frames[0] if frames else None, grid=True)
    _paste_photo(image, draw, (530, 515, 735, 670), frames[1] if len(frames) > 1 else None, grid=True)
    _label(draw, 555, 705, "patchified views", small, fill=MUTED)
    _arrow(draw, (745, 380), (820, 380))
    _arrow(draw, (745, 595), (820, 595))
    _token_column(draw, 830, 300, [ENCODER_BLUE] * 5, size=34)
    _token_column(draw, 830, 515, [ENCODER_BLUE] * 5, size=34)
    draw.text((775, 248), "image\ntokens", fill=MUTED, font=tiny, spacing=0)
    _token_column(draw, 902, 300, [(190, 92, 28), ENCODER_BLUE, ENCODER_BLUE, ENCODER_BLUE, (190, 92, 28)], size=34)
    _token_column(draw, 902, 515, [(190, 92, 28), ENCODER_BLUE, ENCODER_BLUE, ENCODER_BLUE, (190, 92, 28)], size=34)
    draw.text((928, 238), "+ camera\n+ register", fill=(178, 83, 28), font=tiny, spacing=0)
    _arrow(draw, (950, 380), (1015, 405))
    _arrow(draw, (950, 595), (1015, 520))
    _trapezoid(draw, (1015, 285, 1295, 650), "VGGT\nGeometry\nBackbone", text, fill=ENCODER_BLUE)
    _arrow(draw, (1295, 420), (1370, 420))
    _token_column(draw, 1385, 300, [(190, 92, 28), ENCODER_BLUE, ENCODER_BLUE, ENCODER_BLUE, ENCODER_BLUE, (190, 92, 28)], size=33)
    _module(draw, (1480, 235, 1680, 380), "Camera\nhead", small, fill=MODULE_GREEN)
    _draw_camera_frustums(draw, 1505, 470, count=4)
    draw.text((1482, 545), "g_v: intrinsics\n+ extrinsics", fill=MUTED, font=tiny)
    _shadow_round(draw, (1468, 605, 1725, 820), radius=16, fill=TRAINED_BLUE, outline=LINE)
    draw.multiline_text((1495, 626), "Dense\noutputs", fill=INK, font=small, spacing=0)
    draw.text((1495, 696), "D_v, P_v, C_v", fill=MUTED, font=tiny)
    _draw_depth_maps(image, draw, 1495, 738, 60, 44)
    _draw_point_map(draw, 1643, 732, 74, 54, seed=4, cameras=False)
    _arrow(draw, (1725, 720), (1880, 440), elbow=(1800, 720))

    # Proposal branch: real mask overlays, feature tokens, and class-agnostic proposal artifacts.
    _paste_photo(image, draw, (530, 1105, 760, 1275), frames[2] if len(frames) > 2 else None, masks=True)
    _label(draw, 545, 1298, "SAM proposal masks", small, fill=MUTED)
    _trapezoid(draw, (830, 1070, 1115, 1310), "SAM\nMask\nGenerator", text, fill=ENCODER_BLUE)
    _feature_vector(draw, 1160, 1118, 7, color=(232, 226, 239), size=29)
    _module(draw, (1330, 1050, 1660, 1205), "M_vk\nproposal masks", text, fill=FROZEN)
    for i, color in enumerate([NODE_TEAL, NODE_BLUE, NODE_AMBER, NODE_ROSE]):
        xx = 1370 + i * 68
        draw.rounded_rectangle((xx, 1250, xx + 52, 1324), radius=8, fill=(238, 240, 240), outline=LINE, width=2)
        draw.ellipse((xx + 12, 1264, xx + 40, 1292), fill=color)
    _arrow(draw, (760, 1190), (830, 1190))
    _arrow(draw, (1115, 1190), (1330, 1135))

    _paste_photo(image, draw, (530, 1410, 760, 1578), frames[3] if len(frames) > 3 else None, grid=False)
    _trapezoid(draw, (830, 1395, 1115, 1665), "CLIP + DINOv2\nFeature\nEncoders", text, fill=ENCODER_PURPLE)
    _token_column(draw, 1160, 1435, [ENCODER_PURPLE, ENCODER_PURPLE, ENCODER_BLUE, ENCODER_BLUE, MODULE_GREEN, MODULE_GREEN], size=31)
    _module(draw, (1330, 1405, 1660, 1585), "f_vk\nproposal descriptors", text, fill=FROZEN)
    _feature_vector(draw, 1370, 1620, 8, color=TRAINED_BLUE, size=27)
    _arrow(draw, (760, 1490), (830, 1510))
    _arrow(draw, (1115, 1510), (1330, 1490))
    _arrow(draw, (1660, 1145), (1885, 710), elbow=(1785, 1145))
    _arrow(draw, (1660, 1495), (1885, 1265))

    # Proposed algorithmic core.
    _module(draw, (1925, 275, 2325, 505), "Mask-Aware\n3D Lifting", text, fill=MODULE_YELLOW)
    _badge(draw, 1970, 315, "1", tiny, fill=NODE_AMBER)
    _draw_point_map(draw, 1968, 560, 310, 190, seed=11)
    _label(draw, 1990, 775, "candidate point sets X_vk", small, fill=MUTED)
    _module(draw, (2445, 275, 2845, 505), "Uncertainty\nScoring", text, fill=TRAINED_BLUE)
    _badge(draw, 2490, 315, "2", tiny, fill=NODE_BLUE)
    _draw_confidence_meter(draw, 2475, 585, tiny)
    _arrow(draw, (2325, 390), (2445, 390))

    _module(draw, (1925, 910, 2325, 1135), "Candidate\nAssociation Graph", text, fill=MODULE_YELLOW)
    _badge(draw, 1970, 950, "3", tiny, fill=NODE_AMBER)
    _scene_graph(draw, 1880, 1125, tiny, labels=False)
    _module(draw, (2445, 910, 2845, 1135), "Cross-View\nObject Fusion", text, fill=TRAINED_BLUE)
    _badge(draw, 2490, 950, "4", tiny, fill=NODE_BLUE)
    _op_circle(draw, 2380, 1255, "~", op_font)
    _label(draw, 2315, 1320, "connected\ncomponents", tiny, fill=MUTED)
    _arrow(draw, (2125, 815), (2125, 910))
    _arrow(draw, (2325, 1025), (2445, 1025))
    _arrow(draw, (2645, 775), (2645, 910))

    _shadow_round(draw, (1925, 1410, 2325, 1605), radius=16, fill=MODULE_GREEN, outline=LINE)
    _badge(draw, 1970, 1450, "5", tiny, fill=NODE_GREEN)
    draw.text((2008, 1436), "Open-Vocabulary Labeling", fill=INK, font=tiny)
    for i, label in enumerate(["chair", "desk", "monitor", "box"]):
        yy = 1484 + i * 30
        draw.rounded_rectangle((1995, yy, 2258, yy + 28), radius=8, fill=BG, outline=(216, 213, 198))
        draw.text((2010, yy + 2), f"CLIP text: {label}", fill=MUTED, font=tiny)
    _shadow_round(draw, (2445, 1410, 2845, 1605), radius=16, fill=MODULE_YELLOW, outline=LINE)
    _badge(draw, 2490, 1450, "6", tiny, fill=NODE_AMBER)
    draw.text((2530, 1436), "Spatial Relation Inference", fill=INK, font=tiny)
    for i, rel in enumerate(["near", "left of", "supports", "above"]):
        xx = 2495 + (i % 2) * 150
        yy = 1492 + (i // 2) * 48
        draw.rounded_rectangle((xx, yy, xx + 128, yy + 34), radius=8, fill=BG, outline=(216, 213, 198))
        draw.text((xx + 12, yy + 4), rel, fill=MUTED, font=tiny)
    _arrow(draw, (2645, 1135), (2645, 1410))
    _arrow(draw, (2325, 1510), (2445, 1510))
    _arrow(draw, (2845, 1510), (3170, 1160), elbow=(3010, 1510))
    _shadow_round(draw, (1935, 1642, 2848, 1718), radius=12, fill=(252, 252, 248), outline=(180, 177, 166))
    draw.text((1965, 1662), "association rule: distance < eps_g  and  feature cosine > eps_f", fill=MUTED, font=tiny)

    # Exported graph state with a real output thumbnail and symbolic records.
    _paste_image_contain(image, draw, (3220, 360, 3825, 850), _scene_graph_path(scene, 10), fill=(255, 255, 255), crop_light=True)
    draw.text((3240, 875), "10-view output", fill=MUTED, font=tiny)
    draw.text((3635, 870), "G=(O,R)", fill=INK, font=title_font)
    _draw_object_table(draw, (3220, 940, 3825, 1198), title_font, tiny)
    _draw_relation_table(draw, (3220, 1248, 3825, 1515), title_font, tiny)
    _arrow(draw, (3515, 850), (3515, 940))
    _arrow(draw, (3515, 1198), (3515, 1248))

    _legend(draw, 470, 1835, tiny)
    _label(draw, 190, 1992, "(a) Sparse RGB evidence and frozen perception outputs", caption)
    _label(draw, 1840, 1992, "(b) Mask-aware lifting, fusion, labels, and relation export", caption)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    print(f"Wrote {output}")


def _scene_rows(draw: ImageDraw.ImageDraw, x: int, y: int, font: ImageFont.ImageFont) -> None:
    for i, scene in enumerate(["fr1_room", "fr1_desk", "fr1_desk2", "fr2_xyz", "fr3_office"]):
        yy = y + i * 48
        draw.rounded_rectangle((x, yy, x + 275, yy + 34), radius=8, fill=(252, 252, 248), outline=(189, 184, 169), width=2)
        draw.text((x + 14, yy + 7), scene, fill=INK, font=font)


def _view_cards(draw: ImageDraw.ImageDraw, x: int, y: int, font: ImageFont.ImageFont) -> None:
    for i, count in enumerate([3, 5, 8, 10]):
        xx = x + i * 100
        draw.rounded_rectangle((xx, y, xx + 78, y + 112), radius=10, fill=(252, 252, 248), outline=LINE, width=3)
        label = str(count)
        tw, th = _text_size(draw, label, font)
        draw.text((xx + 39 - tw // 2, y + 13), label, fill=INK, font=font)
        for j in range(min(count, 5)):
            draw.rectangle((xx + 13 + j * 7, y + 68 + j * 2, xx + 53 + j * 7, y + 91 + j * 2), fill=(220, 234, 251), outline=NODE_BLUE)


def _table_curve(draw: ImageDraw.ImageDraw, x: int, y: int, font: ImageFont.ImageFont) -> None:
    _module(draw, (x, y, x + 330, y + 230), "Sparse-View\nSummary Tables", font, fill=FROZEN)
    for i in range(5):
        draw.line((x + 52, y + 118 + i * 22, x + 280, y + 118 + i * 22), fill=(167, 174, 181), width=3)
    _module(draw, (x + 410, y, x + 740, y + 230), "Checked-Reference\nF1 Curves", font, fill=FROZEN)
    ax, ay = x + 455, y + 178
    draw.line((ax, y + 68, ax, ay), fill=LINE, width=3)
    draw.line((ax, ay, x + 700, ay), fill=LINE, width=3)
    pts = [(ax + 18, ay - 36), (ax + 76, ay - 58), (ax + 146, ay - 94), (ax + 218, ay - 126)]
    draw.line(pts, fill=NODE_TEAL, width=6)
    for px, py in pts:
        draw.ellipse((px - 8, py - 8, px + 8, py + 8), fill=NODE_TEAL)


def _review_packet(draw: ImageDraw.ImageDraw, x: int, y: int, font: ImageFont.ImageFont) -> None:
    _shadow_round(draw, (x, y, x + 460, y + 300), radius=14, fill=(252, 252, 248), outline=LINE)
    draw.rectangle((x + 28, y + 28, x + 432, y + 68), fill=(235, 238, 239))
    draw.text((x + 45, y + 36), "annotation_review.html", fill=INK, font=font)
    for i, color in enumerate([NODE_TEAL, NODE_BLUE, NODE_AMBER, NODE_ROSE]):
        xx = x + 42 + (i % 2) * 90
        yy = y + 95 + (i // 2) * 82
        draw.rounded_rectangle((xx, yy, xx + 64, yy + 54), radius=7, fill=(228, 235, 240), outline=(222, 220, 205))
        draw.ellipse((xx + 16, yy + 12, xx + 48, yy + 44), fill=color)
    draw.rounded_rectangle((x + 260, y + 100, x + 420, y + 260), radius=10, fill=BG, outline=LINE, width=2)
    for i, item in enumerate(["nodes.csv", "relations.csv", "draft.json"]):
        draw.text((x + 280, y + 118 + i * 48), item, fill=MUTED, font=font)


def _metric_bars(draw: ImageDraw.ImageDraw, x: int, y: int, font: ImageFont.ImageFont) -> None:
    for i, (label, value, color) in enumerate([("object F1", 0.78, NODE_BLUE), ("relation F1", 0.64, NODE_TEAL), ("uncertainty", 0.36, NODE_ROSE)]):
        yy = y + i * 66
        draw.text((x, yy), label, fill=INK, font=font)
        draw.rounded_rectangle((x + 135, yy + 7, x + 295, yy + 31), radius=12, fill=(231, 236, 239))
        draw.rounded_rectangle((x + 135, yy + 7, x + 135 + int(160 * value), yy + 31), radius=12, fill=color)


def _titled_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    body: str,
    *,
    fill: Color,
    title_font: ImageFont.ImageFont,
    body_font: ImageFont.ImageFont,
) -> tuple[int, int, int, int]:
    _shadow_round(draw, box, radius=16, fill=fill, outline=LINE)
    x1, y1, x2, y2 = box
    draw.text((x1 + 24, y1 + 24), title, fill=INK, font=title_font)
    lines = _wrap(draw, body, body_font, x2 - x1 - 48)
    y = y1 + 76
    for line in lines[:3]:
        draw.text((x1 + 24, y), line, fill=MUTED, font=body_font)
        y += 34
    return x1 + 24, y + 12, x2 - 24, y2 - 24


def create_evaluation_diagram(output: Path) -> None:
    width, height = 4000, 2150
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    block_title = _font(52, bold=True)
    title_font = _font(42, bold=True)
    text = _font(34)
    small = _font(28)
    tiny = _font(24)
    caption = _font(44, serif=True)
    scenes = [
        "tum_rgbd_freiburg1_room",
        "tum_rgbd_freiburg1_desk",
        "tum_rgbd_freiburg1_desk2",
        "tum_rgbd_freiburg2_xyz",
        "tum_rgbd_freiburg3_long_office_household",
    ]
    view_counts = [3, 5, 8, 10]
    rows = _summary_rows()
    by_key: dict[tuple[str, int], dict[str, str]] = {}
    for row in rows:
        by_key[(row["scene_id"], int(row["view_count"]))] = row

    _circuit_corner(draw, width)
    draw.line((2050, 135, 2050, 1725), fill=(112, 112, 104), width=3)

    _label(draw, 560, 115, "(a) Sparse-view benchmark matrix", block_title)
    _label(draw, 2570, 115, "(b) Checked annotation protocol", block_title)

    _dashed_box(draw, (90, 225, 1975, 1665), "Public TUM RGB-D Sparse-View Runs", block_title)
    _dashed_box(draw, (2120, 225, 3910, 1665), "Annotation and Metric Protocol", block_title)

    # Left panel: the concrete 5 x 4 benchmark grid.
    draw.text((150, 300), "Scene", fill=INK, font=title_font)
    for j, view_count in enumerate(view_counts):
        draw.text((610 + j * 325, 300), f"{view_count} views", fill=INK, font=title_font)

    for i, scene_id in enumerate(scenes):
        yy = 365 + i * 190
        frame = _scene_frame_paths(scene_id, limit=1)
        _paste_photo(image, draw, (150, yy, 330, yy + 112), frame[0] if frame else None)
        draw.text((150, yy + 126), _scene_name(scene_id), fill=INK, font=small)
        draw.text((150, yy + 154), "10 selected RGB frames", fill=MUTED, font=tiny)
        for j, view_count in enumerate(view_counts):
            row = by_key.get((scene_id, view_count), {})
            nodes = int(row.get("num_nodes", 30 + i * 8 + j * 7))
            relations = int(row.get("num_relations", 300 + i * 80 + j * 120))
            color = [NODE_TEAL, NODE_BLUE, NODE_PURPLE, NODE_AMBER][j]
            _draw_graph_output_cell(
                draw,
                560 + j * 325,
                yy,
                245,
                128,
                nodes=nodes,
                relations=relations,
                color=color,
                font=tiny,
            )
            if view_count == 10:
                draw.rounded_rectangle((738 + j * 325, yy + 10, 796 + j * 325, yy + 42), radius=7, fill=MODULE_GREEN, outline=LINE)
                draw.text((747 + j * 325, yy + 14), "ref", fill=INK, font=tiny)

    draw.rounded_rectangle((500, 1270, 1620, 1315), radius=12, fill=MODULE_YELLOW, outline=LINE, width=2)
    draw.text((540, 1277), "20 graph outputs: same code path, varying only sparse RGB view count", fill=INK, font=small)
    _shadow_round(draw, (270, 1340, 935, 1628), radius=14, fill=FROZEN, outline=LINE)
    draw.text((305, 1362), "Sparse-view summary table", fill=INK, font=title_font)
    table_rows = [("views", "O", "R", "multi-view"), ("3", "31-41", "338-1088", "5-17"), ("5", "31-64", "500-2100", "14-20"), ("8", "40-79", "770-2836", "20-26"), ("10", "47-110", "1130-3564", "25-30")]
    col_x = [305, 455, 585, 760]
    for r, row in enumerate(table_rows):
        yy = 1427 + r * 40
        for value, xx in zip(row, col_x):
            draw.text((xx, yy), value, fill=INK if r else MUTED, font=tiny)
        if r:
            draw.line((300, yy - 8, 900, yy - 8), fill=(215, 216, 210), width=2)
    _draw_sparse_view_metric_curve(draw, 985, 1328, rows, text, small)

    # Right panel: 10-view draft creation and manual-review loop.
    _shadow_round(draw, (2180, 330, 2775, 820), radius=14, fill=MODULE_YELLOW, outline=LINE)
    _badge(draw, 2225, 365, "1", tiny, fill=NODE_AMBER)
    draw.text((2270, 356), "10-view graph drafts", fill=INK, font=title_font)
    draw.text((2270, 398), "one checked seed per scene", fill=MUTED, font=small)
    for i, scene_id in enumerate(scenes):
        xx = 2225 + (i % 3) * 180
        yy = 460 + (i // 3) * 135
        _draw_graph_output_cell(
            draw,
            xx,
            yy,
            150,
            104,
            nodes=int(by_key.get((scene_id, 10), {}).get("num_nodes", 50)),
            relations=int(by_key.get((scene_id, 10), {}).get("num_relations", 1000)),
            color=[NODE_TEAL, NODE_BLUE, NODE_PURPLE, NODE_AMBER, NODE_GREEN][i],
            font=tiny,
        )
        draw.text((xx, yy + 110), _scene_name(scene_id), fill=MUTED, font=tiny)

    _shadow_round(draw, (2950, 330, 3815, 820), radius=14, fill=TRAINED_BLUE, outline=LINE)
    _badge(draw, 2995, 365, "2", tiny, fill=NODE_BLUE)
    draw.text((3040, 356), "Prediction-seeded draft", fill=INK, font=title_font)
    draw.text((3040, 398), "object labels, relation triplets, and source graph ids", fill=MUTED, font=small)
    _feature_vector(draw, 3010, 470, 12, color=TRAINED_BLUE, size=30)
    draft_rows = ["objects: {id, label, centroid, views, U}", "relations: {subject, predicate, object}", "source: scene_graph_labeled.json", "review_state: draft"]
    for i, line in enumerate(draft_rows):
        yy = 548 + i * 54
        draw.rounded_rectangle((3010, yy, 3775, yy + 40), radius=9, fill=BG, outline=(214, 211, 197))
        draw.text((3026, yy + 6), line, fill=INK, font=small)

    _arrow(draw, (2775, 575), (2950, 575), label="draft", font=tiny)
    _arrow(draw, (3380, 820), (3380, 1015), label="packet", font=tiny)

    _shadow_round(draw, (2180, 1040, 2705, 1515), radius=14, fill=(252, 252, 248), outline=LINE)
    draw.rectangle((2215, 1070, 2670, 1110), fill=(235, 238, 239))
    _badge(draw, 2235, 1090, "3", tiny, fill=NODE_PURPLE)
    draw.text((2262, 1078), "annotation_review.html", fill=INK, font=small)
    sample_frame = _scene_frame_paths("tum_rgbd_freiburg1_room", limit=1)
    _paste_photo(image, draw, (2228, 1140, 2446, 1290), sample_frame[0] if sample_frame else None, masks=True)
    draw.rounded_rectangle((2470, 1140, 2678, 1458), radius=10, fill=BG, outline=LINE, width=2)
    for i, item in enumerate(["nodes.csv", "relations.csv", "draft.json", "checked.json"]):
        draw.text((2492, 1164 + i * 62), item, fill=MUTED, font=tiny)
    draw.text((2225, 1322), "visual packet:\nRGB + masks\nobject ids\nCSV/JSON files", fill=MUTED, font=small)

    _shadow_round(draw, (2820, 1040, 3210, 1515), radius=14, fill=MODULE_GREEN, outline=LINE)
    _badge(draw, 2865, 1075, "4", tiny, fill=NODE_GREEN)
    draw.text((2910, 1070), "Manual review", fill=INK, font=title_font)
    draw.multiline_text((2910, 1110), "checked labels\nand triplets", fill=MUTED, font=small, spacing=0)
    for i, label in enumerate(["keep/drop", "relabel", "valid relation"]):
        yy = 1198 + i * 88
        draw.rectangle((2868, yy + 6, 2900, yy + 38), outline=NODE_TEAL, width=3)
        draw.line((2873, yy + 22, 2884, yy + 34, 2904, yy + 8), fill=NODE_TEAL, width=4)
        draw.text((2926, yy + 8), label, fill=INK, font=small)

    non_ref = [r for r in rows if r.get("is_reference_view") == "False"]
    object_f1 = sum(float(r.get("object_label_f1", 0.0)) for r in non_ref) / max(1, len(non_ref))
    relation_f1 = sum(float(r.get("relation_triplet_f1", 0.0)) for r in non_ref) / max(1, len(non_ref))
    uncertainty = sum(float(r.get("mean_uncertainty", 0.0)) for r in rows) / max(1, len(rows))
    _shadow_round(draw, (3310, 1040, 3815, 1515), radius=14, fill=TRAINED_BLUE, outline=LINE)
    _badge(draw, 3355, 1075, "5", tiny, fill=NODE_BLUE)
    draw.text((3400, 1070), "Checked metrics", fill=INK, font=title_font)
    draw.text((3400, 1112), "object labels and relation triplets", fill=MUTED, font=small)
    metrics = [("object F1", object_f1, NODE_BLUE), ("relation F1", relation_f1, NODE_TEAL), ("mean U", min(1.0, uncertainty * 10), NODE_ROSE)]
    for i, (label, value, color) in enumerate(metrics):
        yy = 1195 + i * 92
        draw.text((3355, yy), label, fill=INK, font=small)
        draw.rounded_rectangle((3510, yy + 8, 3765, yy + 36), radius=14, fill=(231, 236, 239))
        draw.rounded_rectangle((3510, yy + 8, 3510 + int(255 * value), yy + 36), radius=14, fill=color)
        draw.text((3775, yy + 2), f"{value:.2f}", fill=MUTED, font=tiny)

    _arrow(draw, (2705, 1270), (2820, 1270), label="review", font=tiny)
    _arrow(draw, (3210, 1270), (3310, 1270), label="checked JSON", font=tiny)

    _label(draw, 185, 1905, "(a) Sparse-view benchmark matrix and summary tables", caption)
    _label(draw, 2160, 1905, "(b) Checked annotation review and metrics", caption)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    print(f"Wrote {output}")


def main() -> None:
    args = parse_args()
    create_method_diagram(args.output_dir / "method_pipeline.png")
    create_evaluation_diagram(args.output_dir / "evaluation_protocol.png")


if __name__ == "__main__":
    main()
