"""Where the work stands: python scripts/agent_status.py

Prints the branch, the commits it has beyond main, uncommitted files, the items still
open in docs/agents/OPEN.md and the newest entry of docs/agents/REPORTS.md. Standard
library only; reads git, never writes.
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / 'docs' / 'agents'
STATUSES = ('open', 'done', 'dropped')


def git(*args):
    try:
        return subprocess.run(('git', *args), cwd=ROOT, capture_output=True, text=True, check=True).stdout.rstrip()
    except (OSError, subprocess.CalledProcessError):
        return ''


def open_items(text):
    """[(id, opened, by, what is open, context, status)] from the table in OPEN.md."""
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) == 6 and re.fullmatch(r'LW-\d{3}', cells[0]):
            rows.append(tuple(cells))
    return rows


def reports(text):
    """[(date, heading)] of the reports, in the order written (newest first); the template
    in the file's fenced example is not a report."""
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
    rows = open_items((AGENTS / 'OPEN.md').read_text(encoding='utf-8'))
    still = [r for r in rows if r[5] == 'open']
    print(f'\nopen     {len(still)} of {len(rows)} items', file=out)
    for item_id, opened, by, what, *_ in still:
        print(f'  {item_id}  {opened}  {what[:86]}', file=out)
    found = reports((AGENTS / 'REPORTS.md').read_text(encoding='utf-8'))
    if found:
        print(f'\nlast report  {found[0][1]}', file=out)
    print('\nThe owner decides what is worked on; reports and open items are in docs/agents/.', file=out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
