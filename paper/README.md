# Paper Draft

Compile from this directory:

```bash
cd paper
tectonic main.tex
```

The local environment does not have `pdflatex`, but `tectonic` is available and
successfully builds:

```text
paper/main.pdf
```

If compiling with a traditional TeX distribution, the equivalent command sequence is:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Current generated tables and figures:

```text
paper/tables/tum_rgbd_sparse_view.tex
paper/tables/tum_rgbd_paper_subset_by_view.tex
paper/tables/tum_rgbd_paper_subset_results.tex
paper/tables/tum_rgbd_paper_subset_pseudo_reference_by_view.tex
paper/figures/method_pipeline.png
paper/figures/evaluation_protocol.png
paper/figures/tum_rgbd_paper_subset_qualitative.png
paper/main.pdf
```

Regenerate a summary table from the current TUM CSV with:

```bash
PYTHONPATH=../src ../.venv/bin/python ../scripts/export_paper_tables.py \
  --summary ../results/benchmark_tum_rgbd/scene_graph_summary.csv \
  --latex-output tables/generated_scene_graph_summary.tex \
  --markdown-output tables/generated_scene_graph_summary.md
```
