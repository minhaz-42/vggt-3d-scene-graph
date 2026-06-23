# Novelty And Gap

## What VGGT Already Did

**VGGT: Visual Geometry Grounded Transformer**, CVPR 2025, introduced a large feed-forward transformer that directly predicts key 3D geometry attributes from one, a few, or many images.

Its outputs include:

- camera intrinsics,
- camera extrinsics,
- depth maps,
- point maps,
- 3D point tracks.

Its main novelty is fast unified 3D geometry prediction without relying on slow classical post-processing as the main pipeline.

What VGGT does not focus on:

- open-vocabulary object labels,
- object-level 3D segmentation,
- scene graph relations,
- text-queryable object understanding,
- sparse-view semantic uncertainty.

## What CUA-O3D Already Did

**Cross-Modal and Uncertainty-Aware Agglomeration for Open-Vocabulary 3D Scene Understanding**, CVPR 2025, integrates multiple 2D foundation models into a 3D scene understanding model.

Its main novelty:

- fuses heterogeneous 2D foundation-model features,
- uses deterministic uncertainty estimation,
- improves open-vocabulary 3D segmentation.

What CUA-O3D does not fully solve:

- feed-forward VGGT-based sparse-view geometry,
- explicit 3D scene graph construction,
- relation prediction between object instances,
- casual few-image capture scenarios.

## What OpenSplat3D Already Did

**OpenSplat3D**, CVPRW 2025, extends 3D Gaussian Splatting toward open-vocabulary 3D instance segmentation.

Its main novelty:

- uses Gaussian Splatting for open-vocabulary 3D instance segmentation,
- avoids manual labeling for target categories,
- enables text-queryable 3D object masks.

What OpenSplat3D does not fully solve:

- structured object relation reasoning,
- uncertainty-aware sparse-view graph fusion,
- scene graph output as the main task.

## Your New Gap

The clear gap is:

**Current methods reconstruct or segment 3D scenes, but they do not reliably build language-grounded 3D scene graphs from sparse casual RGB views.**

## Your Novelty

Your project should contribute:

1. **VGGT-Guided Object Lifting**  
   Lift 2D masks and features into 3D using VGGT geometry instead of requiring dense RGB-D or many posed views.

2. **Uncertainty-Aware Cross-View Object Graph**  
   Merge candidate objects across views using feature similarity, geometry overlap, view coverage, and depth/mask reliability.

3. **Relation-Aware 3D Scene Graph**  
   Predict spatial relations between objects, not only object labels and masks.

4. **Sparse-View Evaluation Protocol**  
   Evaluate under 3, 5, 8, and 10 input views to show practical behavior under limited capture.

## One-Sentence Novelty

**We turn feed-forward 3D geometry and open-vocabulary 2D semantics into a sparse-view, uncertainty-aware 3D scene graph.**

## What Not To Claim

Avoid claiming:

- that you invented uncertainty-aware 3D distillation,
- that you invented feed-forward 3D reconstruction,
- that you invented open-vocabulary 3D segmentation,
- that you trained a new foundation model.

Claim instead:

- a new integration and graph reasoning framework,
- sparse-view robustness,
- scene graph output,
- practical language-grounded 3D understanding.
