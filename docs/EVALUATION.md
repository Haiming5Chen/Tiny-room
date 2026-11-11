# An evaluation of Little World - 11 November 2026

The owner asked that people be able to take this project from GitHub, use it, re-analyse it and
see where it went wrong. This is that look, taken before anyone is asked to trust it.

It was written by Claude, the AI agent that wrote most of the code and most of the records it
judges, which is the first thing to hold against it. To lean on memory as little as possible,
everything in the first table was measured again for this page; the rest is read from the
repository's own records and says where.

## What was measured again

| Looked at | How | Found |
| --- | --- | --- |
| What GitHub has | `git ls-remote` of the public repository, 10 Nov | one branch, `main`, at the import of 24 Sep; no pull request, no release. The working branch was 89 commits ahead and had never been pushed |
| A stranger's install | a clean clone into a new environment, `pip install '.[workshop]'`, the window opened from an empty folder | works: 26 s to install, the package's data complete |
| Both test suites | every test, with and without the window | 1179 passed with a display, 1112 headless |
| The headline numbers | `little-world evidence`: 12 claims, 31 measurements, against their records | all 31 hold on the machine they were recorded on, in 3.5 min |
| Whether a run repeats | the same run twice, compared step by step; and the same 71 Fetch set-ups run a week apart (ADR 0070, ADR 0071) | identical to the last bit; the 71 delivery times agree to the millisecond |
| Another processor's arithmetic | the same machine with NumPy's AVX-512 paths switched off and OpenBLAS's Haswell kernels (`NPY_DISABLE_CPU_FEATURES`, `OPENBLAS_CORETYPE`), as on a processor without AVX-512, on a clean clone | 29 of 31 measurements identical to the last digit; the Fetch's cube is in the bin 4 ms earlier, the cell's furthest part moves in its twelfth digit; the quick tier and the 64 slow tests pass |
| Another machine | the owner's Intel Mac, same MuJoCo (Codex's runs of 2-4 Nov) | one of the project's own tests fails: the kit cart stalls for good at an 18 mm curb that it clears on Linux after 11.6 s |
| A newer engine | the suite without a window on MuJoCo 4.0.0 (the pin is 3.10.0) | 20 of 1,087 tests fail: 13 in the robot importer (one cause), 7 physics results move. Its engine has no wheel for an Intel Mac either: the pin stays |
| Another friction model | the same suite with MuJoCo's elliptic friction cones | 16 of 1,087 fail |
| How long the tests take | every test timed | 37.2 min of test time; 64 tests take 35.9 of them |
| The documents' links | every relative link in 158 Markdown pages | none broken |
| Personal data in a public repository | a search of every tracked file for home folders, addresses, keys | none |
| Lint | `ruff check --select F` | 10 findings: unused imports and names |
| The standard-library-only rule | third-party imports in `core/` and `construction/` | none: the rule holds |
| "The only MuJoCo adapter" | which files import MuJoCo or read its model and data | 23 of 158 files import it; 25 outside `physics/` read the engine's own structures |

## What holds

- **It runs, and it repeats.** A clean clone installs in half a minute and opens its window.
  Both suites pass. On one machine and one MuJoCo release a run is the same run every time, so
  two runs can be compared step by step and a difference between them means something.
- **Its claims can be checked.** Each change has a decision record with the number it was
  measured by, a test that holds the number and a paragraph of what it does not claim; there
  are 73 of them. Two record a thing that was built, measured and not adopted (ADR 0054, 0070),
  and two more say which half of their work was left out (ADR 0056, 0066). Twelve headline
  numbers can now be measured again with one command.
- **The design format is what it says.** The core that holds a design imports nothing but the
  standard library; a design is data, read and written without a simulator.
- **It says what it has not done.** What is unfinished is listed with who found it
  (`docs/agents/OPEN.md`); a flaw - the slope creep, below - is in the evidence list as a flaw.

That is a narrower list than the README's old 58 paragraphs suggested. The rest of this page is
why.

## Where it went wrong

Ordered by what it cost.

### 1. Seven weeks of work never left one folder

The repository on GitHub is the import of 24 Sep: 9 decision records, 163 tests. Everything
since - 89 commits, 62 more records, 454 more tests - was "shipped" 57 times as a bundle into a
build folder on the owner's Mac, each time to wait for a double-click on a publish script. The
script's log has one entry, 24 Sep. The Mac's own app ran a copy two weeks behind (the owner,
26 Oct: "over the past 2 weeks, no updates that i can see from the app"), and the launcher made
on 3 Nov to show the newest work was never opened.

The cause was mine. I could not push, so I built a hand-off with two manual steps at the end,
and then reported "shipped" for seven weeks without once checking that the last step had
happened - the log was one file read away. A delivery nobody received is not a delivery. From
here on the report says what GitHub has, as `git ls-remote` shows it, not what was put in a
folder.

*Now:* `build/publish.sh` on the Mac publishes in one step, forward only, after showing what it
will push. It still needs the owner: nothing here can push.

