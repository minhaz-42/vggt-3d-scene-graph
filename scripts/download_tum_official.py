from __future__ import annotations

import argparse
import json
import tarfile
import tempfile
import urllib.request
from pathlib import Path

"""Download object-rich TUM RGB-D sequences from the OFFICIAL mirror and build a sparse-view manifest.

The HF mirror (voviktyl/TUM_RGBD-SLAM) only carries the 5 paper-subset scenes; the official TUM site
hosts the full ~39-sequence benchmark. This streams each sequence's .tgz, samples N RGB frames by the
same stride protocol as the paper subset (start 0, stride 10, 10 frames), writes the
`<root>/<scene_id>/images/frame_000001.png` layout + a dataset manifest, and deletes the tarball.

URL pattern: https://cvg.cit.tum.de/rgbd/dataset/<freiburgN>/<sequence>.tgz  (freiburgN is read from
the sequence name). Idempotent: a scene whose frames already exist is skipped.
"""

BASE = "https://cvg.cit.tum.de/rgbd/dataset"

# ~30 object-rich sequences (the 5 paper-subset scenes + diverse desks/offices/rooms/household).
# Pure motion/structure-calibration scenes (floor, nostructure_*, structure_*texture_*) are excluded.
DEFAULT_SEQUENCES = [
    # freiburg1 — handheld cluttered desks / rooms
    "rgbd_dataset_freiburg1_desk", "rgbd_dataset_freiburg1_desk2", "rgbd_dataset_freiburg1_room",
    "rgbd_dataset_freiburg1_360", "rgbd_dataset_freiburg1_xyz", "rgbd_dataset_freiburg1_rpy",
    "rgbd_dataset_freiburg1_plant", "rgbd_dataset_freiburg1_teddy",
    # freiburg2 — desks + tabletop objects + larger rooms
    "rgbd_dataset_freiburg2_desk", "rgbd_dataset_freiburg2_desk_with_person", "rgbd_dataset_freiburg2_xyz",
    "rgbd_dataset_freiburg2_coke", "rgbd_dataset_freiburg2_dishes", "rgbd_dataset_freiburg2_flowerbouquet",
    "rgbd_dataset_freiburg2_metallic_sphere", "rgbd_dataset_freiburg2_360_hemisphere",
    "rgbd_dataset_freiburg2_large_no_loop", "rgbd_dataset_freiburg2_large_with_loop",
    # freiburg3 — office / household / cabinets (some dynamic: sitting/walking have a moving person)
    "rgbd_dataset_freiburg3_long_office_household", "rgbd_dataset_freiburg3_long_office_household_validation",
    "rgbd_dataset_freiburg3_cabinet", "rgbd_dataset_freiburg3_large_cabinet", "rgbd_dataset_freiburg3_teddy",
    "rgbd_dataset_freiburg3_sitting_static", "rgbd_dataset_freiburg3_sitting_xyz",
    "rgbd_dataset_freiburg3_sitting_halfsphere", "rgbd_dataset_freiburg3_walking_xyz",
    "rgbd_dataset_freiburg3_walking_static",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download object-rich TUM RGB-D sequences (official mirror) + build manifest.")
    p.add_argument("--sequences", nargs="+", default=DEFAULT_SEQUENCES)
    p.add_argument("--output-root", type=Path, default=Path("data/benchmark/tum_rgbd_expanded"))
    p.add_argument("--manifest-output", type=Path, default=Path("configs/datasets/tum_rgbd_expanded.json"))
    p.add_argument("--num-frames", type=int, default=10)
    p.add_argument("--start-index", type=int, default=0)
    p.add_argument("--frame-stride", type=int, default=10)
    p.add_argument("--sparse-view-counts", type=int, nargs="+", default=[3, 5, 8, 10])
    p.add_argument("--split", default="val")
    p.add_argument("--keep-tgz", action="store_true", help="Keep the downloaded tarballs (default: delete after extract).")
    p.add_argument("--force", action="store_true", help="Re-download/re-extract even if frames exist.")
    return p.parse_args()


def _category(sequence: str) -> str:
    for n in (1, 2, 3):
        if sequence.startswith(f"rgbd_dataset_freiburg{n}_"):
            return f"freiburg{n}"
    raise ValueError(f"Cannot derive freiburgN category from {sequence!r}")


def _scene_id(sequence: str) -> str:
    return "tum_rgbd_" + sequence.removeprefix("rgbd_dataset_")


def _sample_stride(names: list[str], count: int, start: int, stride: int) -> list[str]:
    stride = max(stride, 1)
    selected = names[max(start, 0)::stride][:count]
    if len(selected) < count:  # pad from the front if the stream is short
        seen = set(selected)
        for n in names:
            if n not in seen:
                selected.append(n); seen.add(n)
            if len(selected) >= count:
                break
    return selected


def _download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as resp, dest.open("wb") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)


