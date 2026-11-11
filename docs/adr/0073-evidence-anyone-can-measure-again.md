# Evidence anyone can measure again: the headline numbers re-run, a quick tier, the workflows

**Problem.** The owner asked (10 Nov) that people be able to re-analyse and evaluate this project
and see where it went wrong. What stood in their way, measured:
- *Every number comes from one machine.* The documents' numbers were all measured on one cloud
  Linux machine. On the owner's Intel Mac, with the same MuJoCo, one of the project's own tests
  fails: the kit cart stalls for good at an 18 mm curb that it clears here after 11.6 s (OPEN
  LW-026, Codex's measurements of 3 Nov). The tests say pass or fail inside tolerances; nothing
  shows a reader the numbers on their own machine beside the ones written down.
- *The suite is too slow to be a first check.* Timed test by test (JUnit): 1,093 tests without a
  window take 37.2 minutes of test time - about 25 on two cores - and 64 of them, the ones that
  run the whole Fetch or the cell, take 35.9 of those minutes; the other 1,029 take 1.3.
  `AGENTS.md` still said "about seven minutes".
- *Nothing runs on GitHub.* No workflow: a visitor cannot see whether the tests pass, and a
  pushed change is checked by nobody.
- *The documents' links were unchecked* - 150 pages; none was broken, by luck.

**Does an existing simulator solve it? Can we wrap it?** MuJoCo repeats a run exactly on one
machine and build and makes no promise across them; its own documents say results change
between releases (ADR 0027). pytest has markers and JUnit output; GitHub has Actions. All
used as they are.

**Unique contribution.**
- *The evidence, re-run* (`little_world/evidence.py`, `little-world evidence`): a registry of
  twelve headline claims - the sprint, a curb, the tilt table with and without the arm, the
  doorway, the arm lab's pick and place, the Fetch, the Fetch with its cube moved under a jaw,
  the conveyor, the factory cell, a run repeated bit for bit, and one flaw kept in the list on
  purpose, the creep of a block resting on a slope (OPEN LW-039). Each names its decision
  record and the test that holds it, and carries the numbers recorded for it with the tolerance
  inside which a re-run still holds. The command measures each again where it is run and prints
  it beside its record - "holds", or "DIFFERS" - and `--json` writes what was measured, to
  attach to a report (an issue template on GitHub asks for that file). `docs/EVIDENCE.md` is written from the registry and a test keeps the two
  the same.
- *A quick tier* (`tests/slow.txt`, `tests/conftest.py`, `scripts/test_times.py`): the tests that
  took 2 s or more are listed with what they took, from a timed run; they and every window test
  are marked `slow`, so `pytest -m "not slow"` is the quick tier. With no `-m`, everything runs,
  as before: commits are still judged by both whole suites.
- *Workflows* (`.github/workflows/`): `quick` on every push and pull request - install as the
  README says, the doctor, the quick tier and the five quick measurements, on Linux (required)
  and on macOS and Windows (reported, not required: untried); `full` on pushes to main, weekly
  and on request - the whole suite in two halves, the window tests on a virtual display
  (reported), and all twelve measurements with their file kept.
- *Links checked* (`scripts/check_links.py`, a test): every relative link and image in the
  repository's Markdown leads to a file.
- *An evaluation* (`docs/EVALUATION.md`): what was re-measured for it, what holds, and where the
  project went wrong, with the evidence for each.

**Blueprint and builder.** Untouched.

**Result.** On the machine the numbers were recorded on, `little-world evidence` measures 31
quantities for the twelve claims in 3.5 minutes and all hold - the Fetch's cube in the bin at
36.87 s, the tilt table's 54.61 deg against a predicted 55.58, the slope's creep 0.21 and 1.36
mm/s; `--quick` measures 10 in 33 s. The quick tier: 1,048 tests in 76 s. The same 71
Fetch set-ups run a week apart for ADR 0070 and ADR 0071 agreed to the millisecond.

Held by `tests/test_evidence.py` (9): every claim names a record and a test that exist; a number
holds within its tolerance and a word only when it is the same; a check prints each number beside
its record, and a claim that cannot be measured does not hold; the evidence page is what the
registry writes; the command lists, refuses, measures two claims and writes its file; the slow
list names tests that exist; what it lists, and every window test, is marked slow; every link
leads to a file; the README is short. Suites on MuJoCo 3.10.0: 1179 passed with a display, 1112 headless.

**Boundaries.** The records are one machine's: a difference elsewhere says the result is not
portable, not which machine is right. The tolerances are judgment - wide enough for a run that
ends the same way a little later, not derived. Twelve claims of several hundred: the tests hold
the rest. The workflows have never run - they were written without access to GitHub's runners,
and the macOS, Windows and window jobs are marked as reported for that reason. The slow list is
a measurement that goes stale: a new slow test is in the quick tier until
`scripts/test_times.py --write` is run again on a timed run.
