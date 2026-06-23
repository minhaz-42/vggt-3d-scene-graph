# CVIU Submission Checklist

Target journal: Computer Vision and Image Understanding.

Official guide checked: https://www.sciencedirect.com/journal/computer-vision-and-image-understanding/publish/guide-for-authors

## Ready Files

- Anonymized manuscript: `paper/main.pdf`
- Anonymized LaTeX source: `paper/main.tex`
- Separate title page: `paper/title_page.tex`
- Highlights: `paper/highlights.txt`
- Cover letter draft: `docs/cviu_cover_letter_draft.md`
- Main figures:
  - `paper/figures/method_pipeline.png`
  - `paper/figures/evaluation_protocol.png`
  - `paper/figures/tum_rgbd_paper_subset_qualitative.png`
- Supplement-friendly figure:
  - `paper/figures/tum_rgbd_paper_subset_qualitative_all.png`
- Checked metrics:
  - `results/benchmark_tum_rgbd_paper_subset/sparse_view_checked_metrics.csv`
  - `paper/tables/tum_rgbd_paper_subset_checked_by_view.tex`
  - `paper/tables/tum_rgbd_paper_subset_checked_results.tex`

## CVIU Requirements Covered

- Double-anonymized review: `paper/main.tex` currently compiles with anonymous author
  details.
- Separate title page: `paper/title_page.tex` contains author, affiliation,
  corresponding email, funding, competing interest, and CRediT statement.
- Abstract length: 231 words, below the 250-word limit.
- Highlights: 5 bullet points, each under 85 characters.
- Tables: included as editable LaTeX, not images.
- Figures: regenerated as separate PNG files.
- Data availability statement: included before references.
- Generative AI declaration: included before references.
- No AI-generated artwork: figures are programmatically rendered diagrams or
  experiment visualizations.
- Compilation: `tectonic --keep-intermediates main.tex` succeeds without warnings.

## Needs User Confirmation Before Upload

- Confirm the author name, email, and affiliation on `paper/title_page.tex`.
- Confirm there are truly no competing interests.
- Confirm there was no specific grant funding.
- Decide whether to upload the generated results/annotation packets as supplementary
  material or provide them after acceptance/revision.
- Choose subscription/traditional publishing during submission to avoid APC charges.
- Do a final PDF read for figure/table placement and accidental identifying text.

## Current Scientific Risk

- The checked metrics use prediction-seeded 10-view annotations, not independent dense
  scene ground truth. The manuscript now states this clearly.
- External baselines are discussed but not run. This is the most likely reviewer
  request.
- The benchmark is five TUM RGB-D sequences. This is appropriate for a systems paper,
  but a reviewer may ask for more scenes or another dataset.
