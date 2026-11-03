# Plan the draws before the run: what a sweep can show, said before it runs

**Problem.** A comparison that could not have shown its effect says nothing when it finds none. ADR
0041 counted 4 of 59 set-ups pressing the cube into the table before the cart stood on all four
wheels and 0 after - exact McNemar p = 0.125, the smallest p four pairs can give - and wrote down,
rightly, that four set-ups is all the sweep could say. How much it could have said was not computed
before the run, and the window, offering a sweep of 20 or 45 runs, said nothing of what it could
show. FR-039 (third in the weekly reading of 2 November, after a pre-registered study withdrew a claim
its test was too weak for, arXiv 2610.30478) asked that the draws be planned.

**Does an existing simulator solve it? Can we wrap it?** Not a simulator's question. The tests are
the sweeps' own - the exact McNemar test on paired runs (ADR 0036) and a one-sided Clopper-Pearson
bound on a rate (ADR 0028) - and their power is a sum over every outcome the draws could give; no
library is needed for it.

**Unique contribution.**
- *Power, exactly* (`inventory/power.py`, standard library): `mcnemar_p`; `mcnemar_power(n, broke,
  mended)`, the chance that n paired draws show a difference at p 0.05 when each pair breaks with one
  chance and mends with another, summed over the discordant pairs and their split; `draws_for`, the
  fewest draws for 80 % power; `zero_bound` and `bound_draws` for a rate bounded by draws that all
  succeed; `to_show`, how many of n pairs a disturbance must break for the test to show it; `plan`, in
  words, with "underpowered" when a null result would be inconclusive.
- *In the window*: before a sweep runs, under its button, what it can show - "8 drawn: if all succeed,
  failures under 31 %" for the variations, "to be sure it breaks runs, it must break 6 of the 8 drawn"
  for the disturbances.

**Blueprint and builder.** Untouched.

**Result.** The numbers FR-039 gave, reproduced exactly: with every discordant pair one way the exact
McNemar test needs 6 for p < 0.05 (4 give 0.125, 5 give 0.0625, 6 give 0.031); at a 4 in 59 press rate
59 paired draws had a 21 % chance to show it, 116 give 80 %, 120 83 %, 150 95 %; 59 draws that all
succeed bound a failure rate at 4.95 %, under 2 % takes 149 and under 1 % 299. The power, summed, agrees
with 4000 random draws within 2.5 points. The comparisons the records reported, read again:

| ADR | Compared | Pairs | p | Power for what it saw |
| --- | --- | --- | --- | --- |
| 0036 | the cube moved after the look: 9 of 9 held, 0 of 9 | 8 drawn, all broken | 0.0078 | shown |
| 0041 | cube pressed into the table: 4 of 59, then 0 | 59 | 0.125 | 21 %: underpowered; 116 needed |
| 0042 | set down gently: 68 of 71 without the squeeze, 71 with | 71 | 0.25 | 8 %: underpowered; 186 needed |
| 0051 | looking again against each baseline: 9 rescued, none lost | 9 | 0.0039 | shown |
| 0053 | a bus 0.5 s late: commands, or readings, broke 2 of 9 | 9 | 0.5 | a count, not a difference: under 1 % |

Held by `tests/test_power.py` (4). Suites on MuJoCo 3.10.0: 1129 passed with a display, 1070 headless.

**Boundaries.** The plan line is not yet written into the seed ledger by the sweep command, nor does a
sweep refuse to run underpowered; the effect worth seeing is the owner's or an agent's choice, not
computed. The records' conclusions stand as written: each said what its counts were.
