# ADR 0001: immutable Blueprint, backend-owned mechanics

Accepted. A frozen, versioned data model is the construction interchange format.
Entities instantiate it with IDs and poses. MuJoCo is an optional adapter compiled
with MjSpec. Recompilation occurs at BUILD → SIMULATE, not on every step.

This avoids a second representation for a future editor and prevents runtime state
from overwriting saved designs. Cost: whole-world recompile on edits for now; no
live topology editing, backend migration, or general closed-loop assembly support.
Alternative rejected: use MJCF/native model as the public world model, which would
couple future state, tasks and builder operations to a single solver.
