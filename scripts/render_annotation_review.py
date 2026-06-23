from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from vggt_scene_graph.geometry_io import list_scene_images
from vggt_scene_graph.masking import decode_binary_mask_rle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a visual HTML review sheet for scene graph annotations.")
    parser.add_argument("--scene-graph", type=Path, required=True)
    parser.add_argument("--proposals", type=Path, required=True)
    parser.add_argument("--scene-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--node-review", type=Path, help="Optional node_review.csv to show current review fields.")
    parser.add_argument("--relation-review", type=Path, help="Optional relation_review.csv to summarize relation rows.")
    parser.add_argument("--max-thumbnails-per-node", type=int, default=4)
    parser.add_argument("--thumbnail-long-side", type=int, default=260)
    return parser.parse_args()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_filename(value: str) -> str:
    return "".join(character if character.isalnum() or character in "-_" else "_" for character in value)


def _read_csv_by_key(path: Path | None, key: str) -> dict[str, dict[str, str]]:
    if path is None or not path.exists():
        return {}
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {_clean(row.get(key)): row for row in rows if _clean(row.get(key))}


def _read_relation_rows(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _node_label(node: dict[str, Any]) -> str:
    label = _clean(node.get("label"))
    if label:
        return label
    metadata = node.get("metadata", {})
    if isinstance(metadata, dict):
        return _clean(metadata.get("open_vocab_label")) or "unknown object"
    return "unknown object"


def _top_scores(node: dict[str, Any], top_k: int = 5) -> str:
    metadata = node.get("metadata", {})
    scores = metadata.get("open_vocab_scores", []) if isinstance(metadata, dict) else []
    if not isinstance(scores, list):
        return ""
    parts = []
    for item in scores[:top_k]:
        if isinstance(item, dict):
            label = _clean(item.get("label"))
            score = float(item.get("score", 0.0))
            parts.append(f"{label} {score:.4f}")
    return ", ".join(parts)


def _format_xyz(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    formatted = []
    for value in values[:3]:
        try:
            formatted.append(f"{float(value):.3f}")
        except (TypeError, ValueError):
            formatted.append(_clean(value))
    return ", ".join(formatted)


def _image_by_stem(scene_dir: Path) -> dict[str, Path]:
    return {path.stem: path for path in list_scene_images(scene_dir)}


def _proposal_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    proposals = payload.get("proposals", [])
    return {_clean(record.get("proposal_id")): record for record in proposals if _clean(record.get("proposal_id"))}


def _clamp_bbox(bbox: list[Any], width: int, height: int, padding: int = 14) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = [int(round(float(value))) for value in bbox]
    x1 = max(0, min(width - 1, x1 - padding))
    y1 = max(0, min(height - 1, y1 - padding))
    x2 = max(x1 + 1, min(width, x2 + padding))
    y2 = max(y1 + 1, min(height, y2 + padding))
    return x1, y1, x2, y2


def _resize_long_side(image: np.ndarray, long_side: int) -> np.ndarray:
    if long_side <= 0:
        return image
    height, width = image.shape[:2]
    current_long_side = max(height, width)
    if current_long_side <= long_side:
        return image
    scale = long_side / float(current_long_side)
    size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    return cv2.resize(image, size, interpolation=cv2.INTER_AREA)


def _render_thumbnail(
    proposal: dict[str, Any],
    image_paths: dict[str, Path],
    output_path: Path,
    *,
    long_side: int,
) -> bool:
    view_id = _clean(proposal.get("view_id"))
    image_path = image_paths.get(view_id)
    if image_path is None:
        return False
    image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image_bgr is None:
        return False

    height, width = image_bgr.shape[:2]
    bbox = proposal.get("bbox_xyxy", [0, 0, width, height])
    x1, y1, x2, y2 = _clamp_bbox(bbox, width, height)
    overlay = image_bgr.copy()

    mask_rle = proposal.get("mask_rle")
    if isinstance(mask_rle, dict):
        try:
            mask = decode_binary_mask_rle(mask_rle)
            if mask.shape[:2] == image_bgr.shape[:2]:
                color = np.array([36, 176, 255], dtype=np.uint8)
                overlay[mask] = (0.55 * overlay[mask] + 0.45 * color).astype(np.uint8)
        except (KeyError, ValueError):
            pass

    raw_x1, raw_y1, raw_x2, raw_y2 = [int(round(float(value))) for value in bbox]
    cv2.rectangle(
        overlay,
        (max(0, raw_x1), max(0, raw_y1)),
        (min(width - 1, raw_x2), min(height - 1, raw_y2)),
        (20, 220, 255),
        2,
    )
    crop = overlay[y1:y2, x1:x2]
    crop = _resize_long_side(crop, long_side)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(output_path), crop))