def main() -> None:
    args = parse_args()
    scenes: list[dict[str, object]] = []
    tmp_root = Path(tempfile.gettempdir())

    for sequence in args.sequences:
        scene_id = _scene_id(sequence)
        images_dir = args.output_root / scene_id / "images"
        existing = sorted(images_dir.glob("frame_*.png"))
        if existing and not args.force:
            print(f"SKIP {scene_id}: {len(existing)} frames already present", flush=True)
            image_names = [p.name for p in existing][: args.num_frames]
            scenes.append(_scene(scene_id, sequence, images_dir, image_names, args))
            continue

        url = f"{BASE}/{_category(sequence)}/{sequence}.tgz"
        tgz = tmp_root / f"{sequence}.tgz"
        print(f"Downloading {sequence} <- {url}", flush=True)
        try:
            _download(url, tgz)
        except Exception as exc:  # noqa: BLE001 - skip and continue
            print(f"  SKIP {scene_id}: download failed ({exc})")
            continue

        with tarfile.open(tgz, "r:gz") as tar:
            rgb = sorted(m for m in tar.getnames() if f"{sequence}/rgb/" in m and m.endswith(".png"))
            if not rgb:
                print(f"  SKIP {scene_id}: no rgb/*.png in tarball"); tgz.unlink(missing_ok=True); continue
            picked = _sample_stride(rgb, args.num_frames, args.start_index, args.frame_stride)
            images_dir.mkdir(parents=True, exist_ok=True)
            image_names = []
            for i, member in enumerate(picked, start=1):
                local = f"frame_{i:06d}.png"
                with tar.extractfile(member) as src:
                    (images_dir / local).write_bytes(src.read())
                image_names.append(local)
        if not args.keep_tgz:
            tgz.unlink(missing_ok=True)
        print(f"  {scene_id}: {len(image_names)}/{len(rgb)} frames -> {images_dir}", flush=True)
        scenes.append(_scene(scene_id, sequence, images_dir, image_names, args))

    manifest = {
        "name": args.manifest_output.stem,
        "version": "0.1",
        "root": ".",
        "sparse_view_counts": args.sparse_view_counts,
        "metadata": {
            "stage": "expansion", "dataset": "TUM_RGBD", "source": "official_cvg_tum",
            "dataset_root": str(args.output_root.resolve()),
            "sample_mode": "stride", "start_index": args.start_index,
            "frame_stride": args.frame_stride, "num_frames_per_scene": args.num_frames,
        },
        "scenes": scenes,
    }
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(scenes)} scenes to {args.manifest_output}", flush=True)


def _scene(scene_id, sequence, images_dir, image_names, args):
    return {
        "scene_id": scene_id, "split": args.split, "scene_dir": str(images_dir.resolve()),
        "images": list(image_names),
        "metadata": {"dataset": "TUM_RGBD", "sequence": sequence, "source": "official_cvg_tum",
                     "has_ground_truth_instances": False, "has_scene_graph_labels": False},
    }


if __name__ == "__main__":
    main()
