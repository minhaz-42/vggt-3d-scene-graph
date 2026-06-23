# Paper Outline

## Title

**Uncertainty-Guided Language-Grounded 3D Scene Graphs from Sparse Views**

## Abstract

Cover:

- sparse casual RGB views,
- feed-forward geometry from VGGT,
- 2D foundation-model semantics,
- uncertainty-aware graph fusion,
- 3D object and relation outputs,
- results on sparse-view benchmarks.

## 1. Introduction

Key story:

- 3D scene understanding is moving from reconstruction to spatial intelligence.
- VGGT makes geometry fast and feed-forward.
- Open-vocabulary 3D methods make object queries possible.
- However, practical sparse-view scene graph understanding is still unsolved.
- Propose a graph reasoning framework that fuses geometry, semantics, and uncertainty.

Contribution bullets:

- We propose a sparse-view 3D scene graph framework using frozen 3D and vision-language foundation models.
- We introduce uncertainty-aware graph fusion for cross-view object proposal merging.
- We infer spatial relations between language-grounded 3D object instances.
- We evaluate sparse-view robustness under 3, 5, 8, and 10 input views.

## 2. Related Work

Subsections:

### 2.1 Feed-Forward 3D Geometry

Discuss VGGT, DUSt3R, MASt3R, and SfM/MVS context.

### 2.2 Open-Vocabulary 3D Scene Understanding

Discuss CUA-O3D, OpenScene, ConceptFusion, OpenMask3D, OpenSplat3D.

### 2.3 Gaussian Splatting For 3D Semantics

Discuss 3DGS, OpenSplat3D, and language-driven 3DGS methods.

### 2.4 3D Scene Graphs And Relational Reasoning

Discuss scene graphs, 3D relation prediction, and embodied AI relevance.

## 3. Method

Subsections:

### 3.1 Problem Definition

Input:

- sparse RGB images.

Output:

- 3D object graph with labels and relations.

### 3.2 Sparse-View Geometry Backbone

Describe VGGT outputs and how they are used.

### 3.3 Open-Vocabulary 2D Proposals

Describe masks and feature extraction.

### 3.4 2D-to-3D Object Lifting

Explain projection and point aggregation.

### 3.5 Uncertainty-Aware Graph Fusion

Define nodes, edges, uncertainty scores, and merge objective.

### 3.6 Relation Prediction

Define spatial relation rules or learnable relation head.

## 4. Experiments

Subsections:

### 4.1 Datasets

ScanNet++, ARKitScenes, or a smaller accessible subset.

### 4.2 Baselines

2D-only matching, geometry-only clustering, semantic lifting, OpenSplat3D/CUA-O3D if feasible.

### 4.3 Metrics

Object segmentation, instance matching, scene graph triplet metrics, sparse-view robustness.

### 4.4 Implementation Details

Mention frozen backbones, trainable graph module, and hardware.

## 5. Results

Tables:

- main sparse-view results,
- ablation of geometry,
- ablation of uncertainty,
- relation prediction results,
- runtime and parameter count.

Figures:

- framework diagram,
- 3D graph visualization,
- sparse-view performance curve,
- qualitative scene graph examples,
- failure cases.

## 6. Discussion

Discuss:

- why geometry helps object consistency,
- when uncertainty prevents bad merges,
- limits of 2D foundation-model labels,
- limitations without real scene graph ground truth,
- future work toward robotics and AR.

## 7. Conclusion

End with:

- proposed sparse-view 3D scene graph framework,
- main experimental gain,
- broader value for spatial intelligence.
