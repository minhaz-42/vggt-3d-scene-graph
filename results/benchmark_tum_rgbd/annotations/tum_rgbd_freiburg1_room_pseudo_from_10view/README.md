# Annotation Packet

Source graph: `results/benchmark_tum_rgbd/tum_rgbd_freiburg1_room/views_10/scene_graph_labeled.json`

- `node_review.csv`: per-node label review sheet.
- `relation_review.csv`: aggregated labeled relation triplets with editable review columns.
- `annotation_draft.json`: prediction-derived annotation draft for evaluator input.
- `annotation_review.html`: visual node review sheet with representative SAM-mask crops.
- `annotation_from_review.json`: CSV-derived draft annotation JSON. Blank review fields currently fall back to prediction-derived values.

For real ground truth, edit the review CSVs after manual inspection, then run `scripts/build_annotations_from_review.py`.
