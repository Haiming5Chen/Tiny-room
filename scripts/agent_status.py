"""Where the work stands, for an agent picking it up: python scripts/agent_status.py

Prints the branch, the commits it has beyond main, uncommitted files, the tasks that are
open, claimed or blocked in docs/agents/BACKLOG.md, and the newest entry of
docs/agents/LOG.md. Standard library only; reads git, never writes.
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / 'docs' / 'agents'
STATUSES = ('open', 'claimed', 'blocked', 'done', 'dropped')


def git(*args):
    try:
        return subprocess.run(('git', *args), cwd=ROOT, capture_output=True, text=True, check=True).stdout.rstrip()
    except (OSError, subprocess.CalledProcessError):
        return ''


def backlog(text):
    """[(id, status, owner, task, done when, source)] from the backlog's table."""
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) == 6 and re.fullmatch(r'LW-\d{3}', cells[0]):
            rows.append(tuple(cells))
    return rows


def log_entries(text):
    """[(date, heading)] of the log's entries, in the order written (newest first); the
    template in the log's fenced example is not an entry."""
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    return [(m.group(1), m.group(0)[3:]) for m in re.finditer(r'^## (\S+) · .+$', text, re.MULTILINE)]


def main(out=sys.stdout):
    branch = git('rev-parse', '--abbrev-ref', 'HEAD') or '(not a git checkout)'
    ahead = git('rev-list', '--count', 'main..HEAD')
    head = git('log', '-1', '--format=%h %s')
    dirty = [line for line in git('status', '--porcelain').splitlines() if line.strip()]
    print(f'branch   {branch}' + (f', {ahead} commits beyond main' if ahead else ''), file=out)
    print(f'head     {head}', file=out)
    print(f'tree     {len(dirty)} uncommitted file(s)' if dirty else 'tree     clean', file=out)
    for line in dirty[:10]:
        print(f'         {line.strip()}', file=out)
    if len(dirty) > 10:
        print(f'         and {len(dirty) - 10} more', file=out)
    rows = backlog((AGENTS / 'BACKLOG.md').read_text(encoding='utf-8'))
    live = [r for r in rows if r[1] in ('open', 'claimed', 'blocked')]
    print(f'\nbacklog  {len(live)} live of {len(rows)} tasks', file=out)
    for task_id, status, owner, task, *_ in live:
        print(f'  {task_id}  {status:8} {owner[:18]:18} {task[:80]}', file=out)
    entries = log_entries((AGENTS / 'LOG.md').read_text(encoding='utf-8'))
    if entries:
        print(f'\nlast log {entries[0][1]}', file=out)
    print('\nRead AGENTS.md, then docs/agents/STATE.md and the newest docs/agents/LOG.md entry.', file=out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
