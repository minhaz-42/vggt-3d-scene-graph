# Literature Map

## Primary Anchor

### VGGT: Visual Geometry Grounded Transformer

Authors: Wang et al.  
Venue: CVPR 2025  
Paper: https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_VGGT_Visual_Geometry_Grounded_Transformer_CVPR_2025_paper.pdf  
Code: https://github.com/facebookresearch/vggt

Use in this project:

- geometry backbone,
- sparse-view camera/depth/point estimation,
- point tracks for cross-view consistency.

Limitation to extend:

- not designed for object-level language-grounded scene graphs.

## Open-Vocabulary 3D Understanding

### CUA-O3D

Full name: Cross-Modal and Uncertainty-Aware Agglomeration for Open-Vocabulary 3D Scene Understanding  
Venue: CVPR 2025  
Paper: https://openaccess.thecvf.com/content/CVPR2025/papers/Li_Cross-Modal_and_Uncertainty-Aware_Agglomeration_for_Open-Vocabulary_3D_Scene_Understanding_CVPR_2025_paper.pdf

Use in this project:

- motivates uncertainty-aware foundation-model fusion,
- key baseline for open-vocabulary 3D segmentation.

Limitation to extend:

- focuses on segmentation rather than explicit scene graphs and sparse casual views.

### OpenSplat3D

Full name: Open-Vocabulary 3D Instance Segmentation using Gaussian Splatting  
Venue: CVPR Workshop 2025  
Project: https://jenspiek.github.io/opensplat3d/  
Code: https://github.com/VisualComputingInstitute/opensplat3d

Use in this project:

- Gaussian Splatting-based open-vocabulary instance segmentation baseline.

Limitation to extend:

- relation reasoning and scene graph construction are not the main output.

## Closely Related 2025-2026 Directions

### Inst3D-LMM

Full name: Instance-Aware 3D Scene Understanding  
Venue: CVPR 2025  

Use in this project:

- supports the importance of instance-level 3D understanding and language reasoning.

### Articulate3D

Full name: Holistic Understanding of 3D Scenes as Universal Scene Description  
Venue: ICCV 2025  

Use in this project:

- supports the trend toward richer structured 3D scene descriptions.

### Ilov3Splat

Full name: Instance-Level Open-Vocabulary 3D Scene Understanding in Gaussian Splatting  
Year: 2026 preprint  

Use in this project:

- indicates that instance-level language-driven 3D Gaussian Splatting is still active in 2026.

## Datasets To Consider

### ScanNet++

Official site: https://scannetpp.mlsg.cit.tum.de/scannetpp/cvpr2025

Strength:

- high-fidelity indoor scenes,
- large-vocabulary semantic annotations,
- strong fit for open-vocabulary 3D scene understanding.

Challenge:

- dataset access and processing may be heavy.

### ARKitScenes

Official page: https://machinelearning.apple.com/research/arkitscenes  
GitHub data docs: https://github.com/apple/ARKitScenes/blob/main/DATA.md

Strength:

- mobile RGB-D indoor scenes,
- fits sparse casual capture motivation,
- especially relevant for Apple devices.

Challenge:

- annotations are more detection-oriented than full scene graph annotations.

### HM3D / Matterport3D

HM3D: https://aihabitat.org/datasets/hm3d/  
Matterport: https://matterport.com/partners/meta

Strength:

- large indoor scene dataset,
- strong for embodied AI and spatial reasoning.

Challenge:

- access/license constraints and heavier processing.

## Suggested Literature Positioning

Position the paper as:

1. building on VGGT for geometry,
2. building on CUA-O3D/OpenSplat3D for open-vocabulary semantics,
3. extending both toward sparse-view object graphs and relation reasoning.
