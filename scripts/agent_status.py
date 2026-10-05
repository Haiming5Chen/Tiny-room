#!/usr/bin/env python3
"""Append UTC events or consume unread events. Standard library; never runs Git."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def single_line(value):
    if not value.strip() or any(unicodedata.category(c).startswith('C') or c in '\u2028\u2029' for c in value):
        raise ValueError('Agent and event must be nonempty single-line text without control characters.')
    return value.strip()


@contextmanager
def locked(root):
    state = root / '.agent-status'
    state.mkdir(exist_ok=True)
    with (state / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield state
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


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
            output = ''.join(line for line in complete.decode('utf-8').splitlines(keepends=True) if line.startswith('- '))
            sys.stdout.write(output)
            sys.stdout.flush()  # Do not consume events if delivery to stdout fails.
            offset += len(complete)
            save_cursor(cursor, dict(offset=offset, anchor=anchor(stream, offset)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--new', metavar='READER', help='Print unread events and advance this checkout-local cursor.')
    actions.add_argument('--add', nargs=2, metavar=('AGENT', 'EVENT'), help='Append one UTC event and print it.')
    args = parser.parse_args()
    try:
        if args.add:
            print(append(ROOT, *args.add), end='')
        else:
            unread(ROOT, args.new)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'agent_status: {exc}\n')


if __name__ == '__main__':
    main()
