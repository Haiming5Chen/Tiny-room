# The cart stands on all four: steady under its arm, and slow over a curb

**Problem.** ADR 0040 found the Fetch program pressing the cube into the table before the grasp
in 4 of 59 drawn set-ups that met every goal (0.6 to 2.0 N over 50 ms) and, carrying 0.5 kg,
knocking it onto its side (101 degrees) (OPEN LW-025). Traced: all five carried 0.44 to 0.5 kg on
the deck behind the axle. The kit cart's two swivel casters stood 6.5 mm above the floor its
drive wheels stand on, so it teetered on its drive wheels between them - 3.6 degrees nose up onto
the rear caster, 2.8 nose down onto the front one. Loaded, it stood on the rear caster through
the look; as the arm took its pose over the cube it tipped onto the front caster in a quarter of
a second, carrying the open jaws some 19 mm forward and 2 cm down, and the gripper's palm stop -
the rubber block between the jaws, 27.5 mm behind their middle - came down on the cube's top.
ADR 0025 had found the same rocking and corrected where the tool got to, and said "a machine that
rocks between its casters as its arm moves is still worth redesigning".

**Does an existing simulator solve it? Can we wrap it?** MuJoCo simulated the gap faithfully; it
is the design's. A cart with two drive wheels across its middle and a caster at each end is a
common layout, and carts that work on a flat floor set both casters to the drive wheels' floor;
ones that must cross steps spring them or mount them on a rocker. Tried in the program first
(owner's question, 13 Oct): gripping the cube nearer the jaws' tips keeps the palm clear but
squeezes it at 8 N instead of 4.8; jaws tilted 25 degrees from the pick on drop a cube held only
by its top 2 cm on the way (1 of 71). The owner chose the cart.

**Unique contribution.**
- *The casters reach the floor the drive wheels stand on* (`robots/mobile_platform.py`): each is
  set from the parts' own geometry - the lowest point of its subtree brought to that of the drive
  wheels - 6.5 mm lower than before; not a measured constant, so another caster or wheel finds
  its own. `mobile_platform_blueprint(caster_gap)` builds the cart with its casters that far up;
  `ROCKING_GAP` (6.5 mm) is the cart as it was.
- *The trade-off measured, not argued.* On all four the cart cannot pitch, and pitching was how
  it climbed: its front caster can rise onto a curb only by tipping the whole cart back about the
  rear caster, which lifts the drive wheels that push it. A 3 mm gap was tried as well: in the
  7 s the climbing checks give it, it climbed 10 mm and not 14, and loaded Fetch runs timed out
  at the bin as the cart rocked there.

**Blueprint and builder.** The example cart's Blueprint (two caster mount positions) and the
mobile manipulator built on it; saved designs keep their casters. The stance the Assembly tab
reports follows: "rests on 2 wheels and 2 supports; centre of mass 9.0 cm inside".

**Result.**

Standing, as the stance module predicts and the simulator settles (`tests/test_structure.py`):

| | casters 6.5 mm up | on all four |
| --- | --- | --- |
| mobile manipulator | wheels and front caster, 2.84 deg, margin 3.37 cm | all four, level, margin 9.0 cm |
| mobile platform | two tread patches, margin 0.33 cm ("rocks easily") | all four, level, margin 9.4 cm |
| the cart's pitch through a Fetch run, as designed / 0.5 kg | -3.9 to +3.0 / -4.0 to +3.0 deg | -0.2 to +0.2 / -0.2 to +0.1 deg |
| the drive wheels' load, arm over the cube, unloaded / 0.5 kg | 16.2 / 20.5 N each | 15.4 / 18.0 N each |

The casters now carry 15 % of the machine's weight. The five Fetch set-ups that pressed the cube,
the program unchanged: the table carries 0.17 to 0.18 N over 50 ms - the cube's weight - where it
pushed back at 0.61 to 2.25 N; the cube leans at most 1.5 to 6.1 degrees, where it leaned 11 to
101; every goal met in all five, the squeeze 4.8 to 5.1 N. Over 59 drawn set-ups and the twelve
chosen ([report](../sweeps/2026-10-14-fetch-handling-59-on-all-four.md)), every goal met in all 71:
no set-up pressed the cube into the table - 0 of 59 drawn (at most 6 %; 4 of 59 before, exact
McNemar p = 0.125: four set-ups is all the sweep can say, the trace says why); the table pushed
back at 0.18 N over 50 ms (median; 0.17 to 0.23, where it was 0.16 to 2.25); the cube leaned
3.1 degrees (1.2 to 8.8; it was 9.3, 4.0 to 101); the squeeze 5.0 N (3.7 to 5.1; 4.8, 3.7 to
6.7). Let go 6.8 cm over the bin's floor (6.4 to 6.9; 5.8, 3.1 to 7.0) - standing still, the
cart no longer tips the jaws down as they reach over the bin - landing at 2.1 N in a step. In the
bin at 36.8 s (median; 35.9 before).

Every field the cart runs, as designed:

| Field | casters 6.5 mm up | on all four |
| --- | --- | --- |
| Sprint, 5 m | 11.8 s | 11.9 s |
| Ramps 8, 14, 20 deg | none climbed | none climbed |
| Curbs 10, 20, 35 mm | 10 mm cleared at 3.8 s | 10 mm cleared at 10.4 s |
| Single curb 10 / 14 / 18 mm, 25 s to do it | over at 3.8 / 3.9 / 4.1 s | over at 10.4 / 10.8 / 11.6 s |
| Push: crate past 3 m | missed (26.5 N on the crate) | missed (22.8 N) |
| Doorway: through / in the bay | 14.2 / 16.4 s | 14.4 / 16.5 s |
| Tilt table: tipped at (predicted) | 53.98 deg (55.75) | 54.61 deg (55.58) |
| Fetch: lifted / in the bin | 19.5 / 36.2 s | 19.6 / 36.2 s |

At a curb the cart now stalls, its motors at their limit, until it has slewed far enough for a
drive wheel to meet the curb and climb it; the curbs it climbs are the same, the time is not.
On the tilt table, over 18 set-ups ([report](../sweeps/2026-10-14-tilt-mobile-manipulator-on-all-four.md)),
it tipped between 53.3 and 59.4 degrees (54.0 to 58.5 before), within -2.3 to +1.0 degrees of
the stance module's prediction for each (-1.8 to +0.7). Shoved down the sprint lane
([report](../sweeps/2026-10-14-sprint-mobile-platform-disturbed-on-all-four.md)): 4 N s, 9 of 9
and pushed 16 cm (12 before); 8 N s, 3 of 9 (2) and pushed 89 cm (79) - the drive wheels' 15 %
less grip lets a shove carry it further. Fetch under every disturbance
([report](../sweeps/2026-10-14-fetch-mobile-manipulator-disturbed-on-all-four.md)): the same
set-ups fetched as before, 9 of 9 under each shove and move and none with a failed camera (named,
as ADR 0038 has it); the cube leaned 2 to 5 degrees (median; at most 9, was 17), and nothing but
the jaws pushed it harder than the bin's 0.58 N (3.1 N before, moved 2 s after the look).

Shoved 6 N s at the table (FR-006's check): the shove now comes as the open jaws reach down - the
cart stands still sooner - and blind, a jaw knocks the cube over (103 degrees); before, the jaws
then caught it on its side and delivered it so (96 degrees), which the goals could not see. The
program as it is, looking, goes back to its stop and fetches it upright (1.6 degrees). Frozen as
the cube is moved, on trust, the second reach is now stopped on the moved cube instead of closing
on nothing beside it.

Held by `tests/test_structure.py` (the stance, the rocker with its casters up, the Assembly tab's
words), `tests/test_fields.py` (a rocking cart climbs 18 mm and not 24; on all four it stalls at
18 mm and gets over at 11.6 s, 4.1 s rocking), `tests/test_disturbance.py`,
`tests/test_camera_faults.py` and `tests/test_rise_and_place.py` (as above). Suites on MuJoCo
3.10.0: 991 passed with a display, 944 headless.

**Boundaries.** Flat floors: four rigid points on an uneven one put a wheel or a caster in the air,
and nothing here models a sprung caster or a rocker. The drive wheels carry 15 % less, so a
result limited by their grip - a push, a climb - can come out lower. The cube is still let go
over the bin, now 6.8 cm (OPEN LW-024). Nothing changes for saved designs.
