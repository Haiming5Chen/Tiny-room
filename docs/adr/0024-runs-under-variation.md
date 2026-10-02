# Runs under variation: a result with its spread

**Problem.** Every test field ran its scenario once, exactly as designed: the machine on its
mark, carrying nothing, on surfaces at the one friction value each source gives (OPEN
LW-008). The arm on a cart tips on the tilt table at 54.5 degrees - one number, with nothing
to say how much of it is the machine and how much that one run. A lab repeats a test, and
no repeat is the same: the machine is set down a little off its mark, it carries something,
the floor is not the surface a handbook measured. The radar filed LIBERO-plus, which asks
the same of learned manipulation policies under perturbed layouts, cameras and start
states.

**Does an existing simulator solve it? Can we wrap it?** Robot-learning frameworks randomize
friction, masses and reset poses to train policies (Isaac Lab's event terms, robosuite's
domain-randomization wrapper), and LIBERO-plus perturbs a benchmark to rank policies'
robustness. They vary to train or to rank; none takes a Little World Blueprint, reports a
test's spread against its own design's prediction, or says which change moved a result.
MuJoCo compiles what it is given and has no variation of its own. So the variations are
Blueprint edits and one run condition, and the runs are ordinary field runs.

**Unique contribution.**
- *Variations are data* (`fields/variation.py`, standard library). The machine set down off
  its mark and turned about it: an edit of its root transforms. A payload: a steel block of
  the payload's mass (4 cm at 0.5 kg) set down on the highest rigid part of the base under
  its site and fixed to it - a Blueprint body whose mass and inertia come from its size and
  density like any other. By default it goes over the centre of mass if nothing that moves
  reaches above that spot, else on the base's largest top as far back as it fits (for the
  arm on a cart: its deck behind the arm); anything that would reach into it is named and
  the run is reported as not run. Friction: every sourced surface pair moved across the
  range its own note cites (`materials/contact_pairs.SPREADS`, 13 pairs, each end the value
  used or a number the note quotes; a factor of two for the other 13, which the module's
  docstring already said published values span), applied by the backend for the run and
  never written into a design (`MujocoBackend.vary_pair_friction`).
- *A plan that reads.* The run as designed; each variation alone at both ends of its range,
  so its own effect can be read; then seeded random repeats with everything varied at once
  (20 runs by default). The ranges are stated: set down within 2 cm and 3 degrees of the
  mark, up to 0.5 kg aboard up to 5 cm either side of its site - assumptions, said as such -
  and friction across the sources' own ranges.
- *Protocols the machine can follow alone* (`inventory/sweep.py`): hold still (the tilt
  table), drive straight ahead at full speed as the W key does (sprint, ramps, curbs, push),
  or run the field's program template, solved once for the design on its mark and then run
  unchanged on every variation, as a program written in a lab runs however the machine was
  put down. Runs go to worker processes.
- *The spread, and what moved it.* The report gives each goal met in k of n runs with its
  fastest, median and slowest time and the runs that missed it; for a static test the range
  the machine went over in and the design's prediction for each variation; and each run's
  change from the run as designed. From the run report, "Repeat with variations" starts the
  same sweep in another Python process, shows its progress, then the headline, every run as
  a tick on a line beside the run as designed and the prediction, the changes that moved the
  result most, and copies the full report to the clipboard (`ui/varied_runs.py`). From a shell: `python -m little_world.inventory.sweep tilt --design
  mobile_manipulator`.

**Blueprint and builder.** Nothing saved changes. A varied design is ordinary Blueprint data
(moved roots, a `payload` body and material) and could be saved and inspected; friction is
a condition of the run. The app sends the current design to the sweep process as JSON and
reads the sweep back as JSON.

**Result.** Tilt table, the arm on a cart, 20 runs: it went over between 51.4 and 58.4
degrees (54.5 as designed). Set down 2 cm off its mark in any direction: no change, the
trip rail is set against its wheels. Friction at either end of the sources: -0.5 to +0.2.
Turned 3 degrees on the table: +0.4 and -3.1, where the rigid prediction said +1.7 and -1.6
- its worst case, 2.8 degrees high. Traced since (OPEN LW-017): the machine does not keep the
heading it was set down at. Leaning on its right tread wheel against the rail and on its
front caster, it turns as the table rises - set down straight it settles 1.7 degrees off by
40 degrees of tilt, set down 3 degrees left it settles at the same heading and tips at the
same angle, set down 3 degrees right it settles at -0.5 with only the end block of its tread
against the rail, and near 48 degrees swings about that block (11 degrees by 50) and goes
over early. The rigid prediction holds a heading and a rail along the whole wheel. Carrying 0.5 kg behind the arm: +1.8 to +4.0, each within 0.3 degrees of its
prediction, closer than as designed (1.3, where the swivelling front caster the prediction
does not know about gives way first). Fetch, 20 runs of the program solved once: every goal
met in every run; the cube in the bin at 31.9 to 33.6 s. The one outlier is a lesson in
stance. With 0.5 kg on the deck behind the arm and the arm tucked for the drive, the cart
rides on its rear caster (pitch -2.5 degrees; as designed +2.7, on the front one): its
centre of mass is now behind its drive axle. Every pose solved for the cart as designed
lands elsewhere: the jaws meet the cube 28 mm from where they were aimed, and as the arm
lifts, the cart rocks 5 degrees onto its front caster; the cube ends 12 mm short of 5 cm
(8.6 mm over as designed) until the cart rocks back on the way to the bin - "lifted" at
23.7 s instead of 16.2 (OPEN LW-016; ADR 0025 checks where the tool got to). Every run
of both sweeps is in `docs/sweeps/`. Checks in
`tests/test_variation.py` (14): the plan, refusals, moving and loading a design, the
payload's site and carrier, the friction spreads against their notes, the backend's
friction condition and its reset, the simulator's weight of the payload, a sweep and its
JSON, the headline, the ticks and what moved it most, the tilt table following the prediction with a
payload aboard, stopping a sweep stopping its worker processes, and the run report
starting a sweep in another process.

**Boundaries.** The placement and payload ranges are assumptions, stated; only the friction
ranges come from sources. A payload is a rigid block fixed to the machine, not loose cargo,
and has one default site. Eight random repeats are a sample, not a distribution: the
spread they show is a floor on the real one. The field itself is not varied (object masses,
the table's own friction), nor are the motors (unit-to-unit spread), sensing or timing. Each
run is deterministic: the same variation gives the same answer. The rigid stance prediction
still knows nothing of a rocking cart's dynamics or of a turned machine against a rail.
