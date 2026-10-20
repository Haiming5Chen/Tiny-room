# State

Updated 2026-10-20 by Claude (Cowork). `python scripts/agent_status.py` prints the live
branch, commits and tree; this file says what they mean. What each agent is doing right
now is in `LOG.md` (`python scripts/agent_status.py --new NAME` prints only what is new).

- **Branch** `contact-pair-friction`, ahead of `main` (the public import), with Codex's line
  of work (its six commits on the Mac's `main`, up to 863720e) merged in on 2026-10-07 at the
  owner's decision. Not yet on GitHub; the owner publishes it.
- **Decision records** 0001 to 0041. The newest: 0041 the cart stands on all four (LW-025, the
  owner's decision); 0040 how gently a part is handled (FR-020).
- **Tests**: on MuJoCo 3.10.0, 991 pass with a display (`LITTLE_WORLD_TEST_RENDER=1`
  under Xvfb) and 944 headless.
- **Pinned**: Python 3.11 or newer, MuJoCo 3.10.0 (ADR 0027), the newest release with
  wheels for an Intel Mac; multiccd off. The owner's Mac reinstalls after publishing.
- **Proposals**: `docs/agents/FRONTIER.md`; FR-001 to FR-003, FR-006, FR-011, FR-015 to
  FR-018, FR-020 and FR-021 done; FR-004, FR-005, FR-007, FR-008, FR-012 to FR-014, FR-019 and
  FR-022 to FR-026 wait for the owner (FR-019 from the weekly reading of 5 October, FR-022 to
  FR-026 from that of 19 October); FR-009 and FR-010 not now (the owner).
- **Uncommitted**: nothing.
- **Needs the owner's decision**: publishing the branch; the frontier proposals; the rest of
  radar phase two (LW-012: embeddings, a classifier); hardware for a servo calibration
  (LW-009); the Curb run's 20 mm curb (LW-015); a slippery floor patch (LW-018).
