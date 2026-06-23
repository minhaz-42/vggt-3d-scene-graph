# Uncertainty-Aware Cross-View Fusion (Proposed variant) — Implementation Spec

Locked design for Phase 1 of `docs/bigger_run_plan.md`. Produced by a design panel
(5 independent proposals → 3 adversarial judging lenses each → synthesis). Winner: the
uncertainty-modulated fusion gate (mean judge score 25.33/30), with the `max` aggregator
and an anti-bridge veto grafted from the runner-up. Line anchors verified against live code.

## 1. Chosen mechanism

**Name:** *Uncertainty-modulated conservative fusion gate with a confident-core seeding rule.*

**Core approach.** Per cross-view candidate pair, the effective distance threshold is
*shrunk* and the effective feature-similarity bar is *raised* in proportion to the pair's
joint uncertainty, so uncertain pairs must be geometrically closer and semantically more
similar before an edge (hence a merge) is created. This edits exactly the two gate
comparisons (`graph_builder.py:88` and `:92`) that decide *edge addition* — the only lever
that changes `connected_components` topology (edge weights are ignored by clustering).

**Grafted ideas:**

- **From "Conservative asymmetric merge" (runner-up): `max(u_L,u_R)` aggregator + anti-bridge rule.**
  A merge is only as trustworthy as its least-certain participant, so `max` is the default
  joint-uncertainty aggregator. The runner-up's key insight — *uncertain nodes must not act
  as transitive bridges between two confident objects* — is implemented cheaply as a
  **bridge veto** (two uncertain endpoints may not seed a merge), neutralizing the biggest
  baseline failure mode without the two-stage rewrite.
- **From the rigor lens: single-knob decomposability.** The two modulation strengths
  (`uncertainty_weight` for geometry, `feature_uncertainty_weight` for appearance) are
  independently ablatable and promoted to *primary* comparisons.
- **From the skeptic lens: a uniform-shrink control.** A mandatory `fixed_shrink` control
  variant (constant tightening with *zero* uncertainty info) proves the gain comes from
  uncertainty being informative, not from merely tightening the gate.

We **reject** routing through `merge_score`/`build_candidate_graph` (dead code, lines
32–61): different semantics, cannot reproduce current outputs.

## 2. Exact formula

**Uncertainty convention:** `ObjectNode.uncertainty ∈ [0,1]` is an *UNcertainty*. **`0` =
certain, `1` = maximally uncertain.** Default `0.0` (`types.py:44`); populated in
`lifting.py:192–194` as `clip(0.7·(1−conf) + 0.3·compactness, 0, 1)`. Higher ⇒ stronger
gate tightening.

For each cross-view pair `(L,R)` that passed the same-view gate (`graph_builder.py:84`):

```
u_L = float(L.uncertainty)              # [0,1], 0=certain
u_R = float(R.uncertainty)
u_pair = max(u_L, u_R)                   # default; "mean" selectable for ablation
u_pair = clip(u_pair, 0.0, 1.0)

# (1) DISTANCE GATE — shrink threshold as uncertainty rises
shrink = max(1.0 - uncertainty_weight * u_pair, min_shrink)     # ∈ [min_shrink, 1]
eff_distance_threshold = distance_threshold * shrink            # ≤ distance_threshold

# (2) FEATURE GATE — raise cosine bar (only when feature gate active)
gap = 1.0 - feature_similarity_threshold
eff_feature_threshold = min(
    feature_similarity_threshold + feature_uncertainty_weight * u_pair * gap,
    max_feature_threshold,
)                                                              # ≥ feature_similarity_threshold

# edge admitted iff:
#   centroid_distance(L,R) <= eff_distance_threshold
#   AND (feature gate inactive OR cosine(L.feature,R.feature) >= eff_feature_threshold)
#   AND NOT bridge_veto(L,R)
```

`centroid_distance` = `graph_builder.py:23–24` (L2 of `centroid_xyz`, world meters);
`cosine` = `:11–20` — **add a `left.shape != right.shape → return 0.0` dim guard** (concat
clip+dinov2 vs single-backend features differ in dim). **Edge weight stays on the BASE
threshold** (`:97` unchanged) so stored attributes are reproduction-identical.

**Bridge veto.** A node is *uncertain* iff `uncertainty > bridge_tau`. Forbid edge `(L,R)`
when **both** endpoints are uncertain — bars two uncertain proposals from seeding a merge,
while still letting an uncertain node attach to a confident one. Only ever removes edges;
`bridge_tau ≥ 1.0` ⇒ strict no-op.

