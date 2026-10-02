# Little World: notes for agents

The owner decides what is worked on and where the project goes. Agents report to the
owner; none of them directs or overrides another. This file holds the project's rules and
the facts needed to work here (Codex reads `AGENTS.md`; Claude Code reads `CLAUDE.md`,
which imports it).

What agents have done and left open:

- `docs/agents/REPORTS.md` - each agent's report, newest first: what it did, what it
  measured, what is unfinished.
- `docs/agents/OPEN.md` - unfinished work and problems found but not fixed, with who
  found them and when.
- `docs/agents/STATE.md` - the branch, the tests and what is uncommitted.
- `docs/agents/FRONTIER.md` - what papers, journals and releases offer that could change
  the project, filed by the radar, and agents' proposals for it, each waiting for the
  owner to accept or decline it (ADR 0026).

`python scripts/agent_status.py` prints the branch, the tree, the open items, the
proposals that wait on the owner and the newest report.

## Working alongside other agents

- Take your tasks from the owner.
- Report when you stop, even mid-task: a new entry at the top of `docs/agents/REPORTS.md`
  with what you did (commits), what you measured, and what is unfinished or doubtful.
  Write it for the owner; do not write instructions for other agents.
- Leave other agents' work as it is. If you think something in it is wrong, put it in your
  report with the evidence; whether to change it is the owner's call.
- Add what you leave unfinished, or found and did not fix, to `docs/agents/OPEN.md`. Mark
  an item done only when you finished it.
- Ideas from outside - a paper, a journal article, a release - go into
  `docs/agents/FRONTIER.md` as proposals (`### FR-nnn · title` and its six fields), not
  into the code. Read the file before proposing anything; only the owner accepts or
  declines a proposal, and agents work on accepted ones only. To disagree with another
  agent's proposal, add a dated `- Note` under it instead of changing it.
- The owner publishes the branch to GitHub.

## Rules

Read docs/VISION.md and docs/ARCHITECTURE.md before architectural changes.
Core must remain standard-library-only and independent of MuJoCo and UI.
Objects and robots share Entity/Blueprint. All construction emits versioned,
serializable Blueprint data. No task assumptions in Scene or native handles in core.
Keep geometry, materials, design, runtime state, controllers and solvers separate.
Unsupported behavior must fail explicitly; do not imply future physics exists.
Preserve build → simulate → reset → redesign and immutable saved designs.

Before a new system, document: Does an existing simulator solve it? Can we wrap it?
Is it our unique contribution? Does it preserve Blueprint construction, decoupled
UI/world/backend, and the future builder? Reuse solvers and license-tracked assets.

Add contract tests before significant new behavior, then relevant integration
checks. Run `python -m pytest`; no graphics required for the default suite. Camera
and viewer checks are explicit. Do not implement thermal, fluids, chemistry, AI,
or a graphical builder in milestone one. Do not add dependencies for future phases.

## Set up and check

```sh
python3 -m venv .venv && .venv/bin/python -m pip install -e '.[workshop,dev]'
.venv/bin/python -m pytest -q                         # headless suite, no display needed
LITTLE_WORLD_TEST_RENDER=1 xvfb-run -a -s "-screen 0 1600x1000x24" \
    .venv/bin/python -m pytest -q                     # adds the OpenGL window tests (Linux)
.venv/bin/python examples/workshop.py                 # the app, in Anime (builder) mode
python scripts/agent_status.py                        # branch, tree, open items, proposals, last report
.venv/bin/python -m little_world.radar brief          # the radar's section of docs/agents/FRONTIER.md
ruff check --select F src tests scripts               # optional; not a project dependency
```

MuJoCo is pinned to 3.10.0 (`pyproject.toml`, ADR 0027): the newest release with wheels
for the owner's Intel Mac. The adapter turns multiccd off (one contact per convex pair);
a different release moves physics results (docs/RADAR.md). The headless suite takes about
seven minutes on two cores.

## Conventions

- A change in behaviour has a decision record, `docs/adr/NNNN-short-title.md`, numbered
  after the last, with these parts: *Problem* (measured) · *Does an existing simulator
  solve it? Can we wrap it?* · *Unique contribution* · *Blueprint and builder* · *Result*
  (numbers, and the tests that hold them) · *Boundaries* (what is not claimed).
- A physical claim has a number, a reason and a test that holds it.
- Documents that follow a change: a `README.md` bullet for what users see, a dated section
  in `docs/VALIDATION.md` (what is checked, test counts, what is not claimed),
  `docs/ARCHITECTURE.md` for a new module, the `docs/ROADMAP.md` paragraph.
- Commits: one decision each; subject `Topic: what changed`; the body says what was measured
  before and after. Both suites pass at every commit.

## Map

| Where | What |
| --- | --- |
| `src/little_world/core/` | Blueprint, components, commands, state: standard library only |
| `src/little_world/construction/` | assembly, docking, structure and stance (standard library) |
| `src/little_world/physics/mujoco_backend.py` | the only MuJoCo adapter: compiles Blueprints, steps, applies commands |
| `src/little_world/control/` | drive and arm controllers, navigation, tool motion, telemetry |
| `src/little_world/fields/` | test fields and their goals (goals read the core `State` only) |
| `src/little_world/programming/` | block programs and the runner |
| `src/little_world/factory/` | the automated factory cell |
| `src/little_world/ui/` | the one-window app: workshop, build, program, test drive, factory |
| `src/little_world/radar/` | the frontier radar (ADR 0021); reads documents, never designs |
| `tests/` | one file per area; window tests run only with `LITTLE_WORLD_TEST_RENDER=1` |
| `docs/adr/` | the decision records, 0001 onwards |

## Things that have bitten before

- MuJoCo's soft contacts creep: two noslip iterations keep a held part still (ADR 0017).
- Servo damping is integrated by the solver through a `Torque` slope, not applied a step
  late (ADR 0014); a controller that returns a plain float loses that.
- MuJoCo does not filter contacts between a child and a parent welded to the world: moving
  field parts must clear their stands (ADR 0020).
- Window tests must wait on simulated progress, never on the wall clock.
- The repository is public: no personal data, keys or paths in code, docs or reports;
  third-party assets are listed with their licences in `THIRD_PARTY.md`.
