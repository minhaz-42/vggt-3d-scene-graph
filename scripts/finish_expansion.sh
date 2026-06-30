#!/usr/bin/env bash
# Local finisher for the ~30-scene expansion, run AFTER:
#   1. the Colab bundle (frames + labeled scene graphs) is extracted into the repo, and
#   2. the independent reference for the expanded scenes has been drafted into
#      configs/evaluation/independent_labels_expanded.json (via the reference-drafting workflow).
# Builds reference packets -> evaluates all variants -> aggregates the comparison.
set -euo pipefail
export PYTHONPATH=src
PY="${PY:-.venv/bin/python}"
OUT="${OUT:-results/benchmark_owlv2_expanded}"
MANIFEST="${MANIFEST:-configs/datasets/tum_rgbd_expanded.json}"
LABELS="${LABELS:-configs/evaluation/independent_labels_expanded.json}"
VOCAB=configs/label_vocab/indoor_open_vocab.json

echo "==> build independent-reference packets"
$PY scripts/build_independent_reference.py --labels "$LABELS" \
  --output-root "$OUT/annotations" --reference-view-count 10 --packet-mode pseudo_reference \
  --annotation-file-name annotation_independent.json --label-vocab "$VOCAB"

echo "==> evaluate all variants vs the expanded independent reference"
$PY scripts/evaluate_sparse_view_annotations.py --dataset "$MANIFEST" \
  --results-root "$OUT" --annotations-root "$OUT/annotations" \
  --output "$OUT/variant_independent_metrics.csv" \
  --reference-view-count 10 --packet-mode pseudo_reference --annotation-file-name annotation_independent.json \
  --view-counts 3 5 8 10 \
  --variant graph-fusion --variant graph-fusion-dedup --variant proposed --variant fixed-shrink \
  --variant 2d-only --variant geometry-only --variant semantic-lifting

echo "==> aggregate the variant comparison"
$PY scripts/aggregate_variant_f1.py --metrics-csv "$OUT/variant_independent_metrics.csv" \
  --markdown-output "$OUT/variant_independent_comparison.md"
echo "DONE -> $OUT/variant_independent_comparison.md"
