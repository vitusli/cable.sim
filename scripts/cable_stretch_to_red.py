r"""Runtime anchor-distance stretch monitor for cable_stretch.usd.

Use in Isaac Sim's Script Editor after opening:
    A:/OneDrive - Wandelbots GmbH/nvidia_omniverse/projects/DAVitus/playground/projekte_sidequests/cable/cable_stretch.usd

Execute in Omniverse / Isaac Sim Script Editor with:
    exec(compile(open(r"C:\Users\Vitus\dev\cable.sim\scripts\cable_stretch_to_red.py", encoding="utf-8").read(), r"C:\Users\Vitus\dev\cable.sim\scripts\cable_stretch_to_red.py", "exec"))

Run this script, then press Play. The monitor sets the visual material
/World/Looks/Cable_vis to red while the distance between the cable anchors is
too large relative to the distance measured when the monitor starts. It restores
the normal color when the stretch drops below the threshold again.
"""

from __future__ import annotations

import builtins
import math
import traceback

import carb
import omni.kit.app
import omni.timeline
import omni.usd
from pxr import Gf, Sdf, Usd, UsdGeom


START_PATH = "/World/cable/Start"
END_PATH = "/World/cable/End"
SHADER_PATH = "/World/Looks/Cable_vis/Shader"
COLOR_ATTR = "inputs:diffuseColor"

# 1.10 means 10% more anchor distance than the baseline measured on start.
CRITICAL_STRETCH = 1.10
NORMAL_COLOR = Gf.Vec3f(0.33231598, 0.40200517, 0.45551604)
RED = Gf.Vec3f(1.0, 0.0, 0.0)

# Ignore a few app updates after Play so transforms settle before latching.
WARMUP_UPDATES = 5
LOG_EVERY_N_UPDATES = 30


class CableStretchMonitor:
    def __init__(self):
        self.stage = None
        self.update_sub = None
        self.timeline_sub = None
        self.running = False
        self.triggered = False
        self.update_count = 0
        self.baseline_distance = None
        self.last_distance = None
        self.last_relative_stretch = 1.0
        self.failed = False

    def start(self):
        self.stop()
        self.stage = omni.usd.get_context().get_stage()
        if self.stage is None:
            raise RuntimeError("No open USD stage")

        self._require_prim(START_PATH)
        self._require_prim(END_PATH)
        self._require_prim(SHADER_PATH)
        self._set_shader_color(NORMAL_COLOR)

        app = omni.kit.app.get_app()
        self.update_sub = app.get_update_event_stream().create_subscription_to_pop(
            self._on_update,
            name="cable_stretch_to_red_update",
        )

        timeline = omni.timeline.get_timeline_interface()
        self.timeline_sub = timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._on_timeline_event,
            name="cable_stretch_to_red_timeline",
        )

        self.running = True
        carb.log_info(
            "[cable stretch] Anchor-distance monitor registered. "
            "Press Play to measure baseline."
        )

    def stop(self):
        self.update_sub = None
        self.timeline_sub = None
        self.running = False

    def status(self):
        return {
            "running": self.running,
            "triggered": self.triggered,
            "failed": self.failed,
            "updates": self.update_count,
            "baseline_distance": self.baseline_distance,
            "distance": self.last_distance,
            "relative_stretch": self.last_relative_stretch,
            "threshold": CRITICAL_STRETCH,
            "start_path": START_PATH,
            "end_path": END_PATH,
            "shader_path": SHADER_PATH,
        }

    def _on_timeline_event(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self._reset_run_state()

    def _reset_run_state(self):
        self.triggered = False
        self.update_count = 0
        self.baseline_distance = None
        self.last_distance = None
        self.last_relative_stretch = 1.0
        self.failed = False
        self._set_shader_color(NORMAL_COLOR)

    def _on_update(self, _event):
        if self.failed:
            return

        timeline = omni.timeline.get_timeline_interface()
        if not timeline.is_playing():
            return

        try:
            self.update_count += 1
            distance = self._anchor_distance()
            self.last_distance = distance

            if self.update_count <= WARMUP_UPDATES:
                return

            if self.baseline_distance is None:
                self.baseline_distance = distance
                carb.log_info(
                    f"[cable stretch] Baseline anchor distance: {distance:.6f}"
                )
                return

            if self.baseline_distance <= 1.0e-9:
                raise RuntimeError("Baseline anchor distance is zero")

            relative = distance / self.baseline_distance
            self.last_relative_stretch = relative
            self._log_status(distance, relative)

            if relative >= CRITICAL_STRETCH:
                if not self.triggered:
                    carb.log_warn(
                        f"[cable stretch] Critical anchor stretch reached: "
                        f"{relative:.4f} >= {CRITICAL_STRETCH:.4f} "
                        f"(distance={distance:.6f}, baseline={self.baseline_distance:.6f}). "
                        "Cable visual material set to red."
                    )
                self._set_shader_color(RED)
                self.triggered = True
            else:
                if self.triggered:
                    carb.log_info(
                        f"[cable stretch] Anchor stretch recovered: "
                        f"{relative:.4f} < {CRITICAL_STRETCH:.4f}. "
                        "Cable visual material restored."
                    )
                self._set_shader_color(NORMAL_COLOR)
                self.triggered = False
        except Exception:
            self.failed = True
            carb.log_error("[cable stretch] Monitor failed:\n" + traceback.format_exc())

    def _anchor_distance(self):
        start = self._world_translation(START_PATH)
        end = self._world_translation(END_PATH)
        dx = float(start[0] - end[0])
        dy = float(start[1] - end[1])
        dz = float(start[2] - end[2])
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def _world_translation(self, prim_path):
        prim = self._require_prim(prim_path)
        matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(
            Usd.TimeCode.Default()
        )
        return matrix.ExtractTranslation()

    def _get_shader_attr(self):
        prim = self._require_prim(SHADER_PATH)
        attr = prim.GetAttribute(COLOR_ATTR)
        if not attr.IsValid():
            attr = prim.CreateAttribute(COLOR_ATTR, Sdf.ValueTypeNames.Color3f)
        return attr

    def _set_shader_color(self, color):
        self._get_shader_attr().Set(color)

    def _require_prim(self, prim_path):
        prim = self.stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            raise RuntimeError(f"Missing prim: {prim_path}")
        return prim

    def _log_status(self, distance, relative):
        if LOG_EVERY_N_UPDATES <= 0:
            return
        if self.update_count % LOG_EVERY_N_UPDATES != 0:
            return
        carb.log_info(
            f"[cable stretch] distance={distance:.6f}, "
            f"baseline={self.baseline_distance:.6f}, "
            f"relative={relative:.4f}, threshold={CRITICAL_STRETCH:.4f}"
        )


def start_cable_stretch_monitor():
    old_monitor = getattr(builtins, "_cable_stretch_monitor", None)
    if old_monitor is not None:
        try:
            old_monitor.stop()
        except Exception:
            carb.log_warn("[cable stretch] Failed to stop previous monitor")

    monitor = CableStretchMonitor()
    monitor.start()
    builtins._cable_stretch_monitor = monitor
    return monitor


def stop_cable_stretch_monitor():
    monitor = getattr(builtins, "_cable_stretch_monitor", None)
    if monitor is not None:
        monitor.stop()
        builtins._cable_stretch_monitor = None
        carb.log_info("[cable stretch] Monitor stopped")


def get_cable_stretch_status():
    monitor = getattr(builtins, "_cable_stretch_monitor", None)
    if monitor is None:
        return {"running": False}
    return monitor.status()


start_cable_stretch_monitor()
