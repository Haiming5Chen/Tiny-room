# The stop follows the cube: the Fetch program looks before it drives

**Problem.** The table camera found the cube within 2 mm wherever it was set down (ADR 0032),
yet the Fetch program fetched 13 of 14 placements: the one 6 cm further along the table was
seen within 0.4 mm and was out of the arm's reach from the stop planned for it. The camera
sees the table from anywhere, but the program looked only once it had driven to a stop
planned from where the cube was supposed to be; and it searched 12 cm round that plan, so a
cube set down 15 cm to the side would not have been seen at all (FR-016, OPEN LW-021).
Measured for this record: at the cube's height the arm on the cart reaches up to 28 cm ahead
of its drive axle (26 cm with the cube 10 cm to the side, 24 cm at 15 cm), and at the planned
stop - 23 cm short of the cube - the cart's front, its swivel caster 15.7 cm ahead of the
axle, stands 3.3 cm from the table's edge.

**Does an existing simulator solve it? Can we wrap it?** Placing a mobile manipulator's base
from what it perceives is base placement. Learned answers (capability maps, anchor-pose
supervision: two titles of the 5 October reading) need training; the classic one is an
inverse reachability map (Vahrenkamp, Asfour and Dillmann, ICRA 2013): from the arm's inverse
kinematics, where the base may stand for a tool pose, and the stop nearest the plan among
them. Here the plan already holds a stop solved for the cube where it was planned, and the
arm's poses stay valid if the base moves as the cube moved - a translation of the stop - as
long as the base keeps clear of the table; what the base cannot follow the arm has to reach,
and the arm's own solver (ADR 0025's aim) says whether it can. So no new planner: the
runner, the template, and MuJoCo's geometry for the clearance.

**Unique contribution.**
- *A stop at an object* (programs version 4). A `goto` may name the object it drives to.
  Once a look has seen that object, the stop moves as the object was seen to have moved from
  its plan: sideways fully, towards it along the stop's heading at most `secondary` metres,
  so the machine keeps clear of what the object stands on (`Runner.follow`). Leaving a stop
  that followed, the next stop at the same object moves as that stop did - the machine backs
  off from where it stood, not from where the object was seen once it was there. A stop that
  followed is kept: going back to it after a push (ADR 0031) or to look again (ADR 0033) goes
  back to where it moved. A version-3 reader refuses such a program instead of misreading it.
- *Fetch looks before it drives.* The template's first look comes before the drive - no
  watch, three agreeing pictures, about 0.3 s - and both looks search 25 cm round the plan,
  the table's half-width (a look's `secondary`; the camera's own default stays 12 cm). The
  stop at the cube and the stop it backs off to follow it, their limit set when the program
  is solved: how far the cart, standing at the stop, could drive on before one of its parts
  meets one fixed to the world - 3.3 cm, the table - less 1 cm (`KEEP_CLEAR`).
- *Out of reach, said before moving.* `ToolMotion.aim` answers False, no longer None, when a
  point is out of reach from where the machine stands; a pose re-aimed where a look saw its
  object then fails at once - "Seen 10 cm from where it was planned: out of the arm's reach
  from this stop" - instead of reaching for where the cube was planned and closing on air.
- The picture just before the jaws go down (ADR 0033) is taken of where the look saw the
  object, wherever that was, rather than of where it was planned.

**Blueprint and builder.** Untouched. In the program workspace a stop at an object reads
"Stop at the fetch_cube, where it is seen / 2.3 cm nearer at most", and editing it, or a
look, keeps its object and its search.

**Result.**

| The cube set down before the run | Looking at the stop (ADR 0032, 0033) | Looking before the drive, the stop following |
| --- | --- | --- |
| ADR 0032's 14 placements: up to 8 cm sideways, 6 cm along, turned | 13 of 14 | **14 of 14** |
| 6 cm further along the table | missed: out of reach | fetched |
| 7 cm further along (run on its own) | - | fetched |
| 8 and 10 cm further along | - | refused at the table: out of the arm's reach |
| 15 cm to the left; to the right | - (outside the 12 cm search) | fetched; fetched |
| 6 cm along and 15 cm to the left | - | fetched |

The camera saw the cube within 2.1 mm of where it was in every run. Blind, the same 19
placements give 6. Undisturbed and drawn 59 times (71 runs with the one-at-a-time ones): every
goal in all 71, 59 of 59 drawn - at least 95 % (ADR 0028) - the cube in the bin after 35.9 s
median against 35.8 s before: the first look costs about 0.3 s, and the stop moves only by
what the camera saw. One run looked again although nothing had moved: the one picture before
the jaws went down did not find the cube under them (ADR 0033's single-picture check; each
picture's noise is drawn in turn, so the first look's pictures move where it falls), and it
was fetched 4.4 s later than its neighbours (OPEN LW-022).

Disturbed as ADR 0030 does, on the same 9 set-ups each: every disturbance 9 of 9, as before,
the median change against each set-up undisturbed within 0.6 s of ADR 0033's - shoved 4 and 6
N s, +1.1 and +11.5 s (+0.8 and +11.3); the cube moved 3 and 5 cm as the cart stands at the
table, -0.6 and -0.9 s (-0.9 and -1.1); moved 5 cm 2 s later, +3.2 s (+2.6). A first version
moved the backing-off stop as the cube was last seen too: after a cube moved at the table it
backed off sideways, 1.3 to 1.8 s slower; it now moves as the stop at the cube did.

Held by `tests/test_stop_follows.py` (13): the stop follows sideways fully and towards its
object only as far as allowed, along its own heading, its own object only; going back after a
push returns to the stop that followed; the backing-off stop moves as the stop did; an out-of-reach pose fails before moving and says how
far the object was seen from its plan; version 4 and its fields; the Fetch template's looks,
stops and limit; the cube set down 6 cm further along and 15 cm to the side fetched; 10 cm
further, left with the reason. `tests/test_look.py`, `test_look_again.py` and
`test_aimed_poses.py` follow the extra look and `aim`'s False.

**Boundaries.** The stop moves without turning: a cube far to one side is approached on the
planned heading from beside where it was planned. A cube beyond the arm's reach from every
stop clear of the table is refused, not approached from another side of the table - its
sides and back are further from the cube than its front. The clearance counts parts fixed to
the world (not other loose objects), from box corners (exact for boxes, generous for other
shapes), with the cart as it stood when the program was solved. The 25 cm search is chosen
for the Fetch table. The first look is before the drive, so a cube moved during the drive is
seen only at the stop, as before (ADR 0032, 0033).
