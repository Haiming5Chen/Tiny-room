"""The handoff files agents rely on stay readable (AGENTS.md, docs/agents/).

An agent starting here reads AGENTS.md, the state, the newest log entry and the backlog;
these checks keep that path from rotting: every file is there, the backlog's table parses
with unique task numbers and known statuses, a claimed task names its owner, and the log
keeps its newest entry first.
"""
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def status_module():
    spec = util.spec_from_file_location('agent_status', ROOT / 'scripts' / 'agent_status.py')
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_guide_points_to_every_handoff_file_and_they_exist():
    guide = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
    for name in ('docs/agents/STATE.md', 'docs/agents/LOG.md', 'docs/agents/BACKLOG.md', 'scripts/agent_status.py'):
        assert name in guide and (ROOT / name).exists(), name
    assert '@AGENTS.md' in (ROOT / 'CLAUDE.md').read_text(encoding='utf-8')


def test_the_backlog_is_a_well_formed_table():
    status = status_module()
    rows = status.backlog((ROOT / 'docs' / 'agents' / 'BACKLOG.md').read_text(encoding='utf-8'))
    assert rows, 'no tasks parsed'
    ids = [r[0] for r in rows]
    assert len(ids) == len(set(ids)) and ids == sorted(ids)
    for task_id, state, owner, task, done_when, _source in rows:
        assert state in status.STATUSES, (task_id, state)
        assert task and done_when, task_id
        assert state != 'claimed' or owner, f'{task_id} is claimed by nobody'


def test_the_log_keeps_its_newest_entry_first():
    status = status_module()
    entries = status.log_entries((ROOT / 'docs' / 'agents' / 'LOG.md').read_text(encoding='utf-8'))
    assert entries and not entries[0][0].startswith('YYYY'), 'the template is not an entry'
    dated = [d for d, _ in entries if d[:1].isdigit()]
    assert len(dated) >= 2 and dated == sorted(dated, reverse=True)


def test_the_status_script_runs_without_git_state_to_rely_on(capsys):
    assert status_module().main() == 0
    printed = capsys.readouterr().out
    assert 'backlog' in printed and 'LW-001' in printed and 'last log' in printed
