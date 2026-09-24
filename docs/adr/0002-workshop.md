# ADR 0002: expose the construction loop before importing more assets

Accepted after the first mechanical milestone and drive-controls correction.
The user reported that the result still did not resemble the intended experience.
The next slice brings forward a small interactive workshop rather than integrating
another predefined robot. This prioritizes Little World's unique construction loop.

Reuse MuJoCo physics, scene selection, camera controls and rendering, plus existing
GLFW window/input handling. Add only a side panel and AssemblyEditor operations over
the existing Blueprint format. No third-party GUI toolkit, engine, or asset pack.
A furnished room is built procedurally from the same box/material abstractions.

World.preview compiles while remaining in BUILD; no physics advances. Editing
rebuilds that preview. SIMULATE calls World.start; STOP calls World.reset. Blueprint
history is separate from simulation state. Invalid edits roll back to the previous
design. Saving persists Blueprint JSON with the same schema the Python API uses.

The first slice exposes selection, incremental translation, Z rotation, uniform
scaling, material changes, beams, powered wheel attachments, cameras, loose boxes,
subtree deletion, motor strength, undo/redo and saving/loading. Wheel attachment
operations produce ordinary Body, Hinge, Motor and ControllerSpec data. The UI
recognizes a two-channel differential_torque controller for keyboard driving.

Limitations are explicit: one editable assembly, preset attachment positions, no
arbitrary connection graph UI, no collision-validity editor, no room-asset editing,
no gizmos, no arbitrary controller wiring. Geometry changes do not automatically
move child mounts. These are next builder extensions, not implemented promises.
