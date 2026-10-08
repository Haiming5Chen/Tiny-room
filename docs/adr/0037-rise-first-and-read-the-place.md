# Looking again: rise off the cube first, and read the place before doubting it

**Problem.** Two faults in looking again (ADR 0033), both shown by the paired runs of ADR
0036. Of 59 drawn Fetch set-ups that met every goal undisturbed, the cube moved 5 cm sideways
2 s after the look broke one (repeat 9): the cube moved 26 ms after the picture before the
jaws went down, a jaw came down on it and the reach was stopped; going back to the stop's
approach - one move of every joint from the low pose to `ready` - the arm dragged the cube 3
cm towards the cart, the jaw still on it, and over the table's edge, and the next look found
nothing (OPEN LW-023). And in 2 of the 60 undisturbed set-ups (repeats 35 and 43; 1 of 71 in
ADR 0035's sweep) the picture before the jaws went down found nothing, though nothing had
moved, and the program looked again: 4 s lost. Traced in repeat 35: the open jaws' palm hid
the cube's top face, which the finder needs (ADR 0032), while 148 of the 170 rays of that
picture that would meet the cube ended on its surface - it was plainly there (OPEN LW-022).

**Does an existing simulator solve it? Can we wrap it?** Neither is the simulator's: how a
program backs out of a reach that went wrong, and what it concludes from a picture, are the
program's. Backing out the way the hand came in is the approach-and-retreat of pick-and-place
planners (MoveIt's pick pipeline has both). Asking whether a known part is still where it
was seen, by comparing the depth the camera measures with the depth the part's own shape would
give there, is the visibility test of depth-based mapping; it needs no model of the jaws.
Wrapped: MuJoCo's ray casting through the camera of ADR 0032, numpy.

**Unique contribution.**
- *Rise first.* A reach for the object that is stopped, and a grasp that holds nothing (its
  jaws opened first, as before), first go back to the pose the arm reached down from - the
  way they came, at the reach's speed, each joint straight back - and only then to the stop's
  approach as ADR 0033 does. The runner keeps that pose when a reach for the object begins.
  Seen moved before the reach, the arm has not gone down and goes straight back.
- *Read the place.* When the picture before the jaws go down finds nothing, the camera says
  what it shows where the look saw the object (`Eye.place`, `boxes.place`): each ray that would
  meet the object - 80 % of its size, so that a sighting's error does not matter - is followed
  to where it would meet the object's surface: within the depth noise (three standard
  deviations, at least 5 mm) it ends on the surface, nearer it ends on something over it,
  further it passes where the object was. Something nearer over more than half of them:
  hidden. Otherwise there, when more end on the surface than beyond it; empty, when not. Only
  empty looks again; there and hidden go down, and if the object has gone after all the grasp
  finds out and the program looks again then. A camera that cannot say (a `see` without
  `place`) looks again, as before.

**Blueprint and builder.** Untouched; programs are the same data. Both rules are the runner's,
as looking again is.

**Result.**

ADR 0036's paired sweep again - the design as designed and 59 drawn set-ups, the cube moved
5 cm sideways 2 s after the look
([report](../sweeps/2026-10-08-fetch-moved-later-paired-59-rising.md)):

| | before | rising first, reading the place |
| --- | --- | --- |
| broken by the move, of 59 | 1 (0 to 9 %) | **0** (at most 5 %) |
| every goal met, moved | 59 of 60 | **60 of 60** |
| undisturbed, looked again for nothing | 2 of 60 | **none** |
| the cube in the bin, moved, against undisturbed (median) | +3.1 s | +3.1 s |

The simulator is deterministic, so the two versions can be compared set-up by set-up as well.
Undisturbed, two set-ups ran differently: repeats 35 and 43 no longer look again and finish 4.1
s sooner (36.5 and 35.7 s); the other 58 met their last goal at the same time to the
millisecond. Moved, eleven ran differently, every one of them a reach stopped on the cube - it
had moved just after the picture before the jaws went down: repeat 9 is fetched, and the other
ten, which had recovered before, finish 0.35 to 0.6 s sooner in nine and 0.3 s later in one;
the other 49 met it at the same time. The picture of repeat 35, traced: of the 170 rays that
would meet the cube, 148 ended on its surface and 22 on the jaws in front of it - there; with
the cube moved 5 cm, 159 of them passed where it had been - empty. Every disturbance on the
nine set-ups of ADR 0030, 9 of 9 each with the same median changes as ADR 0035's
([report](../sweeps/2026-10-08-fetch-mobile-manipulator-disturbed-rising.md)); the cube set
down before the run, the same 17 of 19 fetched looking (6 blind), within 0.1 s.

Held by `tests/test_rise_and_place.py` (10): the place on made-up pictures - there, empty
where it was moved from and there where it was moved to, hidden behind a palm, there with its
top covered and its front plain - where the finder finds nothing - and no answer where the
picture does not reach; a reach stopped
on the cube rises the way it came before turning for the approach; a missed grasp opens the
jaws and then rises; seen moved before the reach, no rising; found nowhere before the reach,
the place decides (there and hidden go down, empty and a camera that cannot say look again);
and, in full physics, the two set-ups of LW-022 and LW-023.

**Boundaries.** The place is read for the part standing as its size says, square to the
field: a cube turned a few degrees keeps 80 % of its size inside it, a part lying on its
side does not. Rising goes back along a straight line in the joints, which retraces the reach
because the reach was one such line. Hidden is taken for there: a part moved under the jaws'
cover is found by the grasp, not before. A reach that cannot settle because the machine was
pushed off its stop still goes straight back to it (ADR 0031).
