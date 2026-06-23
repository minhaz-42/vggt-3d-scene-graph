"""Backbone adapters used by the scene graph pipeline."""

from .vggt_adapter import VGGTRunner, select_torch_device

__all__ = ["VGGTRunner", "select_torch_device"]
