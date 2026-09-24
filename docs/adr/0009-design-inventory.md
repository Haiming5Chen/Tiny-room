# Design inventory, comparisons and analysis

Reuse Blueprint, Program and the existing MuJoCo adapter. Persist named immutable
snapshots (design + program) under designs/inventory, with editable draft/finished
metadata. UUID filenames, atomic replacement, explicit schema validation. A checkout
first preserves a different current workspace as a recovery snapshot. No deletion
is needed for this first version. Finished is a user status, not a validation claim.

Analysis is deterministic and standard-library-only: primitive volume/density mass,
part differences, controller coverage, and gravity-only torque at the authored pose.
There is no generic numerical quality score or invented real-world payload rating.
Pros/cons reference actual properties and state their assumptions.

Performance comparisons run two isolated headless worlds under the same environment,
timestep, duration and protocol. Compare a standard drive/hold trial or the exact
current program. Invalid program references fail explicitly. A background worker
keeps the UI responsive; it never mutates the user's world or OpenGL context. Store
results with design/program/environment fingerprints and protocol metadata; reject
stale results when a compared design changes. Mechanical work is not battery energy.
Separate design estimates, simulated observations and physical measurements (none).
