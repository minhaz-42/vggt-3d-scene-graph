# Experiment Plan

## Research Question

Can feed-forward geometry from VGGT and uncertainty-aware graph reasoning improve open-vocabulary 3D object and relation understanding from sparse RGB views?

## Hypotheses

1. VGGT geometry improves cross-view object proposal fusion compared with purely 2D feature matching.
2. Uncertainty-aware graph fusion reduces incorrect object merges under sparse views.
3. Adding relation reasoning improves structured scene understanding beyond segmentation-only baselines.
4. Performance degrades more gracefully from 10 views to 3 views than methods that do not use geometry-aware graph fusion.

## Stages

### Stage 0: Toy Scene Prototype

Use 3-5 images from one indoor scene.

Output:

- reconstructed point map,
- lifted object proposals,
- object graph JSON,
- simple spatial relations.

Success criterion:

- pipeline runs end to end on one scene.

### Stage 1: Small Dataset Evaluation

Use the completed five-sequence TUM RGB-D paper subset:
`configs/datasets/tum_rgbd_paper_subset.json`.

Output:

- completed 3/5/8/10 sparse-view scene graphs,
- object proposal, fusion, relation, and uncertainty statistics,
- relation graph quality using checked annotations or pseudo-labels.

Success criterion:

- compare 3, 5, 8, and 10 image settings across all five scenes.

Current status:

- completed 20 paper-subset runs,
- exported aggregate and per-scene paper tables,
- next step is checked annotation for final object/relation F1.

### Stage 2: Baselines

Compare against:

- 2D-only SAM + CLIP matching,
- geometry-only VGGT clustering,
- OpenSplat3D if feasible,
- CUA-O3D if feasible,
- proposed VGGT + uncertainty graph fusion.

### Stage 3: Full Paper Experiments

Run:

- sparse-view ablation,
- uncertainty ablation,
- graph edge ablation,
- relation-prediction evaluation,
- cross-scene generalization.

## Proposed Method Variants

| Variant | VGGT Geometry | 2D Semantics | Uncertainty | Graph Fusion | Relations |
| --- | --- | --- | --- | --- | --- |
| 2D-only | No | Yes | No | No | No |
| Geometry clustering | Yes | No | No | Yes | No |
| Semantic lifting | Yes | Yes | No | No | No |
| Graph fusion | Yes | Yes | No | Yes | No |
| Proposed | Yes | Yes | Yes | Yes | Yes |

## Metrics

### Object Understanding

- open-vocabulary semantic accuracy,
- 3D IoU if ground truth masks are available,
- instance matching F1,
- object merge/split error.

### Scene Graph Understanding

- relation precision,
- relation recall,
- relation F1,
- triplet accuracy: subject-relation-object.

### Sparse-View Robustness

- performance at 3, 5, 8, and 10 views,
- robustness to viewpoint selection,
- object coverage versus accuracy.

### Efficiency

- feature extraction time,
- graph inference time,
- memory use,
- number of trainable parameters.

## Uncertainty Signals

Use simple signals first:

- mask stability across augmentations,
- CLIP/DINO feature agreement,
- VGGT depth confidence if available,
- point-track consistency,
- number of views supporting an object,
- geometric compactness of lifted points.

## Graph Design

Nodes:

- candidate object instances from lifted 2D masks.

Node features:

- CLIP embedding,
- DINO embedding,
- 3D centroid,
- 3D bounding box,
- view coverage,
- uncertainty vector.

Edges:

- visual similarity,
- 3D overlap,
- spatial proximity,
- point-track consistency,
- co-occurrence across views.

Outputs:

- merged object identity,
- open-vocabulary label,
- spatial relations.

## Timeline

### Week 1

- Set up environment.
- Run VGGT demo on 3-5 local images.
- Save camera, depth, and point outputs.

### Week 2

- Run SAM/SAM2 masks.
- Extract CLIP/DINO features per mask.
- Create lifted 3D object candidates.

### Week 3

- Implement graph construction.
- Implement relation heuristics.
- Produce scene graph JSON.

### Week 4

- Add uncertainty scoring.
- Add graph merge algorithm.
- Compare against 2D-only matching.

### Week 5-6

- Use the completed five-sequence TUM RGB-D paper subset.
- Evaluate 3, 5, 8, and 10 view settings with checked annotations.

### Week 7-8

- Add learnable GNN module if needed.
- Run ablations.
- Prepare figures and first manuscript draft.

## Minimum Publishable Prototype

The minimum strong prototype is:

- one multi-scene dataset subset,
- 3/5/8/10 sparse-view protocol,
- completed structural/proxy metrics,
- at least three baselines,
- object-level outputs,
- scene graph relation outputs,
- ablation showing VGGT geometry and uncertainty both help.

## High-Risk Parts

Risk: full Gaussian Splatting is heavy.  
Fallback: use VGGT point maps as the 3D representation.

Risk: no scene graph labels.  
Fallback: evaluate object segmentation strongly and use rule-based spatial relation evaluation with manually checked subset.

Risk: foundation model inference is slow on Mac.  
Fallback: precompute features on a small subset and train only the graph module.