def _select_proposals(
    node: dict[str, Any],
    proposals: dict[str, dict[str, Any]],
    max_count: int,
) -> list[dict[str, Any]]:
    records = [proposals[proposal_id] for proposal_id in node.get("proposal_ids", []) if proposal_id in proposals]
    records.sort(key=lambda record: int(record.get("mask_area", 0)), reverse=True)

    selected: list[dict[str, Any]] = []
    seen_views: set[str] = set()
    for record in records:
        view_id = _clean(record.get("view_id"))
        if view_id in seen_views:
            continue
        selected.append(record)
        seen_views.add(view_id)
        if len(selected) >= max_count:
            return selected

    for record in records:
        if record in selected:
            continue
        selected.append(record)
        if len(selected) >= max_count:
            break
    return selected


def _css() -> str:
    return """
:root {
  color-scheme: light;
  --ink: #17202a;
  --muted: #64707d;
  --line: #d7dde4;
  --panel: #ffffff;
  --page: #f4f6f8;
  --accent: #0f766e;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--page);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.45;
}
main { max-width: 1280px; margin: 0 auto; padding: 28px; }
h1 { margin: 0 0 8px; font-size: 28px; font-weight: 700; letter-spacing: 0; }
h2 { margin: 28px 0 12px; font-size: 18px; letter-spacing: 0; }
.summary {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 16px 0 24px;
}
.pill {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 6px;
  padding: 6px 10px;
  color: var(--muted);
  font-size: 13px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 14px;
}
.node {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px;
}
.node-head {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: start;
}
.node-id { font-weight: 700; font-size: 16px; }
.label {
  color: var(--accent);
  font-weight: 700;
  font-size: 15px;
  text-align: right;
}
.meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 12px;
  margin: 10px 0;
  font-size: 13px;
}
.meta span { color: var(--muted); }
.scores {
  color: var(--muted);
  font-size: 13px;
  min-height: 20px;
}
.review {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 12px 0;
  font-size: 13px;
}
.review div {
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 6px 8px;
  min-height: 34px;
}
.review span {
  display: block;
  color: var(--muted);
  font-size: 11px;
}
.thumbs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
  margin-top: 12px;
}
.thumb {
  border: 1px solid var(--line);
  border-radius: 6px;
  overflow: hidden;
  background: #eef1f4;
}
.thumb img { display: block; width: 100%; height: 148px; object-fit: contain; background: #111; }
.thumb div {
  padding: 5px 7px;
  color: var(--muted);
  font-size: 11px;
  overflow-wrap: anywhere;
}
details {
  margin-top: 10px;
  color: var(--muted);
  font-size: 12px;
}
table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  display: table;
}
th, td {
  text-align: left;
  border-bottom: 1px solid var(--line);
  padding: 7px 9px;
  font-size: 13px;
}
th { color: var(--muted); font-weight: 600; background: #f9fafb; }
tr:last-child td { border-bottom: 0; }
@media (max-width: 720px) {
  main { padding: 16px; }
  .grid { grid-template-columns: 1fr; }
  .meta, .review { grid-template-columns: 1fr; }
}
"""


def _node_card(
    node: dict[str, Any],
    review_row: dict[str, str],
    thumbnails: list[tuple[str, str]],
) -> str:
    metadata = node.get("metadata", {})
    node_id = _clean(node.get("node_id"))
    predicted_label = _node_label(node)
    review_label = _clean(review_row.get("review_label"))
    keep = _clean(review_row.get("keep"))
    num_views = _clean(metadata.get("num_views") if isinstance(metadata, dict) else "")
    uncertainty = float(node.get("uncertainty", 0.0))
    centroid = _format_xyz(node.get("centroid_xyz"))
    extent = ""
    if isinstance(metadata, dict):
        bbox = metadata.get("bbox_3d", {})
        if isinstance(bbox, dict):
            extent = _format_xyz(bbox.get("extent_xyz"))

    thumb_html = []
    for source, relative_path in thumbnails:
        thumb_html.append(
            '<div class="thumb">'
            f'<img src="{html.escape(relative_path)}" alt="{html.escape(source)}">'
            f"<div>{html.escape(source)}</div>"
            "</div>"
        )
    if not thumb_html:
        thumb_html.append('<div class="thumb"><div>No proposal thumbnail available</div></div>')

    proposal_ids = ", ".join(_clean(value) for value in node.get("proposal_ids", []))
    return f"""
<article class="node">
  <div class="node-head">
    <div class="node-id">{html.escape(node_id)}</div>
    <div class="label">{html.escape(predicted_label)}</div>
  </div>
  <div class="meta">
    <div><span>Views</span> {html.escape(num_views)}</div>
    <div><span>Points</span> {html.escape(_clean(node.get("num_points")))}</div>
    <div><span>Uncertainty</span> {uncertainty:.4f}</div>
    <div><span>Centroid</span> {html.escape(centroid)}</div>
    <div><span>3D extent</span> {html.escape(extent)}</div>
    <div><span>Sources</span> {html.escape(_clean(metadata.get("num_source_nodes") if isinstance(metadata, dict) else ""))}</div>
  </div>
  <div class="scores">{html.escape(_top_scores(node))}</div>
  <div class="review">
    <div><span>review_label</span>{html.escape(review_label)}</div>
    <div><span>keep</span>{html.escape(keep)}</div>
    <div><span>predicted_label</span>{html.escape(predicted_label)}</div>
  </div>
  <div class="thumbs">
    {''.join(thumb_html)}
  </div>
  <details>
    <summary>proposal ids</summary>
    {html.escape(proposal_ids)}
  </details>
</article>
"""


