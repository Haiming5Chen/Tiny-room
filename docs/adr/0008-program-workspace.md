# Program, guided assembly and test workspaces

Implementation order: (1) visual timed programs; (2) guided assembly;
(3) explicit Build/Program/Test navigation; (4) observation conditions;
(5) test feedback; (6) compatible procedural hardware families.

Reuse the existing MuJoCo world, torque controllers, and assembly editor. Programs
are immutable versioned data in a sibling .program.json, with no executable code.
A portable runner accepts elapsed simulation time and scalar observations, yielding
named joint targets / action keys / drive targets. The UI owns editing and view
state. The runner owns active index, repeat count and pause/step state. Design edits
remain independent. Validate references before execution; stale bindings fail.

Only simulation time advances blocks. Timeout fails explicitly. Pausing preserves
program progress and stops simulation; stopping removes program input while joint
controllers retain their targets. Return to BUILD resets physical state. Manual
inputs cannot compete with a running sequence; focus loss pauses it. Conditions
will consume detached observations, not native handles. Sensor signals are ideal
simulation observations, not vendor device emulation. Diagnostics are observations
and heuristics, never physical calibration or hidden changes to solver state.
