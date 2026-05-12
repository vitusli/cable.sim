"""Extension lifecycle — registers omni.kit commands."""

from __future__ import annotations

import carb
import omni.ext
import omni.kit.commands

from .commands.create_cable import CreateCableCommand


class CableSimExtension(omni.ext.IExt):
    """cable.sim — procedural deformable cables."""

    def on_startup(self, ext_id: str) -> None:
        carb.log_info(f"[cable.sim] startup ({ext_id})")
        omni.kit.commands.register(CreateCableCommand)

    def on_shutdown(self) -> None:
        carb.log_info("[cable.sim] shutdown")
        try:
            omni.kit.commands.unregister(CreateCableCommand)
        except Exception:
            pass
