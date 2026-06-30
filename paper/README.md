# Paper — Open-Vocabulary 3D Scene Graphs from Sparse RGB Views

Duplicate-Aware Fusion and a De-Circularized Benchmark.

**Target venue:** ACCV 2026 (deadline **Jul 5, 2026**; Springer LNCS, 14 pages excl. references,
double-blind, supplementary allowed). **Fallback:** OpenSUN3D @ ECCV 2026 (Aug 1; LNCS, 8 pages).

## Build
`main.tex` uses the Springer LNCS base class. For the real submission, open the **official ACCV 2026
LNCS author kit** on Overleaf (accv2026.org/submissions/author-guidelines/) and drop these files in —
the kit fixes the required font; a wrong template risks desk-rejection. Local compile (if a TeX
distribution is available):

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

## Layout
- `main.tex` — LNCS paper; `\input`s the sections.
- `sections/` — abstract, introduction, related_work, method, experiments, results, discussion.
- `tables/tum_rgbd_paper_subset_plan.tex` — the 5 human-verified gold-core benchmark scenes.
- `references.bib`.
- The method pipeline is a TikZ diagram inside `method.tex` (no external image). A qualitative
  figure is still TODO.

## Results provenance
All numbers are on the **28-scene independent benchmark** (5 human-verified + 23 two-pass
VLM-drafted references). Headline: duplicate-aware fusion beats the no-uncertainty baseline by
+0.06–0.12 object-label F1 (22–27/28 scenes, p<0.001); uncertainty-aware fusion is a negative result.
See `docs/opensun3d_submission_plan.md`, `docs/phase1_results_independent.md`, and the raw scores in
`results/benchmark_owlv2_expanded/`.
