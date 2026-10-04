# State

Updated 2026-10-04 by Claude (Cowork). `python scripts/agent_status.py` prints the live
branch, commits and tree; this file says what they mean.

- **Branch** `contact-pair-friction`, ahead of `main` (the public import). Not yet on
  GitHub; the owner publishes it.
- **Decision records** 0001 to 0032. The newest: 0032 a depth camera at the Fetch table.
- **Tests**: on MuJoCo 3.10.0, 682 pass with a display (`LITTLE_WORLD_TEST_RENDER=1`
  under Xvfb) and 643 headless.
- **Pinned**: Python 3.11 or newer, MuJoCo 3.10.0 (ADR 0027), the newest release with
  wheels for an Intel Mac; multiccd off. The owner's Mac reinstalls after publishing.
- **Proposals**: `docs/agents/FRONTIER.md`; FR-001 to FR-003, FR-006 and FR-011 done; FR-004,
  FR-005, FR-007, FR-008, FR-012 to FR-016 wait for the owner; FR-009 and FR-010 not now (the
  owner).
- **Uncommitted**: nothing. Running when ADR 0032 was committed, for a follow-up commit: the
  disturbance sweep run blind on the same day.
- **Needs the owner's decision**: publishing the branch; the frontier proposals; the rest of
  radar phase two (LW-012: embeddings, a classifier); hardware for a servo calibration
  (LW-009); the Curb run's 20 mm curb (LW-015); a slippery floor patch (LW-018); looking
  again after a missed grasp (FR-015, LW-020); planning the stop from what the camera sees
  (FR-016, LW-021).
