#!/usr/bin/env python3
"""Where the work stands, and the agents' shared log. Standard library only.

    python scripts/agent_status.py                     # branch, tree, open items, proposals, last report, newest log lines
    python scripts/agent_status.py --new codex         # only the log events codex has not read yet
    python scripts/agent_status.py --add "Codex" "started: objective (paths)"   # one event, dated now in UTC

With no option it prints the branch, the commits beyond main, uncommitted files, the items
still open in docs/agents/OPEN.md, the proposals in docs/agents/FRONTIER.md that wait on the
owner or are under way, the newest report in docs/agents/REPORTS.md and the newest events in
docs/agents/LOG.md; it reads git and never writes it. `--new` and `--add` never run git: the
event log, its locking and the readers' cursors are described in docs/agents/README.md.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
try:
    import fcntl            # macOS and Linux: the whole file locked
except ImportError:         # Windows has no fcntl: msvcrt locks the file's first byte instead (LW-045)
    fcntl = None
    import msvcrt
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / 'docs' / 'agents'
STATUSES = ('open', 'done', 'dropped')
ENTRY = re.compile(r'^- (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC · (.+?) · (.+)$')


# -- the shared event log (written by Codex, 863720e) ------------------------------------------

def single_line(value):
    if not value.strip() or any(unicodedata.category(c).startswith('C') or c in '\u2028\u2029' for c in value):
        raise ValueError('Agent and event must be nonempty single-line text without control characters.')
    return value.strip()


@contextmanager
def locked(root):
    state = root / '.agent-status'
    state.mkdir(exist_ok=True)
    with (state / 'lock').open('ab') as lock:
        if fcntl is not None:
            fcntl.flock(lock, fcntl.LOCK_EX)
        else:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield state
        finally:
            if fcntl is not None:
                fcntl.flock(lock, fcntl.LOCK_UN)
            else:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def append(root, agent, event):
    agent, event = single_line(agent), single_line(event)
    line = f'- {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} · {agent} · {event}\n'
    with locked(root):
        path = root / 'docs/agents/LOG.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a+b') as stream:
            if stream.tell():
                stream.seek(-1, os.SEEK_END)
                if stream.read(1) != b'\n':
                    raise ValueError('Log has an incomplete last line; resolve it before appending.')
            stream.write(line.encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
    return line


def anchor(stream, offset):
    stream.seek(max(0, offset - 256))
    return hashlib.sha256(stream.read(min(offset, 256))).hexdigest()


def save_cursor(path, value):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.cursor-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def unread(root, agent):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', agent):
        raise ValueError('Reader identity must be lowercase letters, digits, underscores or hyphens (1–64 characters).')
    with locked(root) as state:
        cursor = state / f'{agent}.json'
        offset, previous = 0, None
        if cursor.exists():
            try:
                saved = json.loads(cursor.read_text(encoding='utf-8'))
                offset, previous = saved['offset'], saved['anchor']
                if type(offset) is not int or offset < 0 or not isinstance(previous, str) or not re.fullmatch('[0-9a-f]{64}', previous):
                    raise ValueError()
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f'Invalid cursor {cursor}; remove that local cursor to replay the log.') from exc
        path = root / 'docs/agents/LOG.md'
        if not path.exists():
            return
        with path.open('rb') as stream:
            if previous is not None and (path.stat().st_size < offset or anchor(stream, offset) != previous):
                print('Log boundary changed or was truncated; unread cursor reset to the beginning.', file=sys.stderr)
                offset = 0
            stream.seek(offset)
            data = stream.read()
            # A manually written partial line is not consumed until it is complete.
            complete = data[:data.rfind(b'\n') + 1]
            # Each event ends in a plain newline, whatever the log was written with: a log with Windows line
            # endings printed as it is would have them doubled by a Windows console's own translation (LW-045).
            output = ''.join(line.rstrip('\r\n') + '\n' for line in complete.decode('utf-8').splitlines(keepends=True)
                             if line.startswith('- '))
            sys.stdout.write(output)
            sys.stdout.flush()  # Do not consume events if delivery to stdout fails.
            offset += len(complete)
            save_cursor(cursor, dict(offset=offset, anchor=anchor(stream, offset)))


# -- where the work stands -------------------------------------------------------------------

def git(*args):
    try:
        return subprocess.run(('git', *args), cwd=ROOT, capture_output=True, text=True, check=True, encoding='utf-8').stdout.rstrip()
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
    """[(when, who, what, line)] of the log's events, in file order; other lines (the
    header) are not events."""
    return [(*m.groups(), m.group(0)) for m in map(ENTRY.match, text.splitlines()) if m]


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
    path = AGENTS / 'OPEN.md'
    rows = open_items(path.read_text(encoding='utf-8')) if path.exists() else []
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
    path = AGENTS / 'REPORTS.md'
    found = reports(path.read_text(encoding='utf-8')) if path.exists() else []
    if found:
        print(f'\nlast report  {found[0][1]}', file=out)
    path = AGENTS / 'LOG.md'
    events = log_entries(path.read_text(encoding='utf-8')) if path.exists() else []
    if events:
        print(f'\nlog      {len(events)} events; the newest three (only what is new to you: --new NAME):', file=out)
        for *_, line in events[-3:]:
            print(f'  {line[2:][:110]}', file=out)
    print('\nThe owner decides what is worked on; reports and open items are in docs/agents/.', file=out)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--new', metavar='READER', help='Print unread events and advance this checkout-local cursor.')
    actions.add_argument('--add', nargs=2, metavar=('AGENT', 'EVENT'), help='Append one UTC event and print it.')
    args = parser.parse_args(argv)
    if args.add is None and args.new is None:
        return status(sys.stdout)
    try:
        if args.add:
            print(append(ROOT, *args.add), end='')
        else:
            unread(ROOT, args.new)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'agent_status: {exc}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
