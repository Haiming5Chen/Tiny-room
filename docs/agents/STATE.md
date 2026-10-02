# State

Updated 2026-10-01 by Claude (Cowork). `python scripts/agent_status.py` prints the live
branch, commits and tree; this file says what they mean.

- **Branch** `contact-pair-friction`, ahead of `main` (the public import). Not yet on
  GitHub; the owner publishes it.
- **Decision records** 0001 to 0024. The newest: 0024 runs under variation.
- **Tests**: on MuJoCo 3.3.7, 626 pass with a display (`LITTLE_WORLD_TEST_RENDER=1` under
  Xvfb) and 589 headless. The headless suite also passes in full on MuJoCo 3.14 (589).
- **Pinned**: Python 3.11 or newer, MuJoCo 3.3.7. Upgrading to 3.14 is the owner's decision
  (OPEN LW-004); nothing in the suite stands in its way.
- **Uncommitted**: nothing.
- **Needs the owner's decision**: publishing the branch; a MuJoCo upgrade (LW-004); radar
  phase two (LW-012); hardware for a servo calibration (LW-009); the Curb run's 20 mm curb
  (LW-015).
