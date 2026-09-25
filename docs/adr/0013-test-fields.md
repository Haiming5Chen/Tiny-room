# Test fields: scenarios with goals the simulator checks

**Problem.** Every test ran in one furnished room whose floor is 5 m by 4 m, whose
open sides end in a black void, and whose pickup stand sits 0.46 m in front of the
machine: every vehicle's first drive hit it. There was nothing to measure a design
against - no lane to time, no slope to climb, no step to clear, no load to push, no
place to put an object - so a test could only show that a machine moved, not how well
it did something, and two designs could not be compared on the same task.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo supplies the physics
of every field - contacts on inclines and steps, pushing, tipping - and its renderer a
skybox. Fields are therefore ordinary Blueprint entities (boxes and cylinders with
sourced surfaces, ADR 0010) composed into a Scene; nothing new is simulated. Robot
suites such as MuJoCo's own task sets define tasks in code around specific robots;
here a field must accept any machine built in the workshop, so fields are data and
goals are checked from the core `State` alone.

**Unique contribution.** Scenarios for arbitrary machines, judged by the physics:
- *Fields* (`little_world/fields/`): the workshop room, a sprint lane, a slalom of
  bollard gates, three ramps (8, 14 and 20 degrees, plywood), a curb run (10, 20 and
  35 mm steps), a crate to push (4 kg, wood on concrete), and a pick-and-place table.
  Each is authored in the machine's start frame - the machine stays at the origin
  facing +X, so the Build stage and the design are untouched - on a concrete slab with
  a low barrier and a sky backdrop.
- *Goals* (`fields/goals.py`, standard library): cross a line segment (in order, for
  gates), reach a zone (with a height, for a ramp top), deliver an object to a zone at
  rest, stay upright, leave obstacles undisturbed. They read only body poses and
  velocities from `State`, so they are independent of MuJoCo and of the UI.
- *Results*: live goal status in the Drive tab, lines and zones drawn on the floor,
  and the run report lists each goal with the time it was met; comparison with the
  previous run is made only within the same field.

**Blueprint and builder.** Fields change the scene, never the design. The chosen field
is a session setting; changing it recompiles the scene while building. `Scene` gains
an optional `backdrop` ('sky'), an appearance hint the MuJoCo adapter turns into a
gradient skybox and a directional sun (a field is larger than the room light's cone);
the workshop room keeps its look. The renderer's context is rebuilt when the set of
textures changes, since it only holds what it uploaded. The inventory's controlled
trials still run in the workshop room.

**Result.** Driving five machines straight at each field separates them for physical
reasons: small casters stop at a curb taller than themselves, a 20.5 kg robot on 1 Nm
motors cannot climb 8 degrees and climbs it at 9.1 kg, a rigid four-point chassis
unloads its drive wheels on a slope, and pushing a 4 kg crate needs more than its
15.7 N of friction (docs/VALIDATION.md has the table).

**Boundaries.** Goals judge geometry: a line is crossed when any body of the machine
is past it within the gate; a delivered object must be inside the zone and still. The
ramp and step heights, masses and surfaces are stated in each field; they are test
props, not standards. No timing gates beyond the simulator clock; no field randomises
positions; a program that names the workshop's objects fails its validation in a field
without them, as it should.
