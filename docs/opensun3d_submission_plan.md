# OpenSUN3D @ ECCV 2026 — submission plan (target: archival proceedings track)

**Venue:** OpenSUN3D — Workshop on Open-World 3D Scene Understanding and Representations, @ ECCV 2026,
Malmö (workshop Sept 8, 2026). The closest topical fit available (open-vocabulary 3D scene understanding).
**Deadline:** **Aug 1, 2026** · notify Aug 10 · camera-ready Aug 15. Submissions open Jun 15.
**Track:** **Proceedings (archival), 8 pages** excl. references, ECCV/LNCS format, **double-blind**.
(A non-archival 4/8-page track also exists — see the hedge at the bottom.)
**Sources:** https://opensun3d.github.io/ · ECCV/LNCS kit: https://www.overleaf.com/latex/templates/template-and-author-guidelines-for-eccv-submission/gycdswmdkkyv

## Hard constraints / desk-reject risks
- **8 pages** main content (refs unlimited). Our reframed draft is journal-length → must condense (plan below).
- **ECCV/LNCS template + font** — using another font/template can desk-reject. Use the official kit on Overleaf.
- **Double-blind** — title page `Anonymous`, no author/affiliation, no self-identifying links (the repo is
  public at github.com/minhaz-42 → do NOT link it in the submission; cite results generically).
- **One archival venue per paper** — archival submission here precludes archival-submitting the same paper
  to WACV E&D. (Hedge below preserves WACV.)

## 8-page structure (condense the journal draft → LNCS 8pp)

| § | Content | ~pages | Trim from current draft |
|---|---|---|---|
| 1 Intro | motivation + 4 contributions + the de-circularization lesson | 1.0 | keep tight; the circular-eval story is the hook |
| 2 Related work | open-vocab detection; open-vocab 3D scene graphs (ConceptGraphs delta); eval circularity | 0.75 | compress 4 paras → 3; foreground sparse-RGB-vs-ConceptGraphs delta |
| 3 Method | OWLv2 front-end + VGGT lifting + cross-view fusion + **duplicate-aware fusion**; uncertainty as ablated variant | 1.75 | keep dedup formal; shorten lifting/fusion prose; 1 method figure |
| 4 Benchmark + protocol | independent human-verified reference + de-circularization | 1.0 | merge "datasets/protocol/metrics" subsecs; 1 protocol figure |
| 5 Results | **consolidate 5 tables → 2**: (T1) 7-variant F1 incl. dedup + uncertainty; (T2) per-class + dedup mechanism. Text carries the deltas + IoU robustness | 2.0 | move full IoU sweep + full per-class table to supplementary/appendix |
| 6 Discussion + conclusion | over-counting mechanism; circular-eval takeaway; limitations; future work | 1.0 | compress; keep the "merge vs split" insight |
| figures | 1 method/pipeline + 1 qualitative scene graph (+ maybe 1 results curve) | (incl.) | regenerate from OWLv2/dedup outputs |

**Cuts / move to appendix:** full IoU-sweep table, full 18-row per-class table, the weight-sweep table
(state result in one sentence), reproduction-anchor details. Keep the variant table + the dedup-vs-baseline
deltas + per-class precision/recall summary in the main body.

## Gated on the Colab n≈30 run (in progress)
- When `expansion_bundle.tgz` lands → `tar xzf` → I draft refs (workflow) → `bash scripts/finish_expansion.sh`
  → fold n≈30 corroboration into T1/T2 (replaces the `\todo{}` slots). If it doesn't finish by ~mid-July,
  submit the **n=5 verified** version (workshop scale is acceptable) and note n≈30 as ongoing.

## Figures to regenerate (from OWLv2/dedup outputs)
1. **Pipeline**: sparse RGB → VGGT world points → OWLv2 boxes → lift → cross-view fuse → **dedup** → graph.
2. **Qualitative**: a desk scene graph (real labels) before/after dedup (monitor 10→4, desk 9→1).
3. (optional) F1-vs-views curve: dedup rising while baselines fall.

## Timeline (deadline Aug 1)
- now → ~Jul 5: Colab n≈30 finishes; integrate.
- ~Jul 5–18: LNCS 8-page port + condense + regenerate figures (me).
- ~Jul 18–28: review + tighten to 8pp (both).
- ~Jul 28–Aug 1: anonymization check, final compile on Overleaf, submit.

## Hedge to keep WACV E&D (Aug 28) open
Submit to OpenSUN3D's **non-archival track** (presents + gets feedback, not in proceedings) and send the
**archival** version to **WACV 2027 E&D (Aug 28)** — the ideal archival home for the benchmark/negative-result
angle. This avoids the one-archival-venue rule. Decide archival-vs-non-archival before Aug 1.

## Pre-submit checklist
- [ ] 8 pages in official ECCV/LNCS template (compiled on Overleaf)
- [ ] double-blind: no authors, no repo link, no self-citation tells
- [ ] n≈30 numbers folded in (or n=5 with ongoing note); all `\todo{}` resolved
- [ ] 2 main tables + 2–3 figures; overflow in appendix
- [ ] ConceptGraphs delta (sparse-RGB) stated in intro + related work
- [ ] references compile (splncs04 style)
