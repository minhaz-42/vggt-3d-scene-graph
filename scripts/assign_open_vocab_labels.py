from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assign open-vocabulary labels to fused scene graph nodes.")
    parser.add_argument("--scene-graph", type=Path, required=True)
    parser.add_argument("--proposals", type=Path, help="Proposal JSON with CLIP feature vectors.")
    parser.add_argument("--labels", type=Path, required=True, help="JSON label vocabulary.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-name", default="openai/clip-vit-base-patch32")
    parser.add_argument("--prompt-template", default="a photo of a {}")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--local-files-only", action="store_true", help="Load CLIP only from local cache.")
    return parser.parse_args()


def _load_labels(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        labels = payload
    elif isinstance(payload, dict):
        labels = payload.get("labels", [])
    else:
        labels = []
    labels = [str(label).strip() for label in labels if str(label).strip()]
    if not labels:
        raise ValueError(f"No labels found in {path}")
    return labels


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm > 0:
        vector = vector / norm
    return vector.astype(np.float32)


def _load_clip_text_features(
    labels: list[str],
    model_name: str,
    prompt_template: str,
    device: str,
    local_files_only: bool,
) -> np.ndarray:
    if local_files_only:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    try:
        import torch
        from transformers import AutoProcessor, CLIPModel
    except ImportError as exc:
        raise RuntimeError("Open-vocabulary labeling requires `transformers` and CLIP.") from exc

    processor = AutoProcessor.from_pretrained(model_name, local_files_only=local_files_only)
    model = CLIPModel.from_pretrained(
        model_name,
        local_files_only=local_files_only,
        use_safetensors=False,
    ).to(device)
    model.eval()
    prompts = [prompt_template.format(label) for label in labels]
    inputs = processor(text=prompts, return_tensors="pt", padding=True)
    inputs = {key: value.to(device) for key, value in inputs.items()}
    with torch.inference_mode():
        outputs = model.get_text_features(**inputs)
        if isinstance(outputs, torch.Tensor):
            features = outputs
        elif hasattr(outputs, "text_embeds") and outputs.text_embeds is not None:
            features = outputs.text_embeds
        elif hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
            features = outputs.pooler_output
            if (
                hasattr(model, "text_projection")
                and features.shape[-1] == model.text_projection.in_features
            ):
                features = model.text_projection(features)
        else:
            text_outputs = model.text_model(**inputs)
            features = text_outputs.pooler_output
            if (
                hasattr(model, "text_projection")
                and features.shape[-1] == model.text_projection.in_features
            ):
                features = model.text_projection(features)
    features = features.detach().cpu().float().numpy()
    return np.stack([_normalize(feature) for feature in features], axis=0)


def _proposal_path_from_graph(payload: dict[str, Any], graph_path: Path) -> Path:
    proposals_path = payload.get("pipeline", {}).get("proposals_path")
    if not proposals_path:
        raise ValueError("Scene graph has no pipeline.proposals_path; pass --proposals.")
    path = Path(str(proposals_path))
    if path.exists():
        return path
    candidate = graph_path.parent / path
    if candidate.exists():
        return candidate
    return path


def _load_proposal_clip_features(path: Path) -> dict[str, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    features: dict[str, np.ndarray] = {}
    for record in payload.get("proposals", []):
        proposal_id = str(record.get("proposal_id"))
        clip_payload = record.get("features", {}).get("clip") if isinstance(record.get("features"), dict) else None
        if isinstance(clip_payload, dict) and "vector" in clip_payload:
            features[proposal_id] = _normalize(np.asarray(clip_payload["vector"], dtype=np.float32).reshape(-1))
    if not features:
        raise ValueError(f"No CLIP proposal features found in {path}")
    return features


def _node_feature(node: dict[str, Any], proposal_features: dict[str, np.ndarray]) -> np.ndarray | None:
    vectors = []
    for proposal_id in node.get("proposal_ids", []):
        vector = proposal_features.get(str(proposal_id))
        if vector is not None:
            vectors.append(vector)
    if not vectors:
        return None
    return _normalize(np.mean(np.stack(vectors, axis=0), axis=0))


def main() -> None:
    args = parse_args()
    graph_payload = json.loads(args.scene_graph.read_text(encoding="utf-8"))
    proposals_path = args.proposals or _proposal_path_from_graph(graph_payload, args.scene_graph)
    labels = _load_labels(args.labels)
    text_features = _load_clip_text_features(
        labels,
        model_name=args.model_name,
        prompt_template=args.prompt_template,
        device=args.device,
        local_files_only=args.local_files_only,
    )
    proposal_features = _load_proposal_clip_features(proposals_path)

    labeled_nodes = 0
    for node in graph_payload.get("nodes", []):
        feature = _node_feature(node, proposal_features)
        if feature is None:
            continue
        scores = feature @ text_features.T
        top_indices = np.argsort(-scores)[: max(args.top_k, 1)]
        top_labels = [
            {"label": labels[index], "score": round(float(scores[index]), 6)}
            for index in top_indices
        ]
        node["label"] = top_labels[0]["label"]
        metadata = dict(node.get("metadata", {}))
        metadata["open_vocab_label"] = top_labels[0]["label"]
        metadata["open_vocab_scores"] = top_labels
        metadata["open_vocab_model"] = args.model_name
        metadata["open_vocab_prompt_template"] = args.prompt_template
        node["metadata"] = metadata
        labeled_nodes += 1

    pipeline = dict(graph_payload.get("pipeline", {}))
    pipeline["labeling"] = {
        "backend": "clip_text_similarity",
        "model_name": args.model_name,
        "label_vocab_path": str(args.labels),
        "num_labels": len(labels),
        "num_labeled_nodes": labeled_nodes,
        "proposals_path": str(proposals_path),
    }
    graph_payload["pipeline"] = pipeline
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph_payload, indent=2), encoding="utf-8")
    print(f"Wrote labeled scene graph to {args.output}")
    print(f"labeled_nodes={labeled_nodes} labels={len(labels)}")


if __name__ == "__main__":
    main()
