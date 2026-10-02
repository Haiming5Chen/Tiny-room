# State

Updated 2026-10-02 by Claude (Cowork). `python scripts/agent_status.py` prints the live
branch, commits and tree; this file says what they mean.

- **Branch** `contact-pair-friction`, ahead of `main` (the public import). Not yet on
  GitHub; the owner publishes it.
- **Decision records** 0001 to 0027. The newest: 0027 MuJoCo 3.10.0, one contact per convex pair.
- **Tests**: on MuJoCo 3.10.0, 643 pass with a display (`LITTLE_WORLD_TEST_RENDER=1` under
  Xvfb) and 606 headless.
- **Pinned**: Python 3.11 or newer, MuJoCo 3.10.0 (ADR 0027), the newest release with
  wheels for an Intel Mac; multiccd off. The owner's Mac reinstalls after publishing.
- **Proposals**: `docs/agents/FRONTIER.md`; FR-003 to FR-014 wait for the owner.
- **Uncommitted**: nothing.
- **Needs the owner's decision**: publishing the branch; the frontier proposals; the rest of
  radar phase two (LW-012: embeddings, a classifier); hardware for a servo calibration
  (LW-009); the Curb run's 20 mm curb (LW-015); a turned machine on the tilt table (LW-017).
