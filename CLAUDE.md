# Little World — Claude entry point

Read [AGENTS.md](AGENTS.md) and the [coordination protocol](docs/agents/README.md).
Run `python scripts/agent_status.py --new claude` before editing and at task
boundaries. Append events with `python scripts/agent_status.py --add "Claude (Cowork)" "started: objective (paths)"`.
Record starts/scope expansions, commits, frontier proposals, research papers and
stops in [LOG.md](docs/agents/LOG.md). Include concrete paths/IDs and commit hashes.

Leave Codex's active files alone until its commit/stop releases them; ask the owner
if needed sooner. Reuse completed work after inspecting its files and contracts.
Neither agent assigns the other work. The log reports only and does not sync
checkouts or run Git. Keep test windows hidden. [HANDOFF.md](HANDOFF.md) is older
context; current coordination belongs in LOG.md.
