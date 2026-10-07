# Paired runs: what a disturbance did, set-up by set-up

**Problem.** A disturbance sweep (ADR 0030) runs the same set-ups undisturbed and under each
disturbance and reports two rates: "9 of 9" undisturbed, "0 of 9" with the cube moved 5 cm
after the look (before ADR 0033). Two separate rates leave out what makes the comparison
strong: each disturbed run has a twin, the same drawn set-up run without the event. Nothing
showed that the twins really are the same run until the event, and nothing said how sure a
difference made us - the bound on each rate alone (ADR 0028) says the undisturbed program
succeeds at least 69 % of the time from eight draws and the disturbed one at most 31 %, which
undersells what nine set-ups that all flipped show (FR-017).

**Does an existing simulator solve it? Can we wrap it?** The method is old and standard:
matched pairs and McNemar's exact test (McNemar 1947), used for robot policies by LIBERO-MAX
(arXiv 2609.36518, 5 October reading), whose base and disturbed runs share every action
before the event. MuJoCo is deterministic on one machine, so the pairing is exact rather
than statistical; the test is a binomial sum, `math.comb`. Wrapped: the disturbance sweep.

**Unique contribution.**
- *One run until the event, shown.* `sweep.run` can record, step by step, a digest of every
  joint's position and speed (`trace`), and keeps when the disturbance began (`Run.event`).
  A set-up's two runs are equal bit for bit up to the event and differ from it on - on the
  Sprint field (a shove) and on the Fetch field (the cube moved 2 s after the look).
- *The pairs, counted.* For each disturbance, of the drawn set-ups that met every goal
  undisturbed, how many the event broke, with the share it can break at most (95 %, the
  Clopper-Pearson bound of ADR 0028); how many failures it turned into successes; and the
  exact McNemar p on the set-ups whose outcomes differ (`confidence.mcnemar`). The as-designed
  set-up is chosen, not drawn, and stays out of the count, as in ADR 0028. A "Broken by it"
  column in the report; the run report's panel says "broke k of n".
- `sweep --disturb --only LABEL` runs one of a field's disturbances, so a pair can be drawn
  59 times without the others.

**Blueprint and builder.** Untouched.

**Result.**

Without looking again (`--regrasps 0`, ADR 0033 off), "cube moved 5 cm sideways, 2 s later"
on the nine set-ups of ADR 0030 broke 8 of the 8 drawn set-ups that succeeded undisturbed - at
least 69 % of successes - and rescued none: exact McNemar p = 0.0078, where the two rates alone
said 8 of 8 against 0 of 8
([report](../sweeps/2026-10-07-fetch-moved-later-paired-without-looking-again.md)). FR-017
expected nine pairs and p = 0.0039; the as-designed set-up is chosen, not drawn, so eight
count. With looking again, the same disturbance on 59 drawn set-ups broke 1 of 59 (0 to 9 %)
and rescued none, p = 1: no effect shown; the cube reached the bin 3.1 s later (median), and
the rates alone read 59 of 59 against 58 of 59
([report](../sweeps/2026-10-07-fetch-moved-later-paired-59.md)). The broken pair, traced
(repeat 9): the cube moved 26 ms after the picture before the jaws went down, a jaw came down
on it and the reach was stopped; rising to its ready pose to look again, the arm dragged the
cube 3 cm towards the cart, over the table's edge, and the next look found nothing (OPEN LW-023).
Undisturbed, two of the 60 looked again though nothing had moved (OPEN LW-022). Bit for bit:
on the Sprint field the first step that differs is the one after the shove began; on the Fetch
field, the step the cube was moved.

Held by `tests/test_paired_runs.py` (6): the exact test's values (nine broken and none
rescued: 0.0039; eight: 0.0078; ten and two: 0.0386; no discordant pair: 1); the pairing over
made-up runs, the as-designed set-up left out; a disturbance that breaks nothing bounded; a
rescue counted the other way; the two runs of a pair equal step for step until the event, on
the Sprint and the Fetch fields.

**Boundaries.** A pair is exact on one machine and one MuJoCo build; across machines the two
runs of a pair may part before the event by rounding (ADR 0027's pin keeps the build the
same). The test says whether the event changed outcomes, not by how much a time changed (the
median change stays as it was). A set-up counts once whatever happened in it; an event that
broke a run in a way the goals do not see is not counted.
