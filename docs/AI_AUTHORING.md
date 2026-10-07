# Shared authoring: language, Python and direct manipulation

## Product contract

One authored world must be shared by all three interfaces. AI proposes structured
changes; Python produces the same data; direct scene and machine editing remain
first-class. Never regenerate the whole world merely to change one object. Stable
object IDs identify targets. Labels are for people; ambiguous references require
clarification. Units and coordinate frames are explicit.

A proposal communicates: requested goal, resolved objects, exact before/after
values, assumptions, validation performed, checks not performed, and changes that
cannot be supported. A proposed layout is not a verified working factory. The
user reviews a diff and accepts or dismisses it. Applying a proposal is one undo
step. Failed validation or stale scene revisions leave the current scene intact.
If the user drags an object while AI is thinking, the old proposal cannot overwrite
that edit: obtain a fresh snapshot and re-propose. Do not silently rebase it.

## Research and decisions (2026-10-02)

- OpenUSD supports assembling and composing scene description, including layered
  edits: https://openusd.org/release/intro.html . Adopt explicit authored changes
  and shared scene identity. Do not replace Blueprint or install USD for the
  current small cell editor; an interchange adapter can come later.
- NVIDIA Isaac Sim uses USD asset import/export and robot setup workflows:
  https://docs.isaacsim.omniverse.nvidia.com/latest/robot_setup/index.html . Adopt
  reusable registered assets with provenance and capabilities. Do not imply that
  attractive meshes validate actuator performance or manufacturing processes.
- MoveIt PlanningScene separately checks collisions, constraints and feasibility:
  https://moveit.picknik.ai/main/doc/examples/planning_scene/planning_scene_tutorial.html .
  Adopt explicit validation levels. Existing MuJoCo mechanics and Panda IK stay in
  place; MoveIt/ROS integration is a future adapter, not a dependency added here.

These are architectural adaptations; no upstream implementation is copied.

## Implemented first slice

The existing Panda factory cell accepts versioned JSON proposals for explicit tray
positions, source/destination and product. Python and a precision form generate
identical requests. The editor previews exact changes without changing the scene,
rejects unknown fields/IDs, validates the complete candidate layout atomically,
and rejects stale proposals using both an edit revision and base recipe content.
Existing dragging, task selection and product buttons remain the authoring tools.
All successful cell edits invalidate pending proposals, and applying one is a
single existing recipe undo step. A draft can be exported and submitted by code.

Layout checks cover the existing table, tray spacing, robot base and camera posts.
Robot reach, trajectories, collisions along motion, grasp success and throughput
are not established by accepting a layout. Use the existing path preview and
physical cycle to evaluate the cell further.

## Subsequent implementation order

1. Shared document data/API is implemented in `factory/document.py` and
   `factory/document_editor.py`: stable stations, shared custom Blueprints, process
   links as intent, reviewed transactions and undo/redo. See FACTORY_DOCUMENT.md.
   The same-window Factory layout workspace now uses this API for station selection,
   drag placement, exact poses, machine reuse, flow intent and save/load.
2. Add process connections and capability contracts; active conveyors and generic
   multi-station execution need implementations before AI may request them.
3. Provide a model-facing snapshot/capabilities/propose interface. Supply selection,
   scene revision, IDs, units and explicit unsupported operations. AI returns data,
   never arbitrary Python or native handles. Show questions/assumptions separately.
4. Add object/property locks, proposal revision, durable history and selective
   acceptance with dependency validation. Direct editing remains available.
5. Connect an explicitly configured AI provider. No provider, credential collection,
   external scene upload, sentence parser or chat endpoint is implemented here.

Example future conversation: “Move this station 20 cm away from the arm; keep the
conveyor fixed.” Resolve “this” from selection, ask which direction if unclear,
propose an exact world-coordinate pose, list preserved constraints, show a ghost,
and commit only the reviewed changes. Arbitrary car production, welding and
painting require supported process models; they must not appear as validated
physics merely because a language model can describe them.