### 2. Written for its own record, not for a reader

The README was 1,158 lines, with the install line at line 367 after 58 paragraphs of features.
The pull request text is 89 KB. Reports named work by its record number (the owner, 26 Oct:
"the name of tasks are pretty confusing"). Every paragraph was true and each was added to prove
a change was documented; nobody was asked whether it could be read.

*Now:* the README is 114 lines, and a test keeps it short; the long lists are in
`docs/FEATURES.md` and `docs/MANUAL.md`. The pull request text is still what it was.

### 3. Nothing here has touched hardware

Every number is a simulation's. The gearmotor and the servos are datasheet lines; the kit's
servos are *read as* ROBOTIS XH430s, an assumption stated in ADR 0048 and used ever since; the
camera's noise is the depth error from a datasheet formula; the proposal to calibrate one real
servo on a bench (FR-010) has waited since the start of October. The numbers are precise - "36.87 s",
"0.21 s after the jaw met it" - and precision is repeatability, not accuracy. Nothing here
says how far any of them is from a real machine, and the project has added 60 records of
behaviour on top of parameters it never checked.

### 4. Tuned and judged on the same draws

Until 22 Oct every sweep drew its set-ups with seed 1: every decision from ADR 0024 to ADR 0048
was shaped on those draws and then judged on them (the seed ledger says so itself). Held-out
draws exist since ADR 0049 and there have been three held-out sweeps - one for ADR 0041, 0042
and 0048 together, one each for ADR 0070 and 0071. The "71 of 71" results before that are
fits, not tests.

### 5. A decision made on a symptom

In October the cart pressed the cube into the table in heavy set-ups; the cart rocked on its
casters; ADR 0041 set the casters on the floor ("on all four"), which stopped the rocking and
cost the cart its curbs. A week later ADR 0042 changed where the jaws grasp, and with that
change the rocking cart presses nothing either (OPEN LW-035; Codex's 40 paired runs on the Mac
agree). The decision may still be right - the cart pitches 4 degrees without it - but the harm
it was made for had another cause, and its price was first reported wrongly (below) and is
still being paid: the grounded cart crosses a curb only by slewing onto one wheel, 10.4 s
against 3.8, and that manoeuvre is the one that does not survive a change of machine (7).

### 6. Claims that were reported and then corrected

- *"Climbs no curb, not even 10 mm"* (13 Oct, to the owner): wrong. It was read from checks that
  stopped at 7 s; given 25 s the cart clears 10, 14 and 18 mm. Corrected the next day.
- *The factory cell* ran from the first import with an arm that sagged 6 to 7 mm under its own
  weight and a hand that squeezed 1.6 N where the real one squeezes 70: it "placed parts" 2 to 6
  mm from their slots, and for a month nothing measured where they landed. ADR 0056 measured it
  (26 Oct); ADR 0065 mended it (3 Nov).
- *"The program holds the cube"* was read from the simulator's contacts - which no robot has -
  until ADR 0048 read the servos instead.
- *A test count* reported to the owner as 972 was 979; "ten test fields" in the README was
  eleven; `AGENTS.md` said the suite takes "about seven minutes" when it took 37.
- *The radar's search* was held by a test at 15 of 20 questions; the count moved to 14 and then
  16 while one decision record was being reworded (OPEN LW-043). A test that fails on a
  document's wording was measuring the wrong thing.
- *This page's own first draft* (10 Nov) said MuJoCo 4.0.0 has an Intel Mac wheel again and
  that the pin's reason was gone. `pip download mujoco==4.0.0` for an Intel Mac succeeds
  because that wheel is a wrapper for any platform; the engine, `mujoco-core`, has none. The
  weekly reading of 9 Nov had checked exactly this and had not been read first. Corrected on
  11 Nov, before anything was published.

Each was found by the project's own checks, which is the system working. Each was also
believed first.

### 7. One machine, one release

Every recorded number comes from one cloud Linux machine. On the owner's Intel Mac, with the
same MuJoCo, the kit cart stalls at the 18 mm curb it clears here, and a test fails (OPEN
LW-026): an outcome that hangs on a wheel slewing round a corner flips with the processor's
arithmetic. ADR 0043 checks the Fetch for such knife edges; nothing checked the curb, and
nothing ran anywhere else to find out. The windows of Apple silicon and Windows have never
been opened. How little it takes was measured for this page: on the same machine, with NumPy
told not to use the processor's AVX-512 instructions, the Fetch sets its cube down 4 ms earlier.
Every test still passes there; the curb on the Mac shows what happens when one does not.

