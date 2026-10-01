# Machines start on the floor; the curb history was the fall

**Problem.** The mobile platform and the arm on a cart were assembled with the chassis rail
13 cm up, which leaves their wheels 4.35 cm above the floor (OPEN LW-014): every run began
with a fall of 44 mm. The two-wheel example started 1.0 cm up and the bare block 8.5 cm.
Nothing said so; the build stage showed a design in the air without comment. A field that
drives from its first step, the Curb run, landed the platform with its wheels already turning.
ADR 0022 had read the curb answers on MuJoCo 3.3.7 - stops at 18 and 20 mm after a 10 mm
curb, climbs at 22 and 24 - as the engine's.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo starts a body where the model
puts it; putting the machine on the floor is the builder's job. The editor already sets a base
down (`grounded`, the "Free base + ground" button). The examples were assembled without it.

**Unique contribution.**
- *The examples start on their lowest point*, 2 mm clear of the floor: the mobile platform
  (and so the arm on a cart) is set down after it is assembled, the two-wheel example's chassis
  sits at 12.2 cm and the block at 4.7 cm. As a run starts they settle 2.5 to 2.9 mm, the
  contacts taking the weight, instead of falling.
- *The build stage says when a design starts in the air*: "Starts 4.3 cm above the floor and
  falls when a run starts: Free base + ground sets it down", for any design whose free parts
  start more than 5 mm up (`construction/structure.py`, `clearance`).
- *The curb history, measured again.* Started on its wheels, the platform gives the same
  answer alone and after a 10 mm curb in all four configurations of ADR 0022:

  | | 18 / 20 / 22 / 24 mm, alone and after a 10 mm curb |
  | --- | --- |
  | 3.3.7 as used | climb / stop / stop / stop |
  | 3.3.7 with multiccd | climb / stop / stop / stop |
  | 3.14 as released | climb / climb / climb / stop |
  | 3.14 without multiccd | climb / stop / stop / stop |

  What the fall did: landing with its wheels driven left the platform yawed and a caster
  swivelled, 6 degrees as it reached the lone curb and 37 degrees at the curb after the 10 mm
  one, where a platform started on its wheels arrives with both casters within 2 degrees of
  straight. A caster meeting a curb edge turned 37 degrees makes a different climb. So the
  history in ADR 0022's table came from the start, not from the engine; the engine decided only
  how much a swivelled caster mattered (with multiccd, which makes several contacts per pair,
  the answers held even with the fall). What is left between releases is how far past its
  20 mm radius the caster climbs, and it follows multiccd: it stops at 20 mm on 3.3.7 and on
  3.14 without multiccd, and climbs 22 mm on 3.14 as released.

**Blueprint and builder.** Saved designs are not moved: one built in the air still starts
there, and the build stage says so; "Free base + ground" sets it down as an undoable edit.
Only the examples are built differently.

**Result.** The curb-history check passes on 3.3.7 as well as 3.14 and is no longer marked as
expected to fail. With the manipulator started on its wheels: stance margin 3.34 cm on 3.3.7
and 3.35 cm on 3.14, predicted 3.37 (3.39 and 3.40 after the fall); on the tilt table it tips
at 54.5 degrees on 3.3.7 and 52.6 on 3.14 (54.2 and 52.4), the loaded caster still swivelling
86 degrees first. The record of the twelve releases in ADR 0022 was measured with the fall;
its steps between releases stand. Checks: `tests/test_structure.py` (the examples start within
5 mm of the floor and a lifted design reads its height; the platform and the manipulator
settle less than 3 mm as a run starts), `tests/test_fields.py` (the curb history, unmarked).

**Boundaries.** A run starts a design where it was built; it does not set it down, so a
design built in the air still falls, with a warning. Which release is right near the
caster's radius is still open: that needs a real caster and curb (ADR 0022).
