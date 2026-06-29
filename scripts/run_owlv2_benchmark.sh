#!/usr/bin/env bash
# Week-3 OWLv2 full benchmark driver: real open-vocab objects across all 5 paper-subset
# scenes x {3,5,8,10} views x {graph-fusion, geometry-only, 2d-only, semantic-lifting,
# fixed-shrink, proposed}. Reuses the cached VGGT geometry (symlinked) so no GPU is needed:
# only OWLv2 detection (MPS) + clip/dinov2 features (CPU) + graph/labels run locally.
#
# Idempotent: re-running resumes via --skip-existing. Run from repo root:  bash scripts/run_owlv2_benchmark.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH=src
PY=.venv/bin/python

MANIFEST=configs/datasets/tum_rgbd_paper_subset.json
VOCAB=configs/label_vocab/indoor_open_vocab.json
SAM_CKPT=models/sam_vit_b_01ec64.pth
CACHE=results/benchmark_tum_rgbd_paper_subset      # holds the cached vggt_geometry.{npz,json}
OUT="${OUT:-results/benchmark_owlv2}"
VIEWS="${VIEWS:-3 5 8 10}"
SCENES="tum_rgbd_freiburg1_room tum_rgbd_freiburg1_desk tum_rgbd_freiburg1_desk2 tum_rgbd_freiburg2_xyz tum_rgbd_freiburg3_long_office_household"

echo "==> [1/3] Seeding cached VGGT geometry via symlink (skips the geometry stage)"
for s in $SCENES; do
  for v in 03 05 08 10; do
    d="$OUT/$s/views_$v"; mkdir -p "$d"
    for f in vggt_geometry.npz vggt_geometry.json; do
      src="$ROOT/$CACHE/$s/views_$v/$f"
      if [ -f "$src" ]; then ln -sf "$src" "$d/$f"; else echo "   MISSING geometry: $src"; fi
    done
  done
done

echo "==> [2/3] graph-fusion: all stages (builds shared OWLv2 proposals + clip/dinov2 features + graph/labels)"
$PY scripts/run_benchmark.py --dataset "$MANIFEST" --output-root "$OUT" \
  --view-counts $VIEWS --proposal-backend owlv2 --label-vocab "$VOCAB" \
  --sam-checkpoint "$SAM_CKPT" --owlv2-device auto --feature-device cpu \
  --variant graph-fusion --skip-existing

echo "==> [3/3] other variants: reuse cached features, only graph+labels+figure"
for V in geometry-only 2d-only semantic-lifting fixed-shrink proposed; do
  extra=""
  [ "$V" = "fixed-shrink" ] && extra="--fixed-shrink 0.6"
  # proposed = the rank-normalized config that won at sparse views in Phase 1 (docs/phase1_results.md)
  [ "$V" = "proposed" ] && extra="--uncertainty-normalize rank --uncertainty-weight 0.3 --feature-uncertainty-weight 0.3 --bridge-tau 0.85"
  # shellcheck disable=SC2086
  $PY scripts/run_benchmark.py --dataset "$MANIFEST" --output-root "$OUT" \
    --view-counts $VIEWS --proposal-backend owlv2 --label-vocab "$VOCAB" \
    --variant "$V" --stages graph labels figure --skip-existing $extra \
    --index-output "$OUT/variants/$V/benchmark_index.json"
done

echo "ALL_DONE"