MuJoCo is pinned at 3.10.0 because it is the last release with a wheel for the owner's Intel
Mac. 3.11 to 3.17 have none, and neither has 4.0.0 (6 Nov): its `mujoco` wheel installs anywhere
and is a wrapper around `mujoco-core`, which has no macOS x86_64 wheel. The pin stays while that
Mac is the machine. What leaving it would take was measured on Linux: on 4.0.0, 20 of 1,087
tests fail: the importer breaks in one place (13 tests), the tilt table tips the arm cart
at 51.5 degrees where it tips at 54.6 here, the coast-down is 2 % off its closed form, the curb
flips. A contained study, not a rewrite, for the day the machine changes - and until then the
proposals that wait on a newer engine (a PID servo, moving surfaces, the reworked DC motor)
keep waiting.

### 8. Physics limits found late, and still there

- *Friction creeps.* A block resting on a slope inside its friction angle slides 0.2 to 4 mm/s
  (OPEN LW-039), because MuJoCo's default pyramidal friction cones let a resting contact creep
  and more `noslip` iterations do not stop it. It was found on 2 Nov, in the sixth week, by
  the first measurement that looked at a part at rest. Elliptic cones stop it, and with them 16
  tests fail: a held cube slides 7.6 mm out of the jaws in 10 s and the cell's hand no longer
  squares its parts. Every grip and every friction number here is a result *of* the cone
  model.
- *One contact point per pair of shapes* (ADR 0027, to pass on 3.10): a wheel touches the floor
  at a point, a box across cylinders sinks into them (so the conveyor's rollers are capsules).
- *The kit's rotary jaws* pull what they close on 11 mm towards the palm (OPEN LW-028) and
  cannot hold a cube lying across them (OPEN LW-034): the Fetch works for a cube standing up.
- *Contacts are soft* in proportion to the mass behind them: "a 2 mm wheel lift" is not a tip,
  and a force under 0.1 N is noise.

### 9. A test suite that grew past use

The suite took "about seven minutes" when `AGENTS.md` last said how long; its 1,093 tests now
take 37, 64 of them 35.9. There was no quick tier, so the honest check before a small change was half an hour, and nothing ran on
GitHub at all. Some tests assert outcomes that sit on a knife edge (the curb), and one asserted
a property of the documents (the radar).

*Now:* a quick tier of about 1,000 tests in a minute, two workflows. The slow 64 are still slow:
most run the whole Fetch to assert one number.

### 10. Wide before deep

64 decision records in the 48 days since the import: a builder, eleven fields, block programs, a camera, sweeps,
disturbances, a factory cell, a conveyor, a URDF importer, lessons, a research radar. After the
first weeks, what was built next was chosen from a weekly reading of new papers, ranked by the
agent - not from anyone using the thing. Nobody but the agents has been seen to use any of it:
the first-hour lessons (ADR 0046) have not been tried by a person; What's new had outgrown the
window it opens in - its text ran under the button below it - and that was found on 6 Nov, by
looking at a screenshot.

### 11. The way of working

One long branch and bundles instead of small pushes (1). Two agents with two checkouts and a
shared log: Codex merged the bundle into its own copy on 23 Oct and that merge was never pushed
either, so there are now three lines of the project - GitHub's, the Mac's and the cloud's. The
cloud workspace was lost once (13 Oct) and restarted many times; the work survived only
because the bundles existed. The process was safe against losing work and blind to whether
the work arrived.

### 12. The code

Four files are over 800 lines, the longest 1,214. A sweep's one run takes a tuple of 19 positional fields.
`programming/program.py` is written without spaces and several statements to a line. The
engine's model and data are read directly in 25 files outside the adapter, so "a second
engine's opinion" (FR-013) would mean rewriting control, perception and the sweeps. There are
no type checks, and 10 unused names.

### 13. People may read it and may not use it

No licence has been chosen; all rights are reserved. A project that asks to be taken from GitHub
and used has to say that it may be.

## What to do next

1. **Publish** - `sh ~/Tiny-room/build/publish.sh` on the Mac. Until then nothing above reaches
   anyone.
2. **Choose a licence.** The owner's decision; the first question a user will ask.
3. **Run `little-world evidence` on the Mac**, and on Apple silicon and Windows when someone
   has one. It takes four minutes and turns (7) from a worry into a table.
4. **One hardware check before another feature**: one servo, one bench, one number set against
   the model (FR-010). Without it, (3) is the answer to "is it right?".
5. **Decide the machine before the engine.** MuJoCo 4 has no wheel for an Intel Mac, so the pin
   stays while the owner's Mac is the machine. On Apple silicon or Linux a move to 4 is a contained
   study: mend the importer's one break, list what the other 7 tests show, decide the friction
   cones in the same pass, re-record the evidence.
6. **Have one person do the first hour** while someone watches, before more is built.
7. **Bring the three lines together**: Codex's merge and its caster evaluation belong in the
   same history as this.
8. **Stop asserting knife edges.** A test of a chaotic manoeuvre should check a range, or be an
   evidence claim that is expected to move.

## What this page does not do

It evaluates the project against its own claims. It does not compare it with other simulators
or teaching tools, measure whether anyone learns anything from it, or review the code line by
line. The numbers in the first table are one machine's, like all the others.
