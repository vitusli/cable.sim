"""Public API for the cable.sim extension.

Procedurally creates volume (hex-mesh) deformable cables in an Omniverse stage.
"""

from .core.spec import CableSpec
from .core.defaults import CABLE_DEFAULTS
from .builder.cable_builder import build_cable

__all__ = [
    "CableSpec",
    "CABLE_DEFAULTS",
    "build_cable",
]
