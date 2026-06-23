from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from pathlib import Path

import cv2
import numpy as np

from .types import MaskProposal
from .masking import encode_binary_mask_rle


@dataclass(slots=True)
class ProposalRecord:
    proposal_id: str
    view_id: str
    bbox_xyxy: tuple[int, int, int, int]
    mask_area: int
    image_area: int
    confidence: float
    backend: str
    label_hint: str | None = None
    mask_rle: dict[str, Any] | None = None
    features: dict[str, Any] | None = None


def mask_to_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    rows, cols = np.where(mask > 0)
    if rows.size == 0 or cols.size == 0:
        return (0, 0, 0, 0)
    return (int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1)


def _foreground_components(image_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, threshold1=50, threshold2=140)

    kernel = np.ones((5, 5), dtype=np.uint8)
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    dilated = cv2.dilate(closed, kernel, iterations=1)
    return dilated


def connected_component_proposals(
    image_path: Path,
    view_id: str | None = None,
    min_area: int = 512,
    max_proposals: int = 20,
) -> list[MaskProposal]:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    view_id = view_id or image_path.stem
    foreground = _foreground_components(image)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(foreground, connectivity=8)
    image_area = image.shape[0] * image.shape[1]

    proposals: list[MaskProposal] = []
    for label in range(1, num_labels):
        x, y, width, height, area = stats[label]
        area = int(area)
        if area < min_area:
            continue
        if area > int(0.85 * image_area):
            continue
        if width < 8 or height < 8:
            continue

        mask = labels == label
        proposal_id = f"{view_id}_cc_{label:03d}"
        proposals.append(
            MaskProposal(
                proposal_id=proposal_id,
                view_id=view_id,
                mask=mask,
                bbox_xyxy=(int(x), int(y), int(x + width), int(y + height)),
                confidence=min(1.0, area / max(float(image_area), 1.0)),
                label_hint="opencv_component",
            )
        )

    proposals.sort(key=lambda proposal: int(proposal.mask.sum()), reverse=True)
    return proposals[:max_proposals]


def proposal_to_record(
    proposal: MaskProposal,
    backend: str = "opencv_connected_components",
    include_mask: bool = True,
) -> ProposalRecord:
    mask_area = int(proposal.mask.sum())
    return ProposalRecord(
        proposal_id=proposal.proposal_id,
        view_id=proposal.view_id,
        bbox_xyxy=proposal.bbox_xyxy,
        mask_area=mask_area,
        image_area=int(proposal.mask.size),
        confidence=proposal.confidence,
        backend=backend,
        label_hint=proposal.label_hint,
        mask_rle=encode_binary_mask_rle(proposal.mask) if include_mask else None,
    )


def proposal_record_dict(
    proposal: MaskProposal,
    backend: str = "opencv_connected_components",
    include_mask: bool = True,
) -> dict[str, object]:
    payload = asdict(proposal_to_record(proposal, backend=backend, include_mask=include_mask))
    return {key: value for key, value in payload.items() if value is not None}
