# ~30-scene expansion plan

Lifts the benchmark from n=5 to ~30 scenes for statistical power — the one remaining weakness in the
Week-3 results (`phase1_results_independent.md`). Geometry needs a GPU, so download + VGGT + OWLv2 run
on Colab; reference drafting + eval finish locally.

## Scenes (~30 object-rich TUM RGB-D sequences)

Source: official mirror `https://cvg.cit.tum.de/rgbd/dataset/<freiburgN>/<seq>.tgz` (the HF mirror only
has the 5 paper-subset scenes). Curated in `scripts/download_tum_official.py` (`DEFAULT_SEQUENCES`):
- **freiburg1 (8):** desk, desk2, room, 360, xyz, rpy, plant, teddy
- **freiburg2 (10):** desk, desk_with_person, xyz, coke, dishes, flowerbouquet, metallic_sphere,
  360_hemisphere, large_no_loop, large_with_loop
- **freiburg3 (12):** long_office_household(+_validation), cabinet, large_cabinet, teddy,
  sitting_static, sitting_xyz, sitting_halfsphere, walking_xyz, walking_static
All tarball URLs verified present (HTTP 200). Same sparse-view protocol as the paper subset: stride
10, 10 frames/scene, view counts {3,5,8,10}.

## Pipeline

1. **Colab (GPU + bandwidth) — one command:** `bash scripts/run_owlv2_expansion_colab.sh`
   - downloads the sequences + builds `configs/datasets/tum_rgbd_expanded.json`
   - VGGT geometry (cuda) → OWLv2 detection + clip/dinov2 features → graph + labels for all variants
     (graph-fusion, **graph-fusion-dedup**, proposed, fixed-shrink, 2d-only, geometry-only, semantic-lifting)
   - bundles `expansion_bundle.tgz` = frames + labeled scene graphs + manifest (heavy geometry/features
     excluded). Download + `tar xzf` it into the local repo.
2. **Local — reference drafting (Claude workflow):** generate the per-scene independent reference for
   the expanded scenes by reading the frames (the same draft + adversarial-verify workflow used for the
   5-scene set), writing `configs/evaluation/independent_labels_expanded.json`.
3. **Local — eval:** `bash scripts/finish_expansion.sh` → packets → eval all variants → comparison.

## Reference strategy (n=30 verification is impractical)

- The **5 paper-subset scenes stay the human-verified "gold" set** (the primary result).
- The ~25 new scenes use **two-pass VLM-drafted** references (draft + adversarial verify), clearly
  labeled `vlm-drafted` (not human-verified) — a larger-scale **corroboration** of the two findings,
  not the headline. A human spot-check of a random subset is the cheap way to bound its error.

## Expected outcome + caveats

- Confirm at scale: **uncertainty fusion gives no gain** (negative ablation) and **graph-fusion-dedup
  beats graph-fusion** (the positive contribution). Larger n tightens the sign-test (n=5 floored at
  p=0.062).
- **Dynamic scenes** (sitting_*/walking_*/desk_with_person have a moving person) violate VGGT's static
  multi-view assumption → geometry may be noisier; treat them as a stress subset and report static vs
  dynamic separately if they behave differently.
- Detection quality on never-seen sequences is unknown until run; OWLv2 thresholds may need a per-batch
  glance (books/cabinet were already recall-limited at n=5).

## Artifacts
- `scripts/download_tum_official.py` — official-mirror downloader + manifest builder.
- `scripts/run_owlv2_expansion_colab.sh` — one-command Colab GPU driver → `expansion_bundle.tgz`.
- `scripts/finish_expansion.sh` — local packets → eval → aggregate (after references are drafted).
