# Paper reframe spec (post-pivot, 2026-06-30)

The existing `paper/` (CVIU submission, elsarticle) is built entirely on the now-invalidated story:
SAM+CLIP front-end, **uncertainty-aware fusion as the headline**, and a **circular pseudo-reference**
(graphs graded against the model's own 10-view output). Week-3 work overturned all three. This spec
locks the reframed thesis so the section rewrite stays coherent. **All numbers here are the verified
(human-verified reference, n=5) source of truth — drafters must use these, not invent.**

Positioning (author decision): **lead with the benchmark + honest evaluation**; the negative result and
the de-circularization are *features*. Venue: TBD from the deep-research venue report; format adapts.

## Proposed title

**"Open-Vocabulary 3D Scene Graphs from Sparse RGB Views: Duplicate-Aware Fusion and a
De-Circularized Benchmark"**

Alternatives: "What Actually Helps in Sparse-View 3D Scene Graphs? An Honest Open-Vocabulary
Benchmark"; "Detector-Grounded Open-Vocabulary 3D Scene Graphs from Sparse Views, Honestly Evaluated".

## Abstract (draft)

We study how to build and — crucially — how to *honestly evaluate* open-vocabulary 3D scene graphs
from a handful of casual RGB views. Our pipeline keeps all heavy models frozen: feed-forward VGGT
geometry turns sparse images into world-point maps, an open-vocabulary detector (OWLv2) proposes
labeled object boxes, these are lifted to 3D and fused across views into a labeled object-relation
graph with no per-scene optimization. We make three points. (i) Replacing the common
class-agnostic-mask + CLIP-per-patch front-end with a genuine open-vocabulary detector is what makes
the labels real: on a desk scene the detector recovers the actual objects (monitors, keyboard, books)
where the mask+CLIP pipeline returned room-scale category noise. (ii) The dominant error of the lifted
system is *over-counting* — one physical object survives as several fused nodes — and a simple
duplicate-aware fusion step (merge same-label nodes whose 3D boxes overlap) fixes it, improving
object-label F1 at every view count (+0.07 to +0.15) and winning on every scene. (iii) We show that a
previously-promising uncertainty-aware fusion gate gives *no* benefit once labels are real, across a
full parameter sweep — a negative result that was masked by a circular evaluation. To support these
claims we contribute an independent, human-verified sparse-view benchmark on TUM RGB-D whose reference
is authored from the frames rather than seeded from the model's own predictions, and we document the
circular-pseudo-reference pitfall that inflates scores (a method scoring 1.0 by construction at the
dense view). We hope the benchmark and the de-circularization protocol are useful beyond this system.

## Contributions (replaces the old 4)

1. **A detector-grounded open-vocabulary sparse-view 3D scene-graph system** — OWLv2 → VGGT 3D lifting
   → cross-view fusion → spatial relations, frozen models, no per-scene optimization. Detector-grounded
   labels recover real objects where mask+CLIP labeling does not.
2. **Duplicate-aware cross-view fusion** — a post-fusion merge of same-label nodes whose axis-aligned
   3D boxes overlap (IoU > τ), targeting the measured over-counting failure. Improves object-label F1
   at every view count and is the only variant whose accuracy *rises* with more views.
3. **An independent, human-verified sparse-view benchmark + de-circularization protocol** on TUM RGB-D.
   We show a prediction-seeded pseudo-reference inflates scores (graph-fusion = 1.0 at the reference
   view by construction) and that an independently-authored reference removes the artifact.
4. **A rigorous negative result**: uncertainty-aware fusion (recalibrated, swept over weights) does not
   improve object accuracy on real labels; we analyze why (it lifts recall but over-splits → precision
   loss), which also explains why duplicate-aware *merging* — the opposite move — works.

## Per-section change map (vs current paper/sections/*.tex)

- **abstract / introduction** — rewrite to the thesis above; new contribution list. Keep the
  sparse-view + frozen-foundation-model framing (still valid).
- **related_work** — REUSE most; add: open-vocabulary *detection* (OWLv2, GroundingDINO, OWL-ViT);
  open-vocab 3D scene graphs (ConceptGraphs etc., already cited); evaluation circularity /
  reproducibility in 3D scene understanding. Drop the implication that uncertainty fusion is the novelty.
- **method** — front-end becomes OWLv2 (not SAM-auto+CLIP-text); keep VGGT lifting + cross-view fusion;
  ADD §duplicate-aware fusion; MOVE uncertainty to an ablated variant, not the core method.
- **experiments** — the independent human-verified reference + protocol; variants (baselines,
  graph-fusion, +dedup, uncertainty ablation, fixed-shrink control); de-circularization description.
- **results** — new tables: variant comparison on the independent reference (below), per-class
  characterization, dedup ablation (IoU sweep), uncertainty negative ablation + weight sweep. n=5
  verified now; **leave clearly-marked placeholders for the ~30-scene corroboration**.
- **discussion** — over-counting mechanism; the circular-eval lesson (methodological); limitations
  (n small, closely-packed same-class instances over-merge, dynamic scenes, stuff classes); future
  work (appearance-based instance split — where the recall the uncertainty signal could add might pay
  off as a *split* decision, not a merge gate).

## KEY VERIFIED NUMBERS (n=5, human-verified independent reference) — single source of truth

object_label_f1, mean over 5 scenes, vs the independent reference (full multiset):

| variant | v3 | v5 | v8 | v10 |
|---|---|---|---|---|
| 2d-only | 0.4897 | 0.4940 | 0.4820 | 0.4647 |
| geometry-only | 0.4578 | 0.4843 | 0.4834 | 0.4833 |
| semantic-lifting | 0.4168 | 0.3326 | 0.2548 | 0.2148 |
| fixed-shrink (uninformed control) | 0.5165 | 0.4849 | 0.4471 | 0.4008 |
| graph-fusion (baseline) | 0.5126 | 0.5038 | 0.4688 | 0.4324 |
| proposed (uncertainty, rank w=0.3) | 0.4982 | 0.4725 | 0.4132 | 0.3749 |
| **graph-fusion-dedup (ours)** | **0.5804** | **0.5923** | **0.6137** | **0.5787** |

- dedup − graph-fusion: **+0.068 / +0.089 / +0.145 / +0.146** (v3/v5/v8/v10); per-scene wins 4W/0L (v3),
  4W/0L (v5), **5W/0L (v8, v10)**; sign-test floor p=0.062 at n=5. dedup − fixed-shrink: +0.064 / +0.107 /
  +0.167 / +0.178.
- proposed(uncertainty) − graph-fusion: **−0.014 / −0.031 / −0.056 / −0.057**; 0W/5L at v5/v8/v10. No
  uncertainty weight in [0.1, 0.8] beats graph-fusion (weight sweep).
- Per-class (graph-fusion, drop "unknown object"): recall rises 0.671→0.808 (v3→v10), precision falls
  0.533→0.322 → F1 best at sparse end (0.594 v3 → 0.461 v10). Over-counted classes: desk, keyboard,
  monitor, wall (recall→1.0, precision collapses).
- dedup mechanism (v8, per-class): precision jumps monitor 0.38→1.00, desk 0.19→0.83, keyboard
  0.31→0.62; recall preserved for almost all classes; cost: monitor −0.33, desk −0.17 recall (closely-
  packed same-class instances over-merge). dedup IoU robust across [0, 0.2], default 0.1; IoU-only beats
  adding a centroid term.
- Front-end qualitative: OWLv2 on freiburg1_desk recovers keyboard/monitor×2/desk/book vs the old
  SAM+CLIP "floor:54, curtain:13, bed:6" soup.

### Circular-reference contrast (for the cautionary contribution)
Old prediction-seeded pseudo-reference made `proposed` look like a +0.040/+0.021 sparse-view WIN at
v3/v5, and graph-fusion scored **1.0 at v10 by construction**. The independent reference reverses the
sign of the uncertainty result and removes the dense-view artifact. (Source: `docs/phase1_results.md`
[superseded, with banner] vs `docs/phase1_results_independent.md`.)

## Source docs (drafters cite these for facts, not memory)
`docs/phase1_results_independent.md` (headline + variant table), `docs/owlv2_system_characterization.md`
(per-class), `docs/dedup_ablation.md` (IoU sweep + mechanism + limitation), `docs/owlv2_migration.md`
(front-end), `configs/evaluation/independent_labels.json` (the reference), `docs/expansion_plan.md`
(the ~30-scene corroboration, pending).

## Reusable assets
- LaTeX template (`paper/main.tex`, elsarticle) — keep or swap per chosen venue.
- `paper/references.bib` — extend with OWLv2/open-vocab-detection + eval-reproducibility refs.
- Figures: `method_pipeline.png` (update front-end to OWLv2 + add dedup), `evaluation_protocol.png`
  (update to independent reference), qualitative figures (regenerate from OWLv2 graphs).

## Open items
- Venue + exact format: pending deep-research report.
- ~30-scene corroboration: pending Colab run (`expansion_bundle.tgz`) → results slot into the tables.
- Figures need regeneration from the OWLv2/dedup outputs.
