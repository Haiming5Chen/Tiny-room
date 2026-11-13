"""Contract tests for the shared log CLI; subprocesses never invoke Git."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import shutil
import os
import subprocess
import sys

import pytest


@pytest.fixture
def checkout(tmp_path):
    script = tmp_path / 'scripts' / 'agent_status.py'
    script.parent.mkdir()
    shutil.copyfile(Path(__file__).parents[1] / 'scripts' / 'agent_status.py', script)
    return tmp_path


def run(root, *args):
    # The log's middle dots in UTF-8 both ways, whatever the system's code page (LW-045).
    return subprocess.run([sys.executable, str(root / 'scripts/agent_status.py'), *args],
                          capture_output=True, text=True, encoding='utf-8',
                          env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})


def test_add_and_independent_unread_cursors(checkout):
    assert run(checkout, '--new', 'codex').stdout == ''
    added = run(checkout, '--add', 'Claude (Cowork)', 'started: research (src/radar/)')
    assert added.returncode == 0
    assert re.fullmatch(r'- \d{4}-\d\d-\d\d \d\d:\d\d UTC · Claude \(Cowork\) · started: research \(src/radar/\)\n', added.stdout)
    assert run(checkout, '--new', 'codex').stdout == added.stdout
    assert run(checkout, '--new', 'codex').stdout == ''
    assert run(checkout, '--new', 'claude').stdout == added.stdout
    second = run(checkout, '--add', 'Codex', 'stopped: done ✓')
    assert run(checkout, '--new', 'codex').stdout == second.stdout
    assert run(checkout, '--new', 'claude').stdout == second.stdout


@pytest.mark.parametrize('args', [('--new', '../escape'), ('--add', 'Codex\nClaude', 'hello'),
                                    ('--add', 'Codex', 'one\ntwo'), ('--add', '', 'hello'),
                                    ('--add', 'Codex', 'bad\rline'), ('--add', 'Codex', '\x1b[2J')])
def test_invalid_input_does_not_append(checkout, args):
    result = run(checkout, *args)
    assert result.returncode != 0
    assert not (checkout / 'docs/agents/LOG.md').exists()


def test_concurrent_writers_preserve_whole_events(checkout):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda n: run(checkout, '--add', 'Codex', f'event {n}'), range(24)))
    assert all(r.returncode == 0 for r in results)
    lines = run(checkout, '--new', 'codex').stdout.splitlines()
    assert len(lines) == 24
    assert {line.rsplit(' · ', 1)[1] for line in lines} == {f'event {n}' for n in range(24)}
    with ThreadPoolExecutor(max_workers=2) as pool:
        # Two readers of the same identity cannot both consume the same event.
        run(checkout, '--add', 'Codex', 'last')
        reads = list(pool.map(lambda _: run(checkout, '--new', 'codex'), range(2)))
    assert sum(len(r.stdout.splitlines()) for r in reads) == 1


def test_truncation_resets_with_notice_and_partial_lines_wait(checkout):
    run(checkout, '--add', 'Codex', 'long previous event')
    run(checkout, '--new', 'codex')
    log = checkout / 'docs/agents/LOG.md'
    log.write_text('- replacement\n', encoding='utf-8')
    result = run(checkout, '--new', 'codex')
    assert result.stdout == '- replacement\n' and 'reset' in result.stderr
    with log.open('a', encoding='utf-8') as stream:
        stream.write('- partial')
    assert run(checkout, '--new', 'codex').stdout == ''
    with log.open('a', encoding='utf-8') as stream:
        stream.write(' finished\n')
    assert run(checkout, '--new', 'codex').stdout == '- partial finished\n'


def test_corrupt_cursor_fails_without_skipping_events(checkout):
    run(checkout, '--add', 'Codex', 'event')
    run(checkout, '--new', 'codex')
    (checkout / '.agent-status/codex.json').write_text('broken', encoding='utf-8')
    result = run(checkout, '--new', 'codex')
    assert result.returncode != 0 and 'cursor' in result.stderr.lower()
    assert run(checkout, '--new', 'claude').stdout.endswith(' · event\n')


def test_without_fcntl_the_log_is_locked_by_msvcrt_as_on_windows(checkout, monkeypatch):
    """Windows has no fcntl, and the helper failed to load there (LW-045): it locks the lock file's
    first byte with msvcrt instead, around the same append."""
    import importlib.util
    import types
    spec = importlib.util.spec_from_file_location('agent_status_on_windows', checkout / 'scripts/agent_status.py')
    status = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(status)
    calls = []
    monkeypatch.setattr(status, 'fcntl', None)
    monkeypatch.setattr(status, 'msvcrt', types.SimpleNamespace(LK_LOCK=1, LK_UNLCK=0, locking=lambda fd, mode, n: calls.append((mode, n))),
                        raising=False)
    line = status.append(checkout, 'Codex', 'started: a test')
    assert calls == [(1, 1), (0, 1)], "locked, then unlocked"
    assert line.endswith('· Codex · started: a test\n')
    assert (checkout / 'docs/agents/LOG.md').read_text(encoding='utf-8').endswith(line)
