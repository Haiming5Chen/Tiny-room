# State

Updated 2026-10-04 by Claude (Cowork). `python scripts/agent_status.py` prints the live
branch, commits and tree; this file says what they mean.

- **Branch** `contact-pair-friction`, ahead of `main` (the public import). Not yet on
  GitHub; the owner publishes it.
- **Decision records** 0001 to 0033. The newest: 0033 looking again.
- **Tests**: on MuJoCo 3.10.0, 687 pass with a display (`LITTLE_WORLD_TEST_RENDER=1`
  under Xvfb) and 648 headless.
- **Pinned**: Python 3.11 or newer, MuJoCo 3.10.0 (ADR 0027), the newest release with
  wheels for an Intel Mac; multiccd off. The owner's Mac reinstalls after publishing.
- **Proposals**: `docs/agents/FRONTIER.md`; FR-001 to FR-003, FR-006, FR-011 and FR-015 done;
  FR-004, FR-005, FR-007, FR-008, FR-012 to FR-014 and FR-016 wait for the owner; FR-009 and
  FR-010 not now (the owner).
- **Uncommitted**: nothing.
- **Needs the owner's decision**: publishing the branch; the frontier proposals; the rest of
  radar phase two (LW-012: embeddings, a classifier); hardware for a servo calibration
  (LW-009); the Curb run's 20 mm curb (LW-015); a slippery floor patch (LW-018); planning the
  stop from what the camera sees (FR-016, LW-021).
