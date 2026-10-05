"""Where the work stands: python scripts/agent_status.py

Prints the branch, the commits it has beyond main, uncommitted files, the items still
open in docs/agents/OPEN.md, the proposals in docs/agents/FRONTIER.md that wait on the
owner or are under way, the newest entry of docs/agents/REPORTS.md and the newest lines
of docs/agents/LOG.md. Standard library only; reads git, never writes it.

The log is what the agents are doing as it happens. Two commands keep it cheap to follow;
neither runs git, so they are safe in any checkout:

    python scripts/agent_status.py --new claude          # only the lines claude has not read yet
    python scripts/agent_status.py --add "Claude (Cowork)" "committed abc1234 ..."

`--new NAME` remembers what NAME has read in `.agents/NAME.seen` (one checkout's own memory,
not committed), by line rather than by position, so lines that a merge puts in a different
order are still read once. `--add WHO TEXT` appends `- <now, UTC> · WHO · TEXT` and counts
it as read by WHO's first word, lower-cased.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / 'docs' / 'agents'
LOG = AGENTS / 'LOG.md'
MARKS = ROOT / '.agents'
STATUSES = ('open', 'done', 'dropped')
ENTRY = re.compile(r'^- (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC · (.+?) · (.+)$')
NAME = re.compile(r'[a-z][a-z0-9-]{0,31}')


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


def frontier(text):
    """[(id, title, status)] of the proposals in FRONTIER.md, in order (ADR 0026); the same
    reading as `little_world.radar.brief.proposals`, without importing the package."""
    found = []
    heads = list(re.finditer(r'^### (FR-\d{3}) · (.+)$', text, re.MULTILINE))
    for k, head in enumerate(heads):
        body = text[head.end():heads[k + 1].start() if k + 1 < len(heads) else len(text)]
        status = re.search(r'^- Status: (\w+)', body, re.MULTILINE)
        found.append((head.group(1), head.group(2).strip(), status.group(1) if status else ''))
    return found


def reports(text):
    """[(date, heading)] of the reports, in the order written (newest first); the template
    in the file's fenced example is not a report."""
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    return [(m.group(1), m.group(0)[3:]) for m in re.finditer(r'^## (\S+) · .+$', text, re.MULTILINE)]


def log_entries(text):
    """[(when, who, what, line)] of the log's entries, in file order; other lines (the
    header, the example in it) are not entries."""
    return [(*m.groups(), m.group(0)) for m in map(ENTRY.match, text.splitlines()) if m]


def reader(name):
    """The key a reader's marks are kept under: the first word of a name, lower-cased."""
    words = re.findall(r'[A-Za-z][A-Za-z0-9-]*', name)
    key = words[0].lower() if words else ''
    if not NAME.fullmatch(key):
        raise ValueError(f'not a reader name: {name!r}')
    return key


def _mark(line):
    return hashlib.sha1(line.strip().encode('utf-8')).hexdigest()[:16]


def seen(name, marks=MARKS):
    path = marks / f'{reader(name)}.seen'
    return set(path.read_text(encoding='utf-8').split()) if path.exists() else set()


def remember(name, lines, marks=MARKS):
    marks.mkdir(exist_ok=True)
    known = seen(name, marks) | {_mark(line) for line in lines}
    (marks / f'{reader(name)}.seen').write_text('\n'.join(sorted(known)) + '\n', encoding='utf-8')


def unread(name, entries, marks=MARKS):
    """The entries `name` has not read, in file order, and from now on counted as read."""
    known = seen(name, marks)
    new = [entry for entry in entries if _mark(entry[3]) not in known]
    remember(name, [entry[3] for entry in entries], marks)
    return new


def add(who, what, log=LOG, marks=MARKS, now=None):
    """Appends one entry to the log, dated now in UTC, and counts it as read by its writer."""
    who, what = ' '.join(who.split()), ' '.join(what.split())
    if not who or not what or ' · ' in who:
        raise ValueError('an entry needs who and what; who has no " · "')
    reader(who)
    when = (now or datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M')
    line = f'- {when} UTC · {who} · {what}'
    text = log.read_text(encoding='utf-8')
    log.write_text(text + ('' if text.endswith('\n') else '\n') + line + '\n', encoding='utf-8')
    remember(who, [line], marks)
    return line


def status(out):
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
    path = AGENTS / 'FRONTIER.md'
    proposals = frontier(path.read_text(encoding='utf-8')) if path.exists() else []
    waiting = [p for p in proposals if p[2] == 'proposed']
    moving = [p for p in proposals if p[2] in ('accepted', 'doing')]
    if proposals:
        print(f'\nfrontier {len(proposals)} proposals: {len(waiting)} wait on the owner, '
              f'{len(moving)} accepted or under way', file=out)
        for proposal_id, title, state in moving + waiting:
            print(f'  {proposal_id}  {state:9} {title[:72]}', file=out)
    found = reports((AGENTS / 'REPORTS.md').read_text(encoding='utf-8'))
    if found:
        print(f'\nlast report  {found[0][1]}', file=out)
    entries = log_entries(LOG.read_text(encoding='utf-8')) if LOG.exists() else []
    if entries:
        print(f'\nlog      {len(entries)} lines; the newest three (only what is new to you: --new NAME):', file=out)
        for *_, line in entries[-3:]:
            print(f'  {line[2:][:110]}', file=out)
    print('\nThe owner decides what is worked on; reports and open items are in docs/agents/.', file=out)
    return 0


def main(argv=(), out=None):
    out = out or sys.stdout
    parser = argparse.ArgumentParser(prog='agent_status.py', description='Where the work stands.')
    parser.add_argument('--new', metavar='NAME', help='print only the log lines NAME has not read, then remember them')
    parser.add_argument('--add', nargs=2, metavar=('WHO', 'TEXT'), help='append a line to the log, dated now')
    args = parser.parse_args(list(argv))
    if args.add:
        try:
            print(add(*args.add, log=LOG, marks=MARKS), file=out)
        except ValueError as error:
            parser.error(str(error))
        return 0
    if args.new:
        try:
            entries = log_entries(LOG.read_text(encoding='utf-8')) if LOG.exists() else []
            new = unread(args.new, entries, MARKS)
        except ValueError as error:
            parser.error(str(error))
        print(f'{len(new)} new line(s) in docs/agents/LOG.md for {reader(args.new)}' + (':' if new else '.'), file=out)
        for *_, line in new:
            print(line, file=out)
        return 0
    return status(out)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
