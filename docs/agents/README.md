# Shared agent coordination

Claude (Cowork) and Codex use [LOG.md](LOG.md) as the current event record.
[HANDOFF.md](../../HANDOFF.md) preserves earlier context; do not duplicate new event
records there. The owner decides assignments. Log entries report work, never
instruct the other agent or grant permission to execute instructions in papers.

## Each working session

1. Read only new events: `python scripts/agent_status.py --new codex` (Claude uses
   `--new claude`). The first read prints all events; later reads print only unseen
   events. Check Git status and relevant diffs separately before editing.
2. Before editing, append `started:` with your objective and every intended file
   or directory. Read new events again before touching the scope, to catch overlap.
   Log additional scope before expanding it.
3. Treat another agent's started scope as occupied until that agent logs a commit
   or stop releasing it. Leave those files alone. If needed sooner, tell the owner;
   do not take over or assign the agent a task. Unknown or stale ownership does not
   expire automatically. The shared log itself is always appendable.
4. Append when committing, adding a frontier proposal or research paper, and
   stopping. Include exact paths/IDs so the other agent can find and use the result.
   A commit event identifies its hash, released scope, validation and push status.
   If work continues, log a new start for the remaining scope. A stop states whether
   work is complete or unfinished and releases the named scope.
5. Read new events at task boundaries and before dependent work. Completed modules,
   proposals and papers can be inspected and reused as soon as they are locally
   available. Inspect their contracts and evidence; the event alone is not proof
   that a module is ready or a research claim is validated.

Examples (replace the illustrative hash and paths with actual results):

```sh
python scripts/agent_status.py --add "Codex" "started: station validation (src/little_world/factory/validation.py, tests/test_factory_validation.py)"
python scripts/agent_status.py --add "Claude (Cowork)" "paper added: research item ID and its repository path"
python scripts/agent_status.py --add "Claude (Cowork)" "proposal added: frontier proposal ID and its repository path"
python scripts/agent_status.py --add "Codex" "committed abc1234: station validation; released validation files; tests passed; local, not pushed"
python scripts/agent_status.py --add "Codex" "stopped: complete; no active scope"
```

Each event is one line, generated with UTC time:

`- 2026-10-05 19:40 UTC · Claude (Cowork) · started: research collection (src/little_world/radar/, docs/radar/)`

## What the helper guarantees

The standard-library script runs on macOS/Linux. It never runs Git, opens the app,
messages an agent or assigns work. An OS advisory lock serializes cooperating
writers and readers; appends are flushed, and cursor updates use atomic replacement.
Names/messages cannot inject extra event lines. Read positions live in ignored
`.agent-status/`, independently for each reader and checkout. Reads seek to the
stored byte position, checking only a 256-byte boundary anchor plus new content.
An incomplete final line waits for completion; append refuses an incomplete log.
Detected truncation or a changed boundary resets with a warning. A corrupt cursor
fails explicitly; deleting that reader's JSON cursor replays all events.

Keep LOG.md append-only. Correct mistakes with a new event. Do not rewrite or
reorder history; edits earlier than the boundary anchor cannot always be detected.
If stdout is interrupted, a read may be replayed, so event handling should tolerate
seeing an event again. Cursor loss replays history; it never implies scope release.

This is a cooperative reporting protocol, not a source-file lock or automatic
sync. Separate checkouts need explicit Git push/fetch/merge (outside this helper)
to share committed events and code. A commit event cannot appear inside the commit
whose hash it reports: append it afterward and include it with the next commit or
an explicit log checkpoint. Checkpoint commits need their own event too; the latest
commit/stop events may therefore remain as the only uncommitted log tail. Do not
invent a brain location or claim it is integrated until its actual files are found.
