# The Fetch keeps its closing ramp: a squeeze set by current, measured and not adopted

**Problem.** ADR 0066 made a squeeze a setting: the kit jaws' servos can cap their current, so a
program says how hard to hold in newtons at each pad's centre. The Fetch's own program still closes
its jaws for 1 s and squeezes with what the ramp leaves, and FR-037 asked that it change only after a
side by side: on the 71 tuning set-ups (seed 1) every goal still met, the squeeze within 0.3 N of its
setting across set-ups, the cube's creep and the bin's push no worse; then 59 held-out draws (OPEN
LW-041). ADR 0066's one run as designed, closed fully at 7 N, met every goal 0.7 s later with the
grip's friction at most 60 % in use, where the ramp's reached 80 %.

**Does an existing simulator solve it? Can we wrap it?** Nothing new is modelled: the same sweep
(ADR 0024) runs the Fetch as it is and with `tool_motion.squeezed(program, 7)`, set-up by set-up,
paired (ADR 0036), with the handled-part measures of ADR 0040 and the grip's friction use of ADR 0061.

**Unique contribution.** A measurement, and the decision it leads to: the Fetch's program is not
changed. Recorded in `docs/sweeps/2026-11-05-the-fetch-squeezed-by-current.md`; the held-out seed
20261103 is in the seed ledger.

**Blueprint and builder.** Untouched.

**Result** (paired, the Fetch as it is against closed fully at 7 N):
- *Tuning set-ups (seed 1), 71 pairs*: every goal met 71 of 71 either way - no pair broke, none mended
  (exact McNemar p = 1.0). Set to 7 N at the pads' centres, the jaws pressed the cube with 5.2 to 12.2 N
  (median 10.0; the ramp 3.2 to 5.0, median 3.6): the cube sits nearer the jaws' pivots than the pads'
  centres - the rotary jaws pull it towards the palm as they close (OPEN LW-028) - and a squeeze set
  as a torque reaches it as more force, by as much as where it sits. Its spread over the set-ups is six
  times the ramp's (standard deviation 2.29 against 0.40 N): FR-037 asked for 0.3 N. The grip's
  friction in use at most while carried fell from 96 % at the median (68 to 100) to 85 % (53 to 100);
  the bin's push was the same (0.52 N); the cube fell slightly further when let go (0.48 against 0.37
  cm); and it reached the bin 0.73 s later (0.47 to 1.02).
- *Held-out draws (seed 20261103), 59 pairs*: the same - every goal met 59 of 59 either way (p = 1.0);
  the squeeze 5.4 to 12.2 N at 7 N (median 7.7; the ramp 3.2 to 5.1), its spread 2.39 N against 0.50;
  the grip in use at most 82 % against 95 % at the median; the bin's push the same; the cube in the
  bin 0.76 s later (0.51 to 0.87).
- So the squeeze by current gives the Fetch no goal it did not meet, a less even squeeze and a slower
  cycle, for more grip to spare. It is not adopted: the Fetch keeps its ramp. A squeeze in newtons stays
  a block a program may use.

Held by the sweep record; no code or test changed, so the suites are 5f41dd9's (1152 passed with a
display, 1087 headless).

**Boundaries.** One squeeze, 7 N, at the jaws' full close; a smaller one, or one set where the cube
sits (LW-028), was not swept. The squeeze in newtons is the hardest push from one jaw averaged over 50
ms (ADR 0040), not a measured force at a pad. Held-out draws certify only the drawn set-ups (ADR 0049).
