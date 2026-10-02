# MuJoCo 3.10.0 on every machine, with one contact per convex pair

**Problem.** The project pinned MuJoCo 3.3.7; the newest release is 3.14.0. The owner's
Mac is an Intel Mac, and PyPI has MuJoCo wheels for macOS on x86_64 up to 3.10.0 and none
from 3.11.0 on, for any Python: a newer release there means building MuJoCo from source.
The owner chose one version on every machine, 3.10.0 (FR-002, 2 October 2026). Run
unchanged on 3.10.0, the headless suite failed one physical check: the four-wheel test
cart's coast-down slowed 5.0 % faster than the closed form from its sourced rolling
resistance - 0.2301 against 0.2191 m/s^2, where 3.3.7 gave 0.2195.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo does, with a flag. The
cause is its multiccd option - several contacts for a pair of convex geoms - which 3.8.0
turned on by default; the radar filed that entry as breaking (ADR 0021) and ADR 0022 had
measured its effect on the tilt table. `mjDSBL_MULTICCD` turns it off.

**Unique contribution.**
- *The pin.* `pyproject.toml` (both extras) and the lock file say `mujoco==3.10.0`. The
  radar reads its pin from there, so its digest now lists MuJoCo's changes after 3.10.0.
- *The cause, measured.* With multiccd a cylinder wheel on the box floor touches at four
  contacts - three at one edge of its tread, one at the other - within 0.2 mm of each
  other along the direction of rolling, their normals tilted by a thousandth of a radian
  either way. As the wheel rolls, the solver's soft contacts load the leading ones more
  (8.8 N on the leading contact at one edge, none on the trailing one), which moves the
  floor's reaction ahead of the axle: the mechanism of rolling resistance itself, made by
  the solver instead of the tread, and growing with speed. Coast-down deceleration against
  the closed form (b M g / r over the effective mass):

  | cart rolling at | 3.3.7 | 3.10.0 as released (multiccd) | 3.10.0, one contact per pair |
  | --- | --- | --- | --- |
  | 0.4 m/s | -2.0 % | +1.4 % | -2.0 % |
  | 0.8 m/s (the test) | +0.18 % | +5.0 % | +0.18 % |
  | 1.6 m/s | +0.15 % | +6.3 % | +0.15 % |

- *The choice.* The adapter compiles every model with multiccd off (`MULTICCD = False` in
  `physics/mujoco_backend.py`, the one place models are compiled): one contact per convex
  pair, as in every release before 3.8 and in every result this project has recorded.
  Little World's rolling loss is a sourced number, Hamilton's lever arm, applied at each
  wheel's hinge (ADR 0011); with multiccd the engine adds a loss of its own, unsourced and
  speed-dependent, to every cylinder wheel on a box. Its extra contacts are not a tread's
  contact patch either: they lie within 0.2 mm of each other, where a real tyre's patch is
  centimetres long.
- *What 3.10 brings.* The DC-motor actuator (3.7, with resistance, motor constants,
  inductance, cogging, an on-board controller, heating and LuGre friction; FR-004) and the
  system identification toolbox (3.5, `mujoco[sysid]`; FR-010). Not reachable on the pin:
  moving surfaces (3.11), the PID actuator (3.12), the discrete integrator and cylinder
  multicontact (3.13) - FR-014.

**Blueprint and builder.** Untouched: saved designs load and run unchanged.

**Result.** From 3.3.7 to 3.10.0 with one contact per convex pair, nominal runs:

| | 3.3.7 | 3.10.0 | 3.10.0 with multiccd, for comparison |
| --- | --- | --- | --- |
| tilt table, arm on a cart, goes over at (predicted 55.75 about the rail) | 54.48 deg | 53.99 deg | 54.64 deg |
| settled stance: tilt, margin (predicted 2.84 deg, 3.37 cm) | 2.8 deg, 3.34 cm | 2.89 deg, 3.36 cm | 2.72 deg, 3.34 cm |
| Fetch: at the table, cube lifted, in the bin | 9.65, 16.68, 33.97 s | 9.58, 16.37, 33.04 s | 9.59, 16.31, 33.84 s |
| curbs, mobile platform | 10 mm climbed at 3.78 s; 20, 35 not | the same | the same |
| sprint, mobile platform | 11.8 s | 11.8 s | 11.8 s |
| coast-down, against the closed form | +0.18 % | +0.18 % | +5.0 % |

The tilt table's half degree is the box-box distance fix of 3.4.0 that ADR 0022 named
(-0.6, and +0.2 from 3.7). Both suites pass on 3.10.0: 643 tests with a display, 606 headless. `tests/test_drivetrain.py`
holds the choice: every wheel of the test cart meets the floor at one contact and the
flag is set; the coast-down test holds its 1 %. The staged forward pass of ADR 0010 is
still bit-identical to `mj_step` on 3.10.0 (tested).

**Boundaries.** The suites ran on Linux with Python 3.11; the owner's Mac runs 3.10.0 only
once its environment is reinstalled. Turning multiccd off is a choice for this project's
sourced rolling loss, not a claim that MuJoCo's multiple contacts are wrong: a box resting
on a box keeps MuJoCo's own box-box collider either way, and grasps, curbs and the tilt
table were validated with one contact per convex pair. One contact also means a cylinder
wheel touches a box at one edge of its tread, as it did on 3.3.7.
