from __future__ import annotations

import argparse
import json
from pathlib import Path

"""Build an INDEPENDENT evaluation reference (not seeded from any pipeline prediction).

The existing pseudo-reference (`annotation_checked.json`) is derived from the 10-view
graph-fusion prediction, which makes the evaluation circular (graph-fusion scores ~1.0 at
v10 by construction). This builds per-scene annotation packets from a hand/VLM-authored
label file that was produced by inspecting the RGB frames directly, using the project's
open-vocabulary label set — so it is independent of SAM/CLIP/VGGT/graph-fusion.

Input `--labels` JSON:
{
  "label_source": "human" | "vlm-drafted-human-verified" | ...,   # provenance, for the paper
  "scenes": {
    "tum_rgbd_freiburg1_desk": {
      "objects": {"desk": 1, "monitor": 2, "keyboard": 1, "chair": 2, "cup": 1},
      "relations": [ {"subject_label": "keyboard", "relation": "near", "object_label": "monitor", "count": 1} ]
    },
    ...
  }
}

Writes, per scene, a packet matching evaluate_sparse_view_annotations.py's expected layout:
  <output-root>/<scene>_<suffix>_<ref_view>view/<annotation-file-name>
so the evaluator can be pointed at it with --annotations-root/--annotation-file-name unchanged.
"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build an independent (non-pipeline-seeded) evaluation reference.")
    p.add_argument("--labels", type=Path, required=True, help="Independent labels JSON (see module docstring).")
    p.add_argument("--output-root", type=Path, required=True, help="Annotations root to write packets under.")
    p.add_argument("--reference-view-count", type=int, default=10)
    p.add_argument("--packet-mode", choices=["pseudo_reference", "manual_review"], default="pseudo_reference")
    p.add_argument("--annotation-file-name", default="annotation_independent.json")
    p.add_argument("--label-vocab", type=Path, help="Optional vocab JSON to validate labels against.")
    return p.parse_args()


def _packet_name(scene_id: str, mode: str, view_count: int) -> str:
    suffix = "pseudo_from" if mode == "pseudo_reference" else "manual_from"
    return f"{scene_id}_{suffix}_{view_count:02d}view"


def main() -> None:
    args = parse_args()
    spec = json.loads(args.labels.read_text(encoding="utf-8"))
    source = spec.get("label_source", "independent")
    scenes = spec.get("scenes", {})
    if not scenes:
        raise SystemExit("No scenes in labels file.")

    vocab = None
    if args.label_vocab:
        vocab = set(json.loads(args.label_vocab.read_text(encoding="utf-8")).get("labels", []))

    written = 0
    for scene_id, entry in scenes.items():
        objects = entry.get("objects", {})
        relations = entry.get("relations", [])
        if vocab is not None:
            unknown = sorted(set(objects) - vocab)
            if unknown:
                raise SystemExit(f"{scene_id}: labels not in vocab: {unknown}")
        object_rows = [{"label": label, "count": int(count)} for label, count in objects.items() if int(count) > 0]
        relation_rows = [
            {
                "subject_label": r["subject_label"],
                "relation": r["relation"],
                "object_label": r["object_label"],
                "count": int(r.get("count", 1)),
            }
            for r in relations
        ]
        payload = {
            "name": f"{scene_id}_independent_reference",
            "version": "0.1",
            "source_scene_graph": "",  # explicitly NOT derived from a prediction
            "notes": f"Independent reference (label_source={source}); authored from RGB frames, "
            "not seeded from any pipeline prediction. Breaks the graph-fusion circularity.",
            "scenes": [{"scene_id": scene_id, "objects": object_rows, "relations": relation_rows}],
            "metadata": {"review_state": "independent", "label_source": source},
        }
        packet_dir = args.output_root / _packet_name(scene_id, args.packet_mode, args.reference_view_count)
        packet_dir.mkdir(parents=True, exist_ok=True)
        (packet_dir / args.annotation_file_name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written += 1
        n_obj = sum(o["count"] for o in object_rows)
        print(f"{scene_id}: {len(object_rows)} labels / {n_obj} objects, {len(relation_rows)} relations -> {packet_dir}")

    print(f"Wrote {written} independent reference packets under {args.output_root}")


if __name__ == "__main__":
    main()
