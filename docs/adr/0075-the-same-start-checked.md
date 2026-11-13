# The same start, checked: a fingerprint of every run's set-up before a paired statistic

**Problem.** The project's strongest results are paired: a disturbance against no disturbance
(ADR 0036), the program's recovery against its baselines (ADR 0051), the jaws closed by current
against their ramp (ADR 0070), each read set-up by set-up with an exact McNemar test. Every one of
them assumes that set-up i began from the same start in both arms, and the pairs were matched by
their draws' labels - "repeat 12". A label names a draw, not a start: a scratch driver once drew the
same labels with the payload placed where its own mass put it rather than at the sweep's shared site
(`site=None`, ADR 0052), and nothing would have said that its pairs were not pairs. A study of paired
robot evaluations found the same: the same episode index need not mean the same start, under some
resets, and it asks that the starts be checked before any paired statistic ([arXiv
2611.00896](https://arxiv.org/abs/2611.00896); FR-041, second in the weekly reading of 9 November).

**Does an existing simulator solve it? Can we wrap it?** MuJoCo saves a compiled model to bytes
(`mj_saveModel`) and holds every joint's position and speed (`qpos`, `qvel`); it does not say whether
two runs began alike. The fingerprint is built from those.

**Unique contribution.**
- *A fingerprint of the set-up* (`inventory/identity.py`, standard library), taken as the program
  takes over - after the field's settling and the camera's placing; at once for a field without a
  program. Six parts, each a digest: the MuJoCo release; the compiled model with every change made to
  it since (a varied friction, a heavier body, a moved camera); every joint's position and speed before
  the first step, and as the program takes over; the program's blocks; the draw's own values. The
  physical parts come in two grades: *exact*, the bytes, and *rounded* - the model's numbers to six
  significant figures, taken to twelve first and rounded from there in whole numbers so that a value
  on a half (81/64 of a unit, from a part's sizes) goes one way whatever its last bits; the joints to a
  micrometre, or microradian, and a micrometre a second. `MujocoBackend.digests` computes them.
- *Every sweep run keeps one* (`Run.fingerprint`, in its JSON); `sweep.run(until_start=True)` returns
  it alone, without running - how a paired study's starts are checked again.
- *Checked before the statistic*: `identity.check(pairs, grade, factor)` - a comparison names what it
  tests, and every other part must be the same. The disturbed sweep's report and the recovery report
  say it in a sentence ("Set-ups verified: 63 of 63 pairs began from the same start, exact."), and
  name any pair that did not and what differed, to be read as two runs.

**Blueprint and builder.** Untouched: the fingerprint reads the compiled model and the state.

**Result.**

The paired studies' starts, checked again (each set-up rebuilt with `until_start`):

| Study | Pairs | The same start, exact | Named as the factor |
| --- | --- | --- | --- |
| ADR 0036 and 0051: the Fetch's 9 set-ups, undisturbed against each of its 7 disturbances | 63 | 63 | - |
| ADR 0070: its 71 tuning set-ups and 59 held-out draws, the ramp against 7 N by current | 130 | 130 (130 rounded) | the program |
| ADR 0052's slip reproduced: the 71 tuning set-ups, the shared site against `site=None` | 71 | 12 | - |

The slip is caught where it can be: the 59 pairs it flags are every loaded set-up but the 3 at the
heaviest payload, whose own site is the shared one; the other 9 carry nothing. What differs in each:
the model and the settled start. A disturbance comes after the start, and a recovery is a runner's
setting, not the set-up's: neither shows. ADR 0070's arms differ in their programs only.

The 9 set-ups' fingerprints on the same machine with NumPy's AVX-512 paths switched off and
OpenBLAS's Haswell kernels (as OPEN LW-045 measured): the same to the bit, exact - so the 4 ms the
Fetch's delivery moves there arise in the run, not in its start.

A fingerprint takes 15 to 23 ms - most of it the model's 6 MB of meshes - in a Fetch run of about 47 s.
Held by `tests/test_identity.py` (3: the checker's words, the backend's digests of a part made 1e-12
and 1 % heavier, the slip flagged and a disturbance and a squeeze not). Suites: 1195 pass with a display, 1127 headless.

**Boundaries.** A fingerprint says that two runs began alike, not that they ran alike - a run can
still part from its pair later (LW-045's 4 ms). The rounded grade is an aid across machines, not a
proof: a number on a rounding line on one machine and off it on another still differs. Runs recorded
before this carry no fingerprint, and their reports say so; the window's test drives are not
fingerprinted. Nothing here was run on the owner's Mac: whether its starts match these is one
command there (OPEN LW-050).
