# State

Updated 2026-10-23 by Claude (Cowork). `python scripts/agent_status.py` prints the live
branch, commits and tree; this file says what they mean. What each agent is doing right
now is in `LOG.md` (`python scripts/agent_status.py --new NAME` prints only what is new).

- **Branch** `contact-pair-friction`, ahead of `main` (the public import), with Codex's line
  of work (its six commits on the Mac's `main`, up to 863720e) merged in on 2026-10-07 at the
  owner's decision. Not yet on GitHub; the owner publishes it.
- **Decision records** 0001 to 0055. The newest: 0055 watch it work (the owner's request of 26
  October: recent work seen in the app), 0054 searching for the failure (FR-025, measured, not adopted), 0053 time passes while the program looks (FR-028), 0052 how late is too late (FR-022), 0051 what looking again earns (FR-023), 0050 a contact census (FR-030), 0049 tuning draws and held-out
  draws (FR-027), 0048 a grasp the program feels (FR-026), all by the weekly readings' ranking; 0047 a gripper from its file (OPEN LW-030, FR-031's loose end); 0046
  the first hour, checked by the app (FR-033); 0045 the tool travels its line (FR-032), both by
  the focused reading's ranking; 0044 robots from their own files (FR-031, the owner's request of
  21 Oct).
- **Tests**: on MuJoCo 3.10.0, 1092 pass with a display (`LITTLE_WORLD_TEST_RENDER=1`
  under Xvfb) and 1037 headless; each test runs with an empty robot library of its own.
- **Pinned**: Python 3.11 or newer, MuJoCo 3.10.0 (ADR 0027), the newest release with
  wheels for an Intel Mac; multiccd off. The owner's Mac reinstalls after publishing.
- **Proposals**: `docs/agents/FRONTIER.md`; FR-001 to FR-003, FR-006, FR-011, FR-015 to
  FR-018, FR-020, FR-021, FR-022 (how late is too late), FR-024, FR-025 (measured, not adopted), FR-028 (latency), FR-026 (a grasp the program feels), FR-023 (the retreat baseline), FR-027 (held-out draws), FR-030 (a contact census), FR-031 (a robot library from URDF and MJCF files, the
  owner's request of 21 October), FR-032 (the tool moved, not the joints) and FR-033 (an
  interactive first hour) done; FR-004, FR-005, FR-007, FR-008, FR-012 to FR-014, FR-019
  and FR-029 wait for the owner (FR-019 from the
  weekly reading of 5 October, FR-022 to FR-026 from that of 19 October, FR-027 to FR-030 from
  that of 21 October, FR-031 to FR-035 from the focused reading of 21 October); FR-034 (network
  and an optional dependency) and FR-035 (an MCP server, which the owner said to delay) are the
  owner's to start; FR-009 and FR-010 not now (the owner).
- **Uncommitted**: nothing.
- **Needs the owner's decision**: publishing the branch; the frontier proposals; the rest of
  radar phase two (LW-012: embeddings, a classifier); hardware for a servo calibration
  (LW-009); the Curb run's 20 mm curb (LW-015); a slippery floor patch (LW-018).