**Monotonicity guarantee:** `eff_distance_threshold ≤ distance_threshold`,
`eff_feature_threshold ≥ feature_similarity_threshold`, veto only deletes — so Proposed can
**only remove edges** vs baseline. Never manufactures a merge. Makes "reduces incorrect
merges" a one-directional, mechanistically clean Hypothesis-2 claim.

## 3. Default parameters

| Param | Default (Proposed ON) | Justification |
|---|---|---|
| `use_uncertainty` | **`False`** (fn + CLI default) | **THE ablation knob.** Off ⇒ bitwise baseline (§4). |
| `uncertainty_weight` | `0.5` | At `u=1` distance budget halves (0.15→0.075 m). Primary dial. |
| `feature_uncertainty_weight` | `1.0` | At `u=1` cosine bar 0.75→0.9375; certain pairs keep 0.75. |
| `uncertainty_agg` | `"max"` | Merge bounded by least-certain participant; `"mean"` for ablation. |
| `min_shrink` | `0.1` | Distance budget never collapses below 0.015 m. |
| `max_feature_threshold` | `0.99` | A real cross-view match can still pass. |
| `bridge_tau` | `0.6` | Above 0.6 ⇒ conf < ~0.4 (ill-localized); two such may not seed a merge. `≥1.0` disables. |

`uncertainty_weight` is swept `{0, 0.25, 0.5, 0.75, 1.0}` for the dose–response plot
(weight 0 must equal `graph-fusion`). All other knobs pinned to today's values
(`distance_threshold=0.15`, `feature_similarity_threshold=0.75`,
`allow_same_view_edges=False`, `max_points_per_fused_node=8192`, fuse subsample seed 7,
output-uncertainty `mean·1/min(#views,3)`).

## 4. Reproduction anchor

Set **`use_uncertainty=False`** (function default everywhere) ⇒ the whole modulation block
is skipped, `eff_*` equal the base thresholds, the veto is skipped, and `:88`/`:92` execute
bitwise as today; edge attributes, `connected_components`, `sorted(component)`,
`object_{index:03d}` id minting (`:183–187`), and `fuse_node_cluster` outputs are untouched.
Equivalent no-op: `use_uncertainty=True` with `uncertainty_weight=0`,
`feature_uncertainty_weight=0`, `bridge_tau≥1.0`. The cosine dim-guard is inert in the off
state (feature gate only calls cosine when both features present; same-backend pairs share
dims).

**Mandatory regression test before any Proposed run:**
- Files: `results/benchmark_tum_rgbd_paper_subset/<scene>/views_{03,05,08,10}/scene_graph.json`.
- Capture pre-change copies, apply edits, re-run the **graph** stage with the *baseline*
  command (no `--variant`/`--use-uncertainty`), assert empty diff:
  ```
  python scripts/run_benchmark.py --dataset <manifest> --skip-existing \
    --stages graph --output-root results/benchmark_tum_rgbd_paper_subset
  # then per views_NN:  diff <pre>/scene_graph.json results/.../views_NN/scene_graph.json   # empty
  ```
- Only intentional new keys: `pipeline.variant` / `pipeline.use_uncertainty`. For legacy
  artifacts, diff with `jq 'del(.pipeline.variant,.pipeline.use_uncertainty)'` on both
  sides. Merge topology, node set, labels, and metrics must be byte-identical — that is the
  contract.

## 5. Shared fusion entry point

All five variants route through the single existing `fuse_object_nodes`
(`graph_builder.py:169–188`), dispatched by one new `variant: str`. `run_pipeline.py:93`
calls this one function.

```python
def fuse_object_nodes(
    nodes, *,
    variant: str = "graph-fusion",        # dispatch contract
    distance_threshold: float = 0.15,
    feature_similarity_threshold: float | None = None,
    max_points_per_fused_node: int = 8192,
    # uncertainty knobs (consulted only when variant == "proposed"):
    use_uncertainty: bool = False,
    uncertainty_weight: float = 0.0,
    feature_uncertainty_weight: float = 0.0,
    uncertainty_agg: str = "max",
    min_shrink: float = 0.1,
    max_feature_threshold: float = 0.99,
    bridge_tau: float = 1.0,
    fixed_shrink: float = 1.0,            # fixed-shrink control
) -> list[ObjectNode]:
```

The connected-components + `fuse_node_cluster` tail (`:181–188`) is **identical for all
variants** (preserves node-id semantics + cluster aggregation). The variant only changes the
single `build_geometry_fusion_graph(...)` gate call:

| `variant` | Gate change | Notes |
|---|---|---|
| `2d-only` | `distance_threshold=inf` (geometry off), feature gate active, `allow_same_view_edges=True` | appearance-only |
| `geometry-only` | `feature_similarity_threshold=None` (feature off), distance 0.15 | pure-geometry baseline |
| `semantic-lifting` | no edges — every candidate is its own singleton component | skip `build_geometry_fusion_graph` |
| `graph-fusion` (**default**) | today's gate: distance 0.15 **and** feature 0.75, no uncertainty | bitwise == current pipeline (§4) |
| `proposed` | `graph-fusion` gate **+** §2 modulation + bridge veto, `use_uncertainty=True` | edge-removing only |
| (`fixed-shrink` control) | `graph-fusion` gate with uniform `distance_threshold*fixed_shrink`, no uncertainty | skeptic control |

`build_geometry_fusion_graph` (`:68–73`) gains no-op-default uncertainty params; its body
gains the `if use_uncertainty:` modulation block between `:85` and `:87`, plus the bridge
veto before `graph.add_edge` at `:94`.

## 6. Code changes

**A. `src/vggt_scene_graph/graph_builder.py`**
1. `cosine_similarity` (`:11–20`): add dim guard `if left.shape != right.shape: return 0.0`
   after the `None` check.
2. `build_geometry_fusion_graph` (`:68–102`): extend signature with no-op-default
   uncertainty params (`use_uncertainty=False, uncertainty_weight=0.0,
   feature_uncertainty_weight=0.0, uncertainty_agg="max", min_shrink=0.1,
   max_feature_threshold=0.99, bridge_tau=1.0, fixed_shrink=1.0`). After the same-view skip
   (`:85`), before `distance = centroid_distance(...)` (`:87`), insert:
   ```python
   eff_distance_threshold = distance_threshold * fixed_shrink   # 1.0 default => unchanged
   eff_feature_threshold = feature_similarity_threshold
   veto = False
   if use_uncertainty:
       u_l = float(getattr(left, "uncertainty", 0.0) or 0.0)
       u_r = float(getattr(right, "uncertainty", 0.0) or 0.0)
       u_pair = max(u_l, u_r) if uncertainty_agg == "max" else 0.5 * (u_l + u_r)
       u_pair = min(max(u_pair, 0.0), 1.0)
       shrink = max(1.0 - uncertainty_weight * u_pair, min_shrink)
       eff_distance_threshold = distance_threshold * shrink
       if feature_similarity_threshold is not None:
           gap = 1.0 - feature_similarity_threshold
           eff_feature_threshold = min(
               feature_similarity_threshold + feature_uncertainty_weight * u_pair * gap,
               max_feature_threshold,
           )
       veto = (u_l > bridge_tau) and (u_r > bridge_tau)
   ```
   Change `:88` to `if distance <= eff_distance_threshold and not veto:`, `:92` to
   `if feature_similarity < eff_feature_threshold:`, leave `:97` `weight=` on base
   `distance_threshold`.
3. `fuse_object_nodes` (`:169–188`): add the `variant` dispatch that sets gate kwargs per
   the §5 table, then one shared `build_geometry_fusion_graph` call (except
   `semantic-lifting`, which builds a no-edge graph) and the unchanged components/cluster
   tail.

**B. `scripts/run_pipeline.py`** — add CLI flags `--variant`
(`choices=[2d-only,geometry-only,semantic-lifting,graph-fusion,proposed,fixed-shrink]`,
default `graph-fusion`), `--use-uncertainty` (store_true), `--uncertainty-weight 0.5`,
`--feature-uncertainty-weight 1.0`, `--uncertainty-agg {max,mean}`,
`--uncertainty-min-shrink 0.1`, `--uncertainty-max-feature-threshold 0.99`, `--bridge-tau
0.6`, `--fixed-shrink 1.0`. Forward into the `fuse_object_nodes(...)` call (`:93`). Stamp
`variant`/`use_uncertainty`/weights into `payload["pipeline"]` (`:107`) so CSVs
self-identify (metadata-only; does not affect the merge).

**C. `scripts/run_benchmark.py`** — add the same `--variant` + pass-through flags.
- **Per-variant output dirs:** `run_dir = args.output_root / args.variant / scene.scene_id
  / f"views_{NN}"`.
- **Shared upstream cache:** keep `geometry_path`/`sam_path`/`clip_path`/`dinov2_path` under
  a variant-independent location (e.g. `args.output_root / "_shared" / scene / views_NN`) so
  VGGT/SAM/CLIP/DINOv2 are computed **once** and reused by all variants; only
  graph/labeled/figure live per-variant.
