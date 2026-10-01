# State

Updated 2026-10-01 by Claude (Cowork). `python scripts/agent_status.py` prints the live
branch, commits and tree; this file says what they mean.

- **Branch** `contact-pair-friction`, ahead of `main` (the public import). Not yet on
  GitHub; the owner publishes it.
- **Decision records** 0001 to 0021. The newest: 0020 doorway and tilt table, 0021 frontier
  radar.
- **Tests**: 609 with a display (`LITTLE_WORLD_TEST_RENDER=1` under Xvfb), 573 headless.
  Every commit on the branch passed both.
- **Pinned**: Python 3.11 or newer, MuJoCo 3.3.7. A trial of 3.14 is recorded in
  docs/RADAR.md (OPEN LW-001 to LW-004).
- **Uncommitted**: nothing.
- **Needs the owner's decision**: publishing the branch; a MuJoCo upgrade (LW-004); radar
  phase two (LW-012); hardware for a servo calibration (LW-009).
