"""omni.kit.commands wrapper for build_cable — provides Undo/Redo."""

from __future__ import annotations

import carb
import omni.kit.commands
import omni.usd

from ..core.spec import CableSpec
from ..builder.cable_builder import build_cable


class CreateCableCommand(omni.kit.commands.Command):
    """Create a volume-deformable cable.

    The command's ``do()`` schedules :func:`build_cable_async` and returns the
    anticipated root path immediately.  The async cook + attachment steps
    finish over subsequent Kit frames.

    Args:
        spec: A CableSpec instance (or dict of CableSpec fields).
    """

    def __init__(self, spec: CableSpec | dict | None = None, **kwargs):
        if spec is None:
            spec = CableSpec(**kwargs)
        elif isinstance(spec, dict):
            spec = CableSpec(**{**spec, **kwargs})
        self._spec: CableSpec = spec
        self._created_path: str = ""

    def do(self) -> str:
        self._created_path = build_cable(self._spec)
        return self._created_path

    def undo(self) -> None:
        if not self._created_path:
            return
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            return
        # Remove cable root and its anchors
        parent = "/".join(self._created_path.split("/")[:-1]) or "/"
        for prim_path in [self._created_path, f"{parent}/Start", f"{parent}/End"]:
            if stage.GetPrimAtPath(prim_path).IsValid():
                stage.RemovePrim(prim_path)
                carb.log_info(f"[cable.sim] Removed {prim_path}")
        self._created_path = ""
