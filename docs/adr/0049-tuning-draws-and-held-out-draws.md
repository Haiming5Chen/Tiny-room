# Tuning draws and held-out draws: a decision is certified on set-ups it was not shaped on

**Problem.** Every sweep since ADR 0024 drew its set-ups with seed 1, and the decisions of
October were shaped on those draws and then certified on the same ones: ADR 0042's squeeze was
added after drawn repeat 44 crept out of the jaws, ADR 0041 was judged on the 59 draws where its
four presses had been found, and nothing recorded which seed a sweep used. A design tuned on its
own test set looks better than it is: a study of a frozen robot policy saw fewer near-collisions
in its first cohort and not in an independent replication ([arXiv 2610.24573](https://arxiv.org/abs/2610.24573);
the weekly reading of 21 October, FR-027).

**Does an existing simulator solve it? Can we wrap it?** No simulator keeps a project's
discipline about which draws its decisions have seen. Holding out a test set is ordinary
practice; here it is a ledger and a refusal in the sweep's own command line, and a report.

**Unique contribution.**
- *Every sweep records its seed* (`inventory/sweep.py`): varied and disturbed sweeps keep the
  seed their set-ups were drawn with, write it to their JSON and say it in their report.
- *A ledger of seeds* (`docs/sweeps/seeds.jsonl`, read and written by `inventory/holdout.py`):
  which seed drew which field's set-ups, for which decisions, tuning or held out. Its first entry
  is seed 1 for every field, the tuning draws of ADR 0024 to ADR 0048.
- *A held-out sweep* (`sweep FIELD --holdout "ADR nnnn" --seed N`): refused unless the ledger has
  not seen seed N for the field, and entered in the ledger before it runs, so its draws are never
  mistaken for fresh ones again. A decision changed after seeing its held-out result needs a new
  seed.
- *Read beside its tuning sweep* (`python -m little_world.inventory.holdout TUNING.json
  HELD_OUT.json`): each goal's rate with its two-sided 95 % Clopper-Pearson interval (ADR 0028),
  each handling measure's median and range (ADR 0040), and every held-out value outside its
  tuning range named - reported as found, not tuned away.

**Blueprint and builder.** Untouched.

**Result.** The ledger's first entry is seed 1 for every field: the tuning draws of ADR 0024 to
ADR 0048. The held-out draws are seed 20261022, entered for the Fetch field before its sweep ran
and written here before it was read. On the design as of ADR 0048, its 59 drawn set-ups beside
the 59 of seed 1 (`docs/sweeps/2026-10-22-fetch-held-out-59.md`):
- every goal met in 59 of 59 held out, as tuned - each rate 94 to 100 % (two-sided 95 %), so at
  least 95 % of set-ups drawn this way meet every goal (one-sided); the 12 chosen set-ups, the same
  in both, met every goal too, and the program felt each of its 71 grasps as the contacts showed;
- ADR 0041 holds: no presses - the table's push on the cube over 50 ms 0.17 to 0.23 N held out,
  as tuned;
- ADR 0042 holds: the fall into the bin 0.2 to 0.9 cm (tuned 0.1 to 1.1), the squeeze over 50 ms
  3.71 N (3.22 to 4.97; tuned 3.66, 3.22 to 5.00), the bin's push over 50 ms 0.24 to 0.30 N (0.23
  to 0.30);
- outside the tuning range, as found: the table's push in a single step reached 0.77 N in held-out
  repeat 19, carrying 0.49 kg, against the tuning's most of 0.62 N - over 50 ms it was 0.18 N, the
  cube's weight: a knock lasting a step, not a press. The bin's least push in a step, 0.44 N, and
  the cube's least lean over the bin, 26.0 degrees, fell just under the tuning's 0.45 N and 26.2.
Nothing was changed after these were seen.

Held by `tests/test_holdout.py` (5): a sweep's seed in its JSON and report; the ledger's seed 1
for every field; a held-out seed reserved once, refused again, another field's own; the command
line refusing seen draws, a missing seed and a missing ledger before anything runs; a held-out
sweep read beside its tuning sweep, a squeeze above the tuning's range named. Suites on MuJoCo
3.10.0: 1049 passed with a display, 997 headless.

**Boundaries.** The ledger is kept by hand in the repository and trusts that sweeps outside it
used seed 1 - the scratch scripts of October did. One held-out draw of 59 set-ups bounds a failure
rate to about 5 % (59 successes), not lower. The fixed set-ups - the design as designed and each
range's ends - are the same in every sweep and are not held out; only the drawn ones are.
