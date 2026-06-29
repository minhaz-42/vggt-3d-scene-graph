from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


"""Assign fused-node labels by score-weighted majority vote over detector (OWLv2) proposals.

Replaces the CLIP-text-similarity labeling stage (`assign_open_vocab_labels.py`) for the OWLv2
front-end. That stage was the heart of the project's scientific flaw: CLIP-per-patch mislabeled
SAM surface fragments as room-scale categories (floor/curtain/bed), and the eval graded CLIP
against CLIP. OWLv2 is a genuine open-vocab detector — each proposal already carries a real
`owlv2_label` + `owlv2_score`. The only thing fusion needs is to decide a single label per fused
node from its constituent proposals, which may disagree.

For each fused node we sum each label's detection scores across the node's proposals and pick the
argmax (score-weighted majority vote). This is stronger than a plain count vote (the existing
`fuse_node_cluster` tie-break) because a single high-confidence "keyboard" should outweigh several
low-confidence "desk" boxes that overlapped it. Output schema matches `assign_open_vocab_labels.py`
(node["label"], metadata.open_vocab_label / open_vocab_scores) so the figure + eval consume
`scene_graph_labeled.json` unchanged.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Label fused scene-graph nodes by score-weighted vote over OWLv2 proposal labels."
    )
    parser.add_argument("--scene-graph", type=Path, required=True)
    parser.add_argument(
        "--proposals",
        type=Path,
        help="Proposal/feature JSON carrying owlv2_label + owlv2_score per proposal "
        "(defaults to pipeline.proposals_path recorded in the scene graph).",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--score-key",
        default="owlv2_score",
        help="Per-proposal field used as the vote weight.",
    )
    parser.add_argument(
        "--label-key",
        default="owlv2_label",
        help="Per-proposal field holding the detector label.",
    )
    parser.add_argument("--top-k", type=int, default=5, help="How many ranked labels to record per node.")
    return parser.parse_args()


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


def _load_detector_proposals(
    path: Path, label_key: str, score_key: str
) -> dict[str, tuple[str, float]]:
    """Map proposal_id -> (detector_label, detection_score) for proposals that carry a label."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_id: dict[str, tuple[str, float]] = {}
    for record in payload.get("proposals", []):
        label = record.get(label_key)
        if not label:
            continue
        if score_key in record and record[score_key] is not None:
            score = float(record[score_key])
        elif record.get("confidence") is not None:
            score = float(record["confidence"])
        else:
            score = 1.0
        by_id[str(record.get("proposal_id"))] = (str(label), score)
    if not by_id:
        raise ValueError(
            f"No proposals in {path} carry a '{label_key}'. Is this an OWLv2 proposal/feature file?"
        )
    return by_id


def _vote(
    proposal_ids: list[str], detector: dict[str, tuple[str, float]], top_k: int
) -> tuple[str | None, list[dict[str, Any]]]:
    weight_by_label: dict[str, float] = defaultdict(float)
    count_by_label: dict[str, int] = defaultdict(int)
    for proposal_id in proposal_ids:
        hit = detector.get(str(proposal_id))
        if hit is None:
            continue
        label, score = hit
        weight_by_label[label] += score
        count_by_label[label] += 1
    if not weight_by_label:
        return None, []
    # Rank by summed score, breaking ties by vote count then label for determinism.
    ranked = sorted(
        weight_by_label.items(),
        key=lambda item: (item[1], count_by_label[item[0]], item[0]),
        reverse=True,
    )
    scores = [
        {
            "label": label,
            "score": round(weight, 6),
            "votes": count_by_label[label],
        }
        for label, weight in ranked[: max(top_k, 1)]
    ]
    return ranked[0][0], scores


def main() -> None:
    args = parse_args()
    graph_payload = json.loads(args.scene_graph.read_text(encoding="utf-8"))
    proposals_path = args.proposals or _proposal_path_from_graph(graph_payload, args.scene_graph)
    detector = _load_detector_proposals(proposals_path, args.label_key, args.score_key)

    labeled_nodes = 0
    for node in graph_payload.get("nodes", []):
        label, scores = _vote(node.get("proposal_ids", []), detector, args.top_k)
        if label is None:
            continue
        node["label"] = label
        metadata = dict(node.get("metadata", {}))
        metadata["open_vocab_label"] = label
        metadata["open_vocab_scores"] = scores
        metadata["open_vocab_backend"] = "owlv2_score_weighted_vote"
        node["metadata"] = metadata
        labeled_nodes += 1

    pipeline = dict(graph_payload.get("pipeline", {}))
    pipeline["labeling"] = {
        "backend": "owlv2_score_weighted_vote",
        "label_key": args.label_key,
        "score_key": args.score_key,
        "num_detector_proposals": len(detector),
        "num_labeled_nodes": labeled_nodes,
        "proposals_path": str(proposals_path),
    }
    graph_payload["pipeline"] = pipeline
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph_payload, indent=2), encoding="utf-8")
    print(f"Wrote labeled scene graph to {args.output}")
    print(f"labeled_nodes={labeled_nodes} detector_proposals={len(detector)}")


if __name__ == "__main__":
    main()
