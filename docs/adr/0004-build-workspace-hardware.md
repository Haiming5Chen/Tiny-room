# Dedicated build workspace and robot hardware

Reuse the existing MuJoCo renderer, immutable editor and Blueprint composition.
Add a focused build workspace within the workshop window: a persistent parts
browser, isolated assembly viewport, hardware preview and mounting controls. It
opens/closes without replacing or losing the current design; normal room simulation
remains available. No second solver loop or cross-window OpenGL ownership is needed.

Expand the catalog using original engineering-style procedural geometry: structural
extrusions, open frames, motor/gearbox housings, output shafts, servo horns, bearings,
flanged hubs, treaded wheels and swivel casters. Use compounds of supported primitive
bodies for visible detail and real contact geometry. Openings use separated walls
or ring segments instead of a solid block painted to look hollow. Preserve named
mounting frames and internal joints when instancing modules. Internal motors model
ideal torque only; no commercial product specifications, encoder/electrical behavior
or calibrated vendor CAD are claimed. More detailed geometry still needs physical
calibration, not merely a more realistic silhouette.

Tests cover every catalog item's roundtrip/insertion/compile, active internal joints,
new material preservation, oriented module placement, scoped build input and
save/simulate/return. Visually inspect the workspace and representative hardware.
