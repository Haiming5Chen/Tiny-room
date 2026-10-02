# State

Updated 2026-10-02 by Claude (Cowork). `python scripts/agent_status.py` prints the live
branch, commits and tree; this file says what they mean.

- **Branch** `contact-pair-friction`, ahead of `main` (the public import). Not yet on
  GitHub; the owner publishes it.
- **Decision records** 0001 to 0026. The newest: 0026 the frontier brief and proposals.
- **Tests**: on MuJoCo 3.3.7, 642 pass with a display (`LITTLE_WORLD_TEST_RENDER=1` under
  Xvfb) and 605 headless.
- **Pinned**: Python 3.11 or newer, MuJoCo 3.3.7. The owner chose 3.10.0 for every machine
  (FR-002): the newest release with wheels for an Intel Mac.
- **Proposals**: `docs/agents/FRONTIER.md`; FR-003 to FR-014 wait for the owner.
- **Uncommitted**: nothing.
- **Needs the owner's decision**: publishing the branch; the frontier proposals; the rest of
  radar phase two (LW-012: embeddings, a classifier); hardware for a servo calibration
  (LW-009); the Curb run's 20 mm curb (LW-015); a turned machine on the tilt table (LW-017).