- **Pass `--variant` to the graph stage** (`:215–235`); when `proposed`, conditionally
  append `--use-uncertainty` + weight/`--bridge-tau`; when `fixed-shrink`, append
  `--fixed-shrink`.
- **Drive each variant** with `--stages graph labels figure --skip-existing` after running
  the four costly upstream stages once with the default variant.

## 7. Evaluation & comparison

**Three measurement layers (all already in the harness):**
1. **Incorrect-merge proxy (primary Hyp-2 signal).** No direct merge/split metric exists →
   use `object_label_recall` (over-merge ⇒ recall falls) + `object_label_precision`
   (over-split ⇒ precision falls), always reported with `object_label_f1`. From
   `multiset_precision_recall_f1` (`metrics.py:27–43`).
2. **Structural counts (annotation-free).** `num_nodes`, `num_candidate_nodes`,
   `multi_view_nodes`, `multi_view_ratio`, `mean_uncertainty`, and mean fused-node
   `metadata.num_source_nodes`. Proposed should show **higher `num_nodes`** and **lower mean
   `num_source_nodes`** than `graph-fusion`, with the gap **growing as view_count drops** —
   the Hyp-2 signature.
3. **Relation triplets.** `relation_triplet_{precision,recall,f1}` (`metrics.py:50–63`).

**Pseudo-reference-vs-10-view.** Evaluate every variant×view-count against the frozen 10-view
checked annotation; report effect *trends across view_count* and *deltas between variants*,
never absolute numbers as ground truth (GT is pipeline-biased + view-frozen).

**Variant × view-count table** (one block per metric — object recall/precision/f1, relation
f1, num_nodes, mean num_source_nodes):

| variant | views=3 | views=5 | views=8 | views=10 |
|---|---|---|---|---|
| 2d-only | … | … | … | … |
| geometry-only | … | … | … | … |
| semantic-lifting | … | … | … | … |
| graph-fusion (baseline) | … | … | … | … |
| **proposed** | … | … | … | … |
| *fixed-shrink (control)* | … | … | … | … |

Plus the **dose–response plot** (`object_label_f1` vs `uncertainty_weight ∈
{0,0.25,0.5,0.75,1.0}` per view_count; weight 0 == graph-fusion) and **single-knob ablation
rows**: (a) `uncertainty_weight` only, (b) `feature_uncertainty_weight` only, (c) bridge-veto
only.

**Cross-variant node-id caveat.** Removing edges renumbers `object_{index:03d}` ids and ids
never align across variants — but this is safe: every checked metric reduces to a label
multiset (objects) or label:relation:label multiset (relations), with node ids stripped in
`annotation_checked.json`. **Do not introduce any cross-variant metric keyed on `node_id`.**

## 8. Risks & mitigations

1. **"It's just a retuned global threshold, not uncertainty" (skeptic).** → the mandatory
   `fixed-shrink` control (uniform shrink, zero uncertainty info); if it matches the gain,
   the claim is withdrawn. Dose–response + single-knob rows attribute the gain to
   `uncertainty_weight` and to geometry vs appearance vs veto.
2. **Two coupled interventions confound Hyp-2 (rigor).** → promote single-knob arms to
   primary results; report the bridge veto as its own arm.
3. **`uncertainty` is a size confound (compactness saturates for large objects).** →
   (a) size-stratified breakdown of recall/precision by fused-node `bbox_3d.extent_xyz`;
   (b) `min_shrink=0.1` caps worst-case shrink, `bridge_tau=0.6` means one confident endpoint
   exempts the pair; (c) disclose the no-`world_points_conf` fallback regime and confirm
   scenes carry `mean_world_point_confidence` (they do, via VGGT). Always report precision +
   f1 alongside recall to expose over-split.

## 9. Paper impact

The **"Proposed" numbers will change**: today's Proposed differs from graph-fusion only in
the *output* `mean_uncertainty` (same topology); the new Proposed changes merge topology, so
`num_nodes`, `multi_view_ratio`, `object_label_{precision,recall,f1}`, and
`relation_triplet_*` shift, largest at 3/5 views. **Re-run:** graph + labels + figure for the
`proposed` and new `fixed-shrink` variants (upstream features cached), then
`evaluate_sparse_view_annotations.py`. **Regenerate:** main results table (now six variants),
dose–response figure, single-knob ablation table, size-stratified breakdown, and Proposed
`scene_graph.png` figures. The `graph-fusion`/`geometry-only`/`2d-only`/`semantic-lifting`
numbers are unaffected **provided the §4 regression diff passes** — run that diff first.
