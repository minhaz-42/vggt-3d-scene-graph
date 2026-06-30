# Venue recommendation (researched 2026-06-30)

For the reframed paper (open-vocab sparse-view 3D scene graphs + **duplicate-aware fusion** +
**de-circularized human-verified benchmark** + **honest negative result**), submitting **ASAP
(within ~1–2 months)**, open to conference or journal, positioned benchmark/honest-eval-first.
Researched via a 102-agent fan-out with adversarial verification of every deadline/claim.

## TOP 3 (ranked)

### 1. WACV 2027 — Evaluations & Datasets (E&D) Track  ★ best fit, reachable
- **Type:** conference track (CVF/IEEE, peer-reviewed proceedings).
- **Deadline:** Round 2 — registration **Aug 21, 2026 (AoE)**, **paper Aug 28, 2026 (AoE)**, supp Aug 30; decisions Oct 9, 2026; conference Jan 4–8, 2027. (Round 1, Jun 26, already passed.)
- **Why it's near-perfect:** the E&D track *explicitly* welcomes "audits of existing datasets," "negative results, critical analyses," "analysis of strengths, limitations, or failure modes of existing benchmarks," and "rigorous reproduction, auditing, and stress-testing of prior evaluations" — judged on contribution to *evaluation practice*, not algorithmic novelty. Our de-circularization + benchmark + negative-result paper is essentially an exemplar submission. The modest scale and the negative result are **acceptance criteria here, not liabilities**.
- **Format:** CVF double-column, ~8 pages (needs template conversion from the current elsarticle).
- Source: wacv.thecvf.com/Conferences/2027/CallForPapers, /2027/Dates.

### 2. S3DSGR @ ECCV 2026 workshop — fast, low-risk de-risking option
- **Type:** ECCV workshop (proceedings). **Deadline July 15, 2026** (notify Jul 29, camera-ready Aug 14, workshop Sept 2026). 14-page ECCV'26 format, double-blind.
- **Fit:** partial — lists "foundation models for 3D geometric scene understanding" (matches the VGGT+OWLv2 pipeline) but centers on scene *generation*/large-scale reconstruction and does not list scene graphs / open-vocab 3D / sparse-view. Good for fast feedback + a citable workshop paper in ~2 weeks, in parallel with WACV.
- Source: s3dsgr.github.io, eccv.ecva.net/Conferences/2026/Dates.
- **Verify:** **OpenSUN3D @ ECCV 2026** (Open-World 3D Scene Understanding) is a *stronger topical* match (open-vocab 3D, affordances) but its 2026 paper deadline could not be reliably confirmed (one Aug 1 date was refuted) — **check the OpenSUN3D ECCV-2026 site directly**; if open, prefer it over S3DSGR for scope.

### 3. IEEE RA-L — rolling-deadline journal fallback
- **Type:** journal, **no fixed deadline** (submit anytime), ~4-month to publication, decisions ≤6 months.
- **Fit:** partial — RA-L publishes open-vocab 3D scene-graph work (CLIO, DovSG) but always tied to a robotic/navigation/manipulation task; would need light reframing toward embodied/robotic perception. Best if the ~30-scene expansion slips and you want no deadline pressure.

## Closed / unreachable for 2026 (don't target)
- **NeurIPS 2026 Evaluations & Datasets track** — *ideal scope* (same model as WACV's E&D) but full-paper deadline **May 6, 2026 passed**. Next: NeurIPS 2027 (the highest-prestige exact-scope home if we wait).
- **3DV 2026** — deadline Aug 18, 2025; conference already happened (Mar 2026). Next: 3DV 2027.
- **BMVC 2026** — deadline May 29, 2026 passed (no extensions).
- **ICBINB 2026** ("I Can't Believe It's Not Better") — deadline Jan 31 passed AND scoped to LLMs in 2026, not CV.
- **MLRC 2026** (NeurIPS reproducibility track) — requires prior TMLR acceptance first; not ASAP-feasible; scoped to reproducing *published* claims, not a system's internal ablation.

## Recommended plan
- **Primary: WACV 2027 E&D Track (Aug 28, 2026).** ~2 months out — enough time to land the ~30-scene corroboration, convert to the CVF template, and regenerate figures. The paper's positioning is tailor-made for this track.
- **Parallel/de-risk:** submit a short version to **S3DSGR (Jul 15)** or **OpenSUN3D (verify deadline)** for fast feedback.
- **Fallback if the expansion slips:** **IEEE RA-L** (rolling, reframed toward robotic perception), or hold for **NeurIPS 2027 E&D**.

## Positioning note (affects the paper regardless of venue)
**ConceptGraphs** (ICRA 2024, arXiv:2309.16650) is the canonical prior art — an open-vocab graph-structured 3D representation from 2D foundation models fused to 3D, architecturally near-identical to our pipeline. **But it consumes posed RGB-D sequences with depth; we target sparse RGB via feed-forward VGGT geometry.** Foreground that sparse-RGB delta + the honest-benchmark contribution as the novelty in the intro/related work (already cited as `gu2024conceptgraphs`).
