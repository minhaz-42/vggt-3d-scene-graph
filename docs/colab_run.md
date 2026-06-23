# Running the Bigger Run on Google Colab (GPU)

The Mac is CPU-only (`torch.backends.mps.is_available()` is false; see
`docs/mac_feasibility.md`), so the scale-up benchmark runs on a Colab GPU. This guide and
the companion notebook (`notebooks/bigger_run_colab.ipynb`) reproduce the existing
5-scene paper subset and let you expand to ~30 scenes by editing one list.

> **Scope note.** This runs the **current** pipeline (the "graph-fusion" behavior). The
> baseline-ablation variants and the uncertainty-aware fusion change (Phase 1 of
> `docs/bigger_run_plan.md`) are not implemented yet — once they land, you add a
> `--variant` loop to the run cell. Nothing else changes.

---

## 0. Open a GPU runtime

In Colab: **Runtime → Change runtime type → Hardware accelerator → GPU** (T4 is fine).
Confirm with `!nvidia-smi`.

## 1. Clone the repo (private repo → needs a token)

The repo is **private**, so Colab needs a GitHub token (Personal Access Token with `repo`
scope, or fine-grained read access to this repo). The notebook prompts for it with
`getpass` so it is not stored in the notebook.

```python
import getpass
TOKEN = getpass.getpass("GitHub token: ")
USER, REPO = "minhaz-42", "vggt-3d-scene-graph"
!git clone https://{USER}:{TOKEN}@github.com/{USER}/{REPO}.git
%cd {REPO}
del TOKEN
```

If you later make the repo public, just `git clone https://github.com/minhaz-42/vggt-3d-scene-graph.git` with no token.

## 2. Install dependencies

Colab already ships a CUDA build of PyTorch — do **not** reinstall it (the requirements
file leaves it unpinned and could replace the CUDA wheel). The setup below installs
everything except torch/torchvision, plus the official VGGT and SAM packages.

```python
# non-torch deps (keeps Colab's CUDA torch)
!grep -vE "^torch" requirements.txt > /tmp/reqs_no_torch.txt
!pip install -q -r /tmp/reqs_no_torch.txt
!pip install -q -r requirements-optional.txt          # transformers, timm, segment-anything (git)
!pip install -q "git+https://github.com/facebookresearch/vggt.git"   # VGGT (model weights: facebook/VGGT-1B from HF)
!pip install -q -e .                                   # the vggt_scene_graph package
```

`numpy<2` is enforced by this project; if Colab warns about a numpy downgrade, do
**Runtime → Restart runtime** once, then continue from step 3 (skip steps 1–2; the clone
persists).

## 3. Download the SAM checkpoint

```python
!mkdir -p models
!wget -q -O models/sam_vit_b_01ec64.pth https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
```

## 4. Choose scenes and download the data

The download is deterministic (HF mirror `voviktyl/TUM_RGBD-SLAM`, stride sampling) and it
**rewrites the manifest with Colab-correct absolute paths**, so the local Mac paths don't
matter. List everything available first:

```python
!python scripts/download_tum_rgbd_subset.py --discover
```

Then pick your scenes. **5-scene reproduction** (default) vs **bigger run** = paste more
sequence names from the discover output:

```python
SEQUENCES = [
    "rgbd_dataset_freiburg1_room",
    "rgbd_dataset_freiburg1_desk",
    "rgbd_dataset_freiburg1_desk2",
    "rgbd_dataset_freiburg2_xyz",
    "rgbd_dataset_freiburg3_long_office_household",
    # add more here for the bigger run (up to ~30)
]
!python scripts/download_tum_rgbd_subset.py \
  --sequences {" ".join(SEQUENCES)} \
  --num-frames 10 --sample-mode stride --frame-stride 10 \
  --output-root data/benchmark/tum_rgbd_paper_subset \
  --manifest-output configs/datasets/tum_rgbd_paper_subset.json
```

## 5. Run the benchmark (GPU)

Note `--geometry-device cuda --feature-device cuda`, and **no** `--label-local-files-only`
(Colab downloads the CLIP label weights instead of reading a local cache):

```python
!python scripts/run_benchmark.py \
  --dataset configs/datasets/tum_rgbd_paper_subset.json \
  --output-root results/benchmark_tum_rgbd_paper_subset \
  --view-counts 3 5 8 10 \
  --sam-checkpoint models/sam_vit_b_01ec64.pth \
  --sam-points-per-side 12 --sam-max-proposals-per-image 20 \
  --label-vocab configs/label_vocab/indoor_open_vocab.json \
  --geometry-device cuda --feature-device cuda \
  --skip-existing
```

`--skip-existing` makes the run resumable if Colab disconnects: re-run the cell and it
continues. Use `--dry-run` first if you want to see the planned commands without inference.

## 6. Rebuild tables and figures

```python
!python scripts/summarize_scene_graph.py \
  results/benchmark_tum_rgbd_paper_subset/*/views_*/scene_graph_labeled.json \
  --output results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_summary.csv

!python scripts/evaluate_scene_graph.py \
  results/benchmark_tum_rgbd_paper_subset/*/views_*/scene_graph_labeled.json \
  --output results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_metrics.csv

!python scripts/export_sparse_view_tables.py \
  --summary results/benchmark_tum_rgbd_paper_subset/sparse_view_scene_graph_summary.csv \
  --latex-output paper/tables/tum_rgbd_paper_subset_results.tex \
  --markdown-output paper/tables/tum_rgbd_paper_subset_results.md \
  --aggregate-latex-output paper/tables/tum_rgbd_paper_subset_by_view.tex \
  --aggregate-markdown-output paper/tables/tum_rgbd_paper_subset_by_view.md
```

(Full rebuild chain incl. pseudo-reference metrics and figures is in
`docs/dataset_protocol.md`.)

## 7. Download the results

```python
!tar -czf results_bundle.tar.gz results paper/tables paper/figures
from google.colab import files
files.download("results_bundle.tar.gz")
```

Unpack locally into the repo root to bring the GPU results back to the Mac, then commit.

---

## Expected runtime

Order-of-magnitude on a free T4 (vs ~3.5 min/run on the Mac CPU):

| Scope | Runs (scenes × {3,5,8,10}) | Rough wall-clock |
| --- | --- | --- |
| 5-scene reproduction | 20 | ~15–30 min |
| ~30-scene bigger run | ~120 | ~1.5–3 h |

If you hit GPU OOM on the 10-view scenes, use a higher-RAM Colab runtime or drop `10` from
`--view-counts` for the largest scenes.

## One-shot alternative

Steps 2–6 are also wrapped in `scripts/run_colab_bigger_run.sh` — after steps 0–1 and 3–4
you can run `!bash scripts/run_colab_bigger_run.sh` instead of the individual cells.
