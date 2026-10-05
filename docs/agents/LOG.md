# Log

What the agents are doing, as it happens, oldest first. Add a line when you start something
(what, and the files it will touch), when you commit, when you add to the frontier or the
research collection, and when you stop. Then the other agent can see what is being changed
before it changes the same files, and can use new work as soon as it lands.

Read only what is new to you, and write a line, with:

    python scripts/agent_status.py --new codex                       # the lines codex has not read yet
    python scripts/agent_status.py --add "Codex" "started: ... (files)"   # appends one, dated now in UTC

Neither runs git. Format: `- YYYY-MM-DD HH:MM UTC · who · what`, one line each, appended at
the end; details belong in the commit, the report or the decision record. Earlier lines are
not edited, and a merge keeps both sides' new lines (`.gitattributes`). A line reports; it
does not ask the other agent to do anything - the owner decides (AGENTS.md).

- 2026-10-03 21:51 UTC · Claude (Cowork) · committed 11009ec going back to the stop (ADR 0031) and 8601971 "Repeat with disturbances" (LW-018)
- 2026-10-04 02:41 UTC · Claude (Cowork) · committed a303c40 a depth camera at the Fetch table, programs that look (ADR 0032, FR-011); perception/ is new
- 2026-10-04 03:26 UTC · Claude (Cowork) · committed a2ee1a3 ADR 0032's disturbances run blind the same day (documents only)
- 2026-10-05 19:10 UTC · Claude (Cowork) · committed 942a287 looking again before the jaws go down, when stopped, when they miss (ADR 0033, FR-015)
- 2026-10-05 19:12 UTC · Claude (Cowork) · the weekly brain run failed at 00:52 UTC (no output); fired it again by hand
- 2026-10-05 19:15 UTC · Claude (Cowork) · started: this log and `agent_status.py --new` (docs/agents/LOG.md, scripts/agent_status.py, AGENTS.md, tests/test_agent_docs.py), then the radar's research collection and search (src/little_world/radar/, docs/radar/, docs/RADAR.md)
