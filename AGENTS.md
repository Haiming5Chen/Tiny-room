# Little World: guide for agents

This file is read first by any agent working here (Codex reads `AGENTS.md`; Claude Code
reads `CLAUDE.md`, which imports this file). Then read, in order:

1. `docs/agents/STATE.md` - where the work stands: branch, tests, what is in flight.
2. The newest entry of `docs/agents/LOG.md` - what the last agent did and left open.
3. `docs/agents/BACKLOG.md` - the tasks, who holds them, and when each is done.

`python scripts/agent_status.py` prints the live version of all three: branch, commits
ahead of `main`, uncommitted files, open and claimed tasks, and the newest log entry.

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
python scripts/agent_status.py                        # the handoff state, live
ruff check --select F src tests scripts               # optional; not a project dependency
```

MuJoCo is pinned to 3.3.7 (`pyproject.toml`); do not upgrade it inside another task - it
moves physics results (see docs/RADAR.md and BACKLOG LW-004). The full headless suite takes
about six minutes on two cores; run the files you touched first, the whole suite before a
commit.

## How a change is made

1. **Claim** a task in `docs/agents/BACKLOG.md`: status `claimed`, your name, the date.
   One agent per task; if a claim is older than a week with no log entry, ask the owner.
2. **Decide** in a decision record when behaviour changes: `docs/adr/NNNN-short-title.md`,
   numbered after the last one, with these parts:
   *Problem* (what was wrong, measured) · *Does an existing simulator solve it? Can we wrap
   it?* · *Unique contribution* (what is ours, as bullets) · *Blueprint and builder* (what
   saved designs see) · *Result* (numbers, and the tests that hold them) · *Boundaries*
   (what is not claimed).
3. **Test** first: a contract test that fails, then the change, then an integration check in
   the simulator. A physical claim needs a number, a reason and a test that holds it.
4. **Document** what users and later agents need: a `README.md` bullet for a user-visible
   feature, a dated section in `docs/VALIDATION.md` (what is checked, test counts, what is
   not claimed), `docs/ARCHITECTURE.md` for a new module, the `docs/ROADMAP.md` paragraph,
   and extra words for the new record in `docs/radar/profile.md` if papers name its subject
   differently.
5. **Commit** one decision per commit. Subject: `Topic: what changed` (e.g. "Friction that
   holds: noslip, and no self-contact between robot links"); body: what was measured before
   and after. Never commit a failing suite; never rewrite published history.
6. **Hand off** before you stop, even mid-task: add an entry at the top of
   `docs/agents/LOG.md`, update `docs/agents/STATE.md`, and set the task's status. If work
   is unfinished, say exactly where it stopped and what is uncommitted.

Agents do not publish. The owner moves the branch to GitHub; an agent's work ends in
commits on the working branch and an up-to-date handoff.

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
- The repository is public: no personal data, keys or paths in code, docs or logs; third-party
  assets are listed with their licences in `THIRD_PARTY.md`.
