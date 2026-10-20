# Set down, not dropped: the jaws hold the cube's upper half, firmly, and tilt over the bin

**Problem.** The Fetch program let the cube go over the bin: 5.8 cm over its floor (median) on
the rocking cart, landing at 1.9 N in a step (ADR 0040, OPEN LW-024), and 6.8 cm on the cart
standing on all four, landing at 2.1 N (ADR 0041). A vial would not be dropped. Lowering until
the cube touches the floor was the obvious fix and is not open to this machine: from any stop 22
to 28 cm short of the drop point, the kit arm cannot bring the point between its jaws lower than
8.5 cm over the bin's floor while they stay level - any lower and it would hit its own cart.
Tilted 25 degrees, that point reaches 4 cm.

**Does an existing simulator solve it? Can we wrap it?** It is the program's. Placing is the
other half of pick and place, and planners choose the grasp with the place in mind (a grasp the
placement can also take) and approach the place along the gripper's own axis. Tried first
(13 Oct, the owner's question): jaws tilted 25 degrees from the pick on set the cube down, but
held only by its top 2 cm it was dropped on the way in 1 of 71 runs and whenever it had been
moved 5 cm; tilted over the bin only, on the rocking cart, loaded carts pitched forward there
and pressed the cube onto the bin's floor at 3 N. The owner chose to tilt over the bin only,
once the cart stood still (ADR 0041).

**Unique contribution.**
- *Grip the upper half* (`control/tool_motion.py`, `fetch`): the grasp is raised until the jaws'
  lower edge is level with the object's middle - found from the jaws' own geometry at the level
  grasp, 18.3 mm for the kit gripper - so the lower half hangs below the jaws and meets the
  place first, and the jaws close 20 mm over the table instead of 1.7.
- *Tilt over the place, as far as lowers it most*: carried level, over the bin the jaws try their
  own angle and then 5 to 60 degrees in steps of 5; for each the tool is stepped down 2.5 mm at a
  time until the object's lowest corner would come within `SET_GAP` (2 mm) of the floor or the
  jaws within `JAWS_CLEAR` (5 mm), or the arm out of reach or into its own machine; the tilt that
  brings the corner lowest wins, the smaller of two within a millimetre. The object's corners
  ride in the tool's frame from the grasp (`_held_corners`), so this is geometry, not a fit.
  Where no tilt reaches down at all, it lets go as low as it reaches, as before.
- *Held firmly enough to be tilted* (`SQUEEZE`): the jaws close on a 1 s ramp that ends 0.2
  degrees past the kit cube, so through the carry they held it at about 0.5 N a pad - three
  times its weight; the 4.8 to 5.0 N squeeze ADR 0040 and 0041 report is the jaws' arrival.
  Level, that held.
  Tilted, the first sweep of this design found 3 of 71 set-ups where it did not: in one (repeat
  44: the pads' friction low in its range, 0.44 kg on the deck) the cube crept 10 mm down the
  pads as the cart drove, turned in the jaws as they tilted and slipped out, its lowest corner
  3.2 cm over the bin's floor; the jaws, still coming down, then pressed it there at 1.65 N over
  50 ms; in two
  it turned 2 to 3 degrees in the jaws and its corner met the floor while still held (0.6 N).
  Once the grasp is felt, the jaws now close 0.02 s more - 0.6 degrees, about 1 N a pad, the
  smallest step tried, which held all three. A grasp should be as firm as holding needs and no
  firmer ([How Firm Should a Grasp Be?](https://arxiv.org/abs/2610.11221), from the weekly
  reading of 19 Oct): the squeeze over 50 ms stays under ADR 0041's.
- *What a part went through, told apart* (`inventory/handling.py`): set down tilted, every cube
  leans 25 degrees in the jaws, which hid what ADR 0040's lean was for; a run now also reports
  the most it leaned before the machine first held it - two of its bodies pushing it from
  opposite sides, each at 0.05 N or more - and how far it leaned when the run ended. And a fall
  is now the most it fell after the machine let go, before the machine touched it again: repeat
  44's cube fell 3.9 cm, but the jaws touched it last on the floor, and ADR 0040's measure said
  it had not fallen at all.

**Blueprint and builder.** Untouched: a program's data are the same, only the poses the Fetch
template solves differ and one block more (the squeeze), in the Program workspace as in sweeps.

**Result.** As designed, on the cart standing on all four: the jaws close 18.3 mm higher and
squeeze at 3.5 N over 50 ms (5.1); over the bin they tilt 25 degrees, the cube's lowest corner
planned 2.5 mm over the floor and the jaws 10.8 mm. It is let go 6 mm up (6.8 cm before), falls
0.8 cm, lands at 0.78 N in a step and 0.29 N over 50 ms (2.2 and 0.58) and comes to rest
upright; in the bin at 36.8 s (36.2). Carrying 0.5 kg: 0.67 N, 0.5 cm, upright. Kept level, the
arm would bring the cube's lowest corner no nearer the floor than 4.9 cm.

Over 59 drawn set-ups and the twelve chosen
([report](../sweeps/2026-10-20-fetch-set-down-59.md); before, ADR 0041's
[report](../sweeps/2026-10-14-fetch-handling-59-on-all-four.md)), every goal met in all 71:

| Fetch, 71 runs: median (least to most) | let go over the bin (ADR 0041) | set down |
| --- | --- | --- |
| fell when let go | 6.8 cm (6.4 to 6.9) | 0.3 cm (0.1 to 1.1) |
| the bin's push on the cube, in a step | 2.14 N (1.69 to 2.25) | 0.52 N (0.42 to 0.78) |
| the bin's push, over 50 ms | 0.57 N (0.56 to 0.58) | 0.26 N (0.23 to 0.30) |
| the squeeze, over 50 ms | 4.98 N (3.68 to 5.13) | 3.89 N (3.35 to 4.98) |
| the table's push, over 50 ms | 0.18 N (0.17 to 0.23) | 0.18 N (0.16 to 0.23) |
| leaned before it was held / at rest | - | 0.0 / 0.0 degrees (at most 0.1 / 0.0) |
| in the bin | 36.8 s (36.1 to 37.6) | 37.3 s (36.7 to 38.1) |

The first sweep of this design, without the squeeze, set the cube down as gently in 68 of 71
and not in the three named above: repeat 44 fell 3.9 cm and was pressed into the bin's floor at
1.65 N over 50 ms; repeats 21 and 35 were pressed there at 0.63 and 0.60 N while still held.
With it, the three fell 0.3 to 0.4 cm and the bin pushed back at 0.25 to 0.28 N.

Under every disturbance ([report](../sweeps/2026-10-20-fetch-mobile-manipulator-disturbed-set-down.md)):
the same set-ups fetched as on the cart's own sweep (ADR 0041) - 9 of 9 under each shove and
move, none with a failed camera, named - and each cube set down, falling 0.2 to 0.8 cm (median
by disturbance), the bin pushing back at 0.26 to 0.29 N over 50 ms. One thing moved the wrong
way. With the cube moved 5 cm sideways 2 s after the look, the higher pose over the cube is
reached 0.3 s sooner, so the last picture before the jaws go down (ADR 0033) is now taken just
before the move instead of just after: in all 9 set-ups a jaw came down on the moved cube and
pressed it into the table at 3.3 N over 50 ms (0.26 N before) for about 2 s, until the reach
timed out and was stopped (ADR 0033, 0037); the program then looked again and fetched it
upright, the cube having leaned 4 to 5 degrees before it was held (OPEN LW-029).

Shoved 6 N s at the table (FR-006's check), the cart slides 7 cm as the open jaws reach down.
Going down to the cube's middle, a jaw came down on it and, blind, knocked it over (103
degrees, ADR 0041); going down to its upper half, the cube leans under a degree until the jaws
hold it, and blind it is fetched and set down upright. With the cube moved 5 cm and the program
blind, a jaw still comes down on it and presses it into the table, at 3.2 N (5 N before);
looking, it is fetched.

Held by `tests/test_set_down.py` (5): the plan (level at the table, the jaws' lower edge at the
cube's middle, 25 degrees over the bin, the corner 2.5 mm over the floor, the jaws clear); the
level fallback 4.9 cm up; the cube set down without a fall and at rest upright, as designed and
carrying 0.5 kg; repeat 44, held firmly, set down. `tests/test_handling.py` (7): the lean before
it was held and at rest; a part that slips out and is then pressed has still fallen.
`tests/test_disturbance.py`: the shove at the table, blind and looking. Suites on MuJoCo 3.10.0:
998 passed with a display, 951 headless.

**Boundaries.** The plan takes the object to stay where the jaws closed on it; the kit's rotary
jaws pull it about 11 mm towards the palm as they close, so tilted it hangs a few millimetres
higher than planned and is let go 3 to 6 mm over the floor instead of 2.5 (OPEN LW-028). There
is no touch sensing: the height comes from the plan and the aimed pose's 5 mm, so a floor not
where the field says would be met harder or missed. The cube comes down on an edge and settles
onto its face; an open vial tilted 25 degrees may spill - this sets down what can be tilted. The
squeeze is a duration of the jaws' ramp, sized on the kit cube and gripper: a heavier or more
slippery part, or another gripper, needs its own (FR-026 would set it from the servo's current).
The search is the kit's: 5 degree steps, a 2.5 mm stride, one bin.
