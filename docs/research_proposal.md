# Research Proposal

## Working Title

**Uncertainty-Guided Language-Grounded 3D Scene Graphs from Sparse Views**

## Target Level

This topic is designed for a Q1 journal path and a CVPR-style research standard. The realistic venue targets are:

- IEEE TPAMI
- IJCV
- IEEE TIP
- IEEE TMM
- Pattern Recognition
- Information Fusion
- IEEE TCSVT

The project can also be shaped into a conference submission if the method and experiments become strong enough.

## Problem

Given only a few casual RGB images of a scene, produce a language-grounded 3D scene graph:

- 3D object instances,
- open-vocabulary object labels,
- object confidence and uncertainty,
- spatial relations such as `on`, `under`, `near`, `inside`, `left of`, and `behind`.

This is harder than 3D reconstruction because the output must understand object identity and object relationships, not only geometry.

## Research Gap

Recent 2025 work makes major progress, but each line remains incomplete:

- **VGGT** predicts camera parameters, depth maps, point maps, and tracks in a feed-forward pass. It solves geometry, not language-grounded scene understanding.
- **CUA-O3D** fuses multiple 2D foundation-model features into 3D with deterministic uncertainty, but focuses on open-vocabulary 3D segmentation rather than sparse-view scene graphs.
- **OpenSplat3D** uses Gaussian Splatting for open-vocabulary 3D instance segmentation, but does not fully address structured relational reasoning from sparse casual views.

The missing piece is a framework that uses feed-forward geometry and open-vocabulary semantics to build a reliable 3D scene graph under sparse-view conditions.

## Proposed Method

The proposed framework has five stages:

1. **Sparse-view geometry extraction**  
   Use VGGT to estimate cameras, depth maps, point maps, and point tracks from 3-10 images.

2. **2D object proposal and semantic extraction**  
   Use SAM/SAM2 for masks and CLIP/DINOv2 for open-vocabulary features.

3. **3D object lifting**  
   Lift 2D masks into a shared 3D point representation using VGGT depth/camera outputs.

4. **Uncertainty-aware graph fusion**  
   Build a graph where nodes are candidate object instances and edges represent cross-view matches or spatial relations. Use uncertainty from mask consistency, feature agreement, view coverage, and depth reliability.

5. **Language-grounded scene graph output**  
   Produce object nodes and relation edges queryable by text prompts.

## Main Novelty

The novelty is not simply using VGGT or uncertainty. The novelty is:

**A sparse-view graph reasoning framework that transforms VGGT geometry and 2D foundation-model semantics into language-grounded 3D scene graphs.**

Specific contributions:

- A VGGT-guided 2D-to-3D object lifting pipeline for sparse casual views.
- A graph module that merges object proposals across views using geometry, semantics, and uncertainty.
- A language-grounded 3D scene graph representation with object and relation prediction.
- A sparse-view benchmark protocol evaluating 3, 5, 8, and 10 view settings.

## Why It Is Strong

This topic connects four high-impact areas:

- feed-forward 3D foundation models,
- open-vocabulary 3D scene understanding,
- Gaussian Splatting and 3D representations,
- graph-based relational reasoning.

It is stronger than simple classification because it asks for structured 3D understanding, which is closer to robotics, AR, embodied AI, and spatial intelligence.

## Expected Contribution Statement

We propose a lightweight, uncertainty-aware graph reasoning framework that fuses VGGT-derived geometry with open-vocabulary 2D foundation-model features to infer 3D object instances and spatial scene graphs from sparse RGB views.

## Scope Control

To keep this feasible on Apple Silicon:

- freeze VGGT, SAM/SAM2, CLIP, and DINOv2,
- precompute features,
- train only the graph fusion/relation module,
- start with point-map based 3D representation before full Gaussian Splatting.

If Gaussian Splatting becomes too heavy locally, use VGGT point maps as the main 3D representation and frame Gaussian Splatting as an optional extension.
