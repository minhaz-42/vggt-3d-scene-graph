#!/usr/bin/env bash
# One-command Colab/GPU driver for the ~30-scene expansion. Runs the WHOLE compute on GPU and
# produces a small bundle to finish locally (independent-reference drafting + eval).
#
# On a fresh Colab GPU runtime:
#   !git clone https://github.com/minhaz-42/vggt-3d-scene-graph.git && cd vggt-3d-scene-graph
#   !bash scripts/run_owlv2_expansion_colab.sh
#   # then download expansion_bundle.tgz (printed at the end) and extract it into the local repo.
#
# Env overrides: OUT (results dir), MANIFEST, VIEW_COUNTS, SEQUENCES (space-separated to subset),
#   SKIP_INSTALL=1.
set -euo pipefail

OUT="${OUT:-results/benchmark_owlv2_expanded}"
MANIFEST="${MANIFEST:-configs/datasets/tum_rgbd_expanded.json}"
VIEW_COUNTS="${VIEW_COUNTS:-3 5 8 10}"
VOCAB="configs/label_vocab/indoor_open_vocab.json"
SAM_CKPT="models/sam_vit_b_01ec64.pth"
export PYTHONPATH=src

if [ "${SKIP_INSTALL:-0}" != "1" ]; then
  echo "==> Installing deps (keep Colab CUDA torch)"
  grep -vE "^torch" requirements.txt > /tmp/reqs_no_torch.txt
  pip install -q -r /tmp/reqs_no_torch.txt
  pip install -q -r requirements-optional.txt
  pip install -q "git+https://github.com/facebookresearch/vggt.git"
  pip install -q -e .
fi
if [ ! -f "$SAM_CKPT" ]; then
  echo "==> Downloading SAM vit_b"; mkdir -p models
  wget -q -O "$SAM_CKPT" https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
fi

echo "==> [1/4] Download ~30 object-rich TUM sequences (official mirror) + build manifest"
SEQ_ARG=""; [ -n "${SEQUENCES:-}" ] && SEQ_ARG="--sequences $SEQUENCES"
# shellcheck disable=SC2086
python scripts/download_tum_official.py --manifest-output "$MANIFEST" $SEQ_ARG

echo "==> [2/4] graph-fusion: geometry (GPU) + OWLv2 + features + graph + labels"
# shellcheck disable=SC2086
python scripts/run_benchmark.py --dataset "$MANIFEST" --output-root "$OUT" \
  --view-counts $VIEW_COUNTS --proposal-backend owlv2 --label-vocab "$VOCAB" \
  --sam-checkpoint "$SAM_CKPT" --owlv2-device cuda --geometry-device cuda --feature-device cuda \
  --variant graph-fusion --skip-existing

echo "==> [3/4] other variants (reuse cached features): dedup + baselines + uncertainty ablation"
for V in graph-fusion-dedup geometry-only 2d-only semantic-lifting fixed-shrink proposed; do
  extra=""
  [ "$V" = "fixed-shrink" ] && extra="--fixed-shrink 0.6"
  [ "$V" = "graph-fusion-dedup" ] && extra="--dedup-iou 0.1"
  [ "$V" = "proposed" ] && extra="--uncertainty-normalize rank --uncertainty-weight 0.3 --feature-uncertainty-weight 0.3 --bridge-tau 0.85"
  # shellcheck disable=SC2086
  python scripts/run_benchmark.py --dataset "$MANIFEST" --output-root "$OUT" \
    --view-counts $VIEW_COUNTS --proposal-backend owlv2 --label-vocab "$VOCAB" \
    --variant "$V" --stages graph labels figure --skip-existing $extra \
    --index-output "$OUT/variants/$V/benchmark_index.json"
done

echo "==> [4/4] Bundle frames + labeled scene graphs + manifest for local finishing"
BUNDLE=expansion_bundle.tgz
# frames (for independent-reference drafting) + labeled graphs (for eval) + manifest. Exclude
# heavy geometry/features/npz so the bundle stays small.
tar czf "$BUNDLE" \
  "$MANIFEST" \
  data/benchmark/tum_rgbd_expanded/*/images \
  $(find "$OUT" -name scene_graph_labeled.json) \
  $(find "$OUT" -name benchmark_index.json)
echo "ALL_DONE — created $BUNDLE ($(du -h "$BUNDLE" | cut -f1)). Download it, then locally:"
echo "    tar xzf expansion_bundle.tgz    # from repo root"
echo "    # then ask Claude to draft references (workflow) + run scripts/finish_expansion.sh"
