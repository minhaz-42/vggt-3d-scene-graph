from __future__ import annotations

import argparse
import json
from pathlib import Path

from vggt_scene_graph.features import extract_features_for_records, make_feature_extractor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract proposal-level visual features.")
    parser.add_argument("--scene-dir", type=Path, required=True)
    parser.add_argument("--proposals", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", default="handcrafted_color", choices=["handcrafted_color", "clip", "dinov2", "transformers"])
    parser.add_argument("--model-name", help="Model name for transformer-backed extraction.")
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.proposals.read_text(encoding="utf-8"))
    extractor = make_feature_extractor(args.backend, model_name=args.model_name, device=args.device)
    records = extract_features_for_records(args.scene_dir, payload.get("proposals", []), extractor)

    output_payload = dict(payload)
    output_payload["proposals"] = records
    output_payload["feature_backends"] = sorted({key for record in records for key in record.get("features", {})})
    output_payload["num_featured_proposals"] = len(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")
    print(f"Wrote features for {len(records)} proposals to {args.output}")
    print(f"feature_backends={output_payload['feature_backends']}")


if __name__ == "__main__":
    main()