def _relation_table(rows: list[dict[str, str]], max_rows: int = 80) -> str:
    if not rows:
        return ""
    body = []
    for row in rows[:max_rows]:
        subject = _clean(row.get("review_subject_label")) or _clean(row.get("subject_label"))
        relation = _clean(row.get("review_relation")) or _clean(row.get("relation"))
        obj = _clean(row.get("review_object_label")) or _clean(row.get("object_label"))
        count = _clean(row.get("review_count")) or _clean(row.get("count"))
        keep = _clean(row.get("keep"))
        body.append(
            "<tr>"
            f"<td>{html.escape(subject)}</td>"
            f"<td>{html.escape(relation)}</td>"
            f"<td>{html.escape(obj)}</td>"
            f"<td>{html.escape(count)}</td>"
            f"<td>{html.escape(keep)}</td>"
            "</tr>"
        )
    return f"""
<h2>Relation Triplets</h2>
<table>
  <thead>
    <tr><th>Subject</th><th>Relation</th><th>Object</th><th>Count</th><th>Keep</th></tr>
  </thead>
  <tbody>{''.join(body)}</tbody>
</table>
"""


def main() -> None:
    args = parse_args()
    scene_graph = json.loads(args.scene_graph.read_text(encoding="utf-8"))
    proposal_payload = json.loads(args.proposals.read_text(encoding="utf-8"))
    nodes = scene_graph.get("nodes", [])
    relations = scene_graph.get("relations", [])
    proposals = _proposal_by_id(proposal_payload)
    image_paths = _image_by_stem(args.scene_dir)
    node_review = _read_csv_by_key(args.node_review, "node_id")
    relation_rows = _read_relation_rows(args.relation_review)

    thumbs_dir = args.output_dir / "thumbnails"
    cards = []
    rendered_count = 0
    for node in nodes:
        node_id = _clean(node.get("node_id"))
        thumbnail_records = []
        selected = _select_proposals(node, proposals, args.max_thumbnails_per_node)
        for index, proposal in enumerate(selected, start=1):
            proposal_id = _clean(proposal.get("proposal_id"))
            thumb_name = f"{_safe_filename(node_id)}_{index:02d}_{_safe_filename(proposal_id)}.jpg"
            thumb_path = thumbs_dir / thumb_name
            if _render_thumbnail(
                proposal,
                image_paths,
                thumb_path,
                long_side=args.thumbnail_long_side,
            ):
                rendered_count += 1
                thumbnail_records.append((proposal_id, f"thumbnails/{thumb_name}"))
        cards.append(_node_card(node, node_review.get(node_id, {}), thumbnail_records))

    html_payload = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(_clean(scene_graph.get("scene_id")))} annotation review</title>
  <style>{_css()}</style>
</head>
<body>
  <main>
    <h1>{html.escape(_clean(scene_graph.get("scene_id")))} Annotation Review</h1>
    <div class="summary">
      <div class="pill">{len(nodes)} nodes</div>
      <div class="pill">{len(relations)} predicted relations</div>
      <div class="pill">{len(proposals)} proposals</div>
      <div class="pill">{rendered_count} thumbnails</div>
    </div>
    <section class="grid">
      {''.join(cards)}
    </section>
    {_relation_table(relation_rows)}
  </main>
</body>
</html>
"""
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "annotation_review.html"
    output_path.write_text(html_payload, encoding="utf-8")
    print(f"Wrote annotation review HTML to {output_path}")
    print(f"Rendered {rendered_count} thumbnails to {thumbs_dir}")


if __name__ == "__main__":
    main()
