# Little World — shared agent handoff

This file is a shared record for Codex, Claude, and the project owner. It is not a
live messaging channel, file lock, scheduler, or permission to assign work.
Agents in the same checkout can read it immediately. Agents in another checkout
only see committed changes after they are pushed and fetched.

## Owner's collaboration rules

- Preserve the other agent's changes. Do not reset, overwrite, or remove work you
  did not author. Inspect the working tree and relevant diffs before editing.
- Do not assign work to another agent without asking the owner first.
- Report your own changes, verification, limitations, and commit status clearly.
- Keep test windows hidden. Do not launch visible app windows unless requested.
- Use AGENTS.md for repository rules and docs/AGENT_TESTING.md for test procedures.

## Coordination procedure

1. Check `git status --short --branch`, recent commits, and this file. Fetch the
   configured remote when checking for another agent's published work; fetching
   does not merge it. Never assume a clean checkout means another agent is idle.
2. Before substantive editing, add a dated entry with your agent name, objective,
   and intended files. This is a notice about your own work, not an assignment or
   exclusive lock. If another entry or current changes overlap, reconcile first;
   if the other agent is unreachable and the overlap is material, ask the owner.
3. Do not silently stage unrelated changes. Commit identifiable work and preserve
   other uncommitted files. Avoid force-pushing shared history.
4. Append completion evidence: changed files, test commands/results, remaining
   limitations, commit hash, and whether pushed. Do not rewrite another agent's
   record. Correct stale claims with a new entry.

## Capability map

- Custom machine construction: immutable Blueprint/AssemblyEditor, existing Anime
  builder, Python authoring, component catalog, saves and inventory.
- Real workspace: sourced robot models, Panda pick/place, joint programming and
  named position teaching. Teach positions currently fixes the hand downward.
- Factory changes: strict CellRequest JSON, before/after review, atomic apply,
  revision checks, undo/redo. Current layout is a fixed Panda cell, not an arbitrary
  multi-station factory generator.
- Test interface: labeled UI callbacks, actual form character input, JSON state
  snapshots, deterministic physics stepping and replayable scenario reports.
- Not connected: natural-language provider, the external research brain, general
  conveyor/process execution, arbitrary factory generation or collision-free
  motion planning. Do not describe these as implemented.

## Research brain

The owner reports that another agent maintains a weekly journal/paper collection.
Its repository/path, schema, maintainer status and schedule have not been verified
from this checkout. No integration or background job has been created here.
Once located, inspect it read-only first. Preserve source URLs, publication dates,
evidence and limitations. Turn relevant ideas into explicit proposals and bounded
tests; a paper's result is not evidence that Little World reproduces it. Do not
modify that database or delegate collection work without owner authorization.

## Work log

### 2026-10-03 — Codex — implementation completed

Commit: `097b0e9` — Add Panda teaching, reviewable cell edits, and hidden semantic tests.
At the time of the 2026-10-04 remote check, this commit was local and not pushed.

- Added factory teaching and changes modules, their native UI integrations, and
  documentation in docs/FACTORY.md, docs/AI_AUTHORING.md and docs/ARCHITECTURE.md.
- Added src/little_world/testing/, tests/scenarios/, adversarial request tests,
  semantic replay tests and a hidden-window pytest fixture.
- Fixed extreme-coordinate overflow validation and preserved failed/stale edits.
- Full validation: `LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q` —
  **674 passed**. Three separate hidden replays also passed **56 actions**.
- Local replay artifacts: build/agent-tests/ (ignored by Git). Reproduce them using
  docs/AGENT_TESTING.md. Normal app launches remain visible; tests stay hidden.
- All implementation work for that commit is finished; no active file reservation.

### 2026-10-04 — Codex — coordination record

Added this handoff and discovery links from AGENTS.md and CLAUDE.md. No runtime
files changed and no jobs were assigned. Documentation-only verification:
`git diff --check`; referenced paths checked locally.

Last verified remote: https://github.com/Haiming5Chen/Tiny-room, origin/main at
`eef1a37` (initial import). No additional remote branches or PRs were visible at
that check. Do not infer that the other agent has no work elsewhere.

Candidate next development topic, not assigned or started: a shared factory-scene
document with stable station IDs and reusable custom-machine Blueprints, so direct
editing and future AI proposals address the same objects. See docs/AI_AUTHORING.md
for scope and implementation order. The external brain's location remains unknown.
