#!/usr/bin/env bash
# One-shot Colab/GPU driver for the bigger run. Run from the repo root AFTER cloning.
# Idempotent: re-running resumes via --skip-existing.
#
# Usage:
#   bash scripts/run_colab_bigger_run.sh
#   SEQUENCES="rgbd_dataset_freiburg1_room rgbd_dataset_freiburg1_desk ..." bash scripts/run_colab_bigger_run.sh
#
# Env overrides:
#   SEQUENCES   space-separated TUM sequence folder names (default: 5 paper-subset scenes)
#   OUTPUT_ROOT results dir (default: results/benchmark_tum_rgbd_paper_subset)
#   MANIFEST    manifest path (default: configs/datasets/tum_rgbd_paper_subset.json)
#   VIEW_COUNTS (default: "3 5 8 10")
#   SKIP_INSTALL=1 to skip dependency install (already installed)
set -euo pipefail

OUTPUT_ROOT="${OUTPUT_ROOT:-results/benchmark_tum_rgbd_paper_subset}"
MANIFEST="${MANIFEST:-configs/datasets/tum_rgbd_paper_subset.json}"
VIEW_COUNTS="${VIEW_COUNTS:-3 5 8 10}"
SAM_CKPT="models/sam_vit_b_01ec64.pth"
SEQUENCES="${SEQUENCES:-rgbd_dataset_freiburg1_room rgbd_dataset_freiburg1_desk rgbd_dataset_freiburg1_desk2 rgbd_dataset_freiburg2_xyz rgbd_dataset_freiburg3_long_office_household}"

if [ "${SKIP_INSTALL:-0}" != "1" ]; then
  echo "==> Installing dependencies (keeping Colab's CUDA torch)"
  grep -vE "^torch" requirements.txt > /tmp/reqs_no_torch.txt
  pip install -q -r /tmp/reqs_no_torch.txt
  pip install -q -r requirements-optional.txt
  pip install -q "git+https://github.com/facebookresearch/vggt.git"
  pip install -q -e .
fi

if [ ! -f "$SAM_CKPT" ]; then
  echo "==> Downloading SAM vit_b checkpoint"
  mkdir -p models
  wget -q -O "$SAM_CKPT" https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
fi

echo "==> Downloading TUM RGB-D data + (re)building manifest with local paths"
# shellcheck disable=SC2086
python scripts/download_tum_rgbd_subset.py \
  --sequences $SEQUENCES \
  --num-frames 10 --sample-mode stride --frame-stride 10 \
  --output-root data/benchmark/tum_rgbd_paper_subset \
  --manifest-output "$MANIFEST"

echo "==> Running benchmark on GPU"
# shellcheck disable=SC2086
python scripts/run_benchmark.py \
  --dataset "$MANIFEST" \
  --output-root "$OUTPUT_ROOT" \
  --view-counts $VIEW_COUNTS \
  --sam-checkpoint "$SAM_CKPT" \
  --sam-points-per-side 12 --sam-max-proposals-per-image 20 \
  --label-vocab configs/label_vocab/indoor_open_vocab.json \
  --geometry-device cuda --feature-device cuda \
  --skip-existing

echo "==> Rebuilding summary + metrics + tables"
python scripts/summarize_scene_graph.py \
  "$OUTPUT_ROOT"/*/views_*/scene_graph_labeled.json \
  --output "$OUTPUT_ROOT/sparse_view_scene_graph_summary.csv"

python scripts/evaluate_scene_graph.py \
  "$OUTPUT_ROOT"/*/views_*/scene_graph_labeled.json \
  --output "$OUTPUT_ROOT/sparse_view_scene_graph_metrics.csv"

python scripts/export_sparse_view_tables.py \
  --summary "$OUTPUT_ROOT/sparse_view_scene_graph_summary.csv" \
  --latex-output paper/tables/tum_rgbd_paper_subset_results.tex \
  --markdown-output paper/tables/tum_rgbd_paper_subset_results.md \
  --aggregate-latex-output paper/tables/tum_rgbd_paper_subset_by_view.tex \
  --aggregate-markdown-output paper/tables/tum_rgbd_paper_subset_by_view.md

# --- Phase 1: baseline/ablation variants (reuse the cached upstream features) ---
VARIANTS="${VARIANTS:-geometry-only 2d-only semantic-lifting fixed-shrink proposed}"
if [ "${RUN_VARIANTS:-1}" = "1" ]; then
  echo "==> Running fusion variants (graph+labels+figure, features reused): $VARIANTS"
  for V in $VARIANTS; do
    extra=""
    [ "$V" = "fixed-shrink" ] && extra="--fixed-shrink ${FIXED_SHRINK:-0.6}"
    # proposed auto-enables uncertainty (no extra flag needed).
    # shellcheck disable=SC2086
    python scripts/run_benchmark.py --dataset "$MANIFEST" --output-root "$OUTPUT_ROOT" \
      --view-counts $VIEW_COUNTS --variant "$V" --stages graph labels figure --skip-existing \
      --label-vocab configs/label_vocab/indoor_open_vocab.json $extra \
      --index-output "$OUTPUT_ROOT/variants/$V/benchmark_index.json"
  done

  echo "==> Structural variant comparison (annotation-free)"
  python scripts/export_variant_comparison.py --results-root "$OUTPUT_ROOT" \
    --markdown-output "$OUTPUT_ROOT/variant_structural_comparison.md" \
    --csv-output "$OUTPUT_ROOT/variant_structural_comparison.csv"

  # Labeled object/relation F1 per variant vs the 10-view annotation (needs annotation packets).
  ANN="$OUTPUT_ROOT/annotations"
  if [ -d "$ANN" ]; then
    echo "==> Per-variant labeled F1 vs 10-view annotation"
    python scripts/evaluate_sparse_view_annotations.py --dataset "$MANIFEST" \
      --results-root "$OUTPUT_ROOT" --annotations-root "$ANN" \
      --output "$OUTPUT_ROOT/variant_checked_metrics.csv" \
      --reference-view-count 10 --packet-mode pseudo_reference \
      --annotation-file-name annotation_checked.json \
      --variant graph-fusion --variant geometry-only --variant 2d-only \
      --variant semantic-lifting --variant fixed-shrink --variant proposed \
      || echo "   (skipped: annotation_checked.json not present for all scenes)"
  fi
fi

echo "==> Done. Bundle results with:"
echo "    tar -czf results_bundle.tar.gz $OUTPUT_ROOT paper/tables paper/figures"
