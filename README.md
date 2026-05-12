# cable.sim

Omniverse Kit extension for procedural cable simulation, based on the Beta
deformable body schema (volume / hex-mesh).

## Status

Phase 1: headless core (no GUI). Builds a complete cable hierarchy from a
declarative `CableSpec`:

- procedural cylinder cooking mesh (length, radius, axial rings, radial segments)
- volume deformable with auto hex-mesh
- deformable physics material
- `Start` (kinematic) and `End` rigid-body anchors
- auto attachments (`attachmentStart`, `attachmentEnd`)

## Layout

```
source/extensions/cable.sim/
├── config/extension.toml
└── cable/sim/
    ├── core/         pure data: CableSpec, defaults
    ├── geometry/     cylinder mesh generator
    ├── physics/      deformable, material, rigid, attachment, usd helpers
    ├── builder/      orchestrator (spec → USD prim hierarchy)
    └── commands/     omni.kit.commands (Undo/Redo)
```

`cable.sim` exposes a clean public Python API:

```python
from cable.sim import CableSpec, build_cable
import omni.usd

spec = CableSpec(path="/World/Cable", length=1.5, radius=0.005)
build_cable(omni.usd.get_context().get_stage(), spec)
```

The same is also reachable as a Kit command:

```python
import omni.kit.commands
omni.kit.commands.execute("CreateCable", spec=spec)  # Undo/Redo enabled
```

## Setup

Once after cloning, bootstrap the NVIDIA `repo`/`packman` tooling. We do
**not** vendor those files; instead copy them from a reference Kit-template
repo:

```powershell
.\scripts\bootstrap_tools.ps1 -Reference "A:\isaac-sim-exts\cable-extension"
```

Then build:

```powershell
.\repo.bat build
```

## Use in Kit

Add the built `_build/<platform>/<config>/exts/` directory (or
`source/extensions/`) to Kit's extension search paths and enable `cable.sim`.

## Roadmap

- live wireframe preview while editing
- GUI (Cable Creator window)
- custom USD as cooking mesh source
- multi-cable management / list view
- non-straight cable spines (control points + spline)
