from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path

import cv2


@dataclass(slots=True)
class PairMatchReport:
    left_image: str
    right_image: str
    left_keypoints: int
    right_keypoints: int
    raw_matches: int
    good_matches: int
    match_ratio: float


def _load_gray(path: Path):
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return image


def pairwise_orb_match(
    left_path: Path,
    right_path: Path,
    max_features: int = 3000,
    ratio_threshold: float = 0.75,
) -> PairMatchReport:
    orb = cv2.ORB_create(nfeatures=max_features)
    left = _load_gray(left_path)
    right = _load_gray(right_path)

    left_keypoints, left_descriptors = orb.detectAndCompute(left, None)
    right_keypoints, right_descriptors = orb.detectAndCompute(right, None)

    if left_descriptors is None or right_descriptors is None:
        return PairMatchReport(
            left_image=left_path.name,
            right_image=right_path.name,
            left_keypoints=len(left_keypoints),
            right_keypoints=len(right_keypoints),
            raw_matches=0,
            good_matches=0,
            match_ratio=0.0,
        )

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    knn_matches = matcher.knnMatch(left_descriptors, right_descriptors, k=2)
    good_matches = []
    for pair in knn_matches:
        if len(pair) < 2:
            continue
        first, second = pair
        if first.distance < ratio_threshold * second.distance:
            good_matches.append(first)

    denominator = max(1, min(len(left_keypoints), len(right_keypoints)))
    return PairMatchReport(
        left_image=left_path.name,
        right_image=right_path.name,
        left_keypoints=len(left_keypoints),
        right_keypoints=len(right_keypoints),
        raw_matches=len(knn_matches),
        good_matches=len(good_matches),
        match_ratio=len(good_matches) / denominator,
    )


def pairwise_scene_report(image_paths: list[Path]) -> list[dict[str, object]]:
    reports = []
    for left_path, right_path in combinations(image_paths, 2):
        reports.append(asdict(pairwise_orb_match(left_path, right_path)))
    return reports
