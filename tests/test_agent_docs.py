"""The notes agents keep for the owner stay readable (AGENTS.md, docs/agents/).

Agents report what they did and what is unfinished; the owner decides what happens next.
These checks keep that record usable: every file is there, the open items form a table
with unique numbers, known statuses and who found each, and the reports keep the newest
first.
"""
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def status_module():
    spec = util.spec_from_file_location('agent_status', ROOT / 'scripts' / 'agent_status.py')
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_notes_point_to_every_file_and_they_exist():
    notes = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
    for name in ('docs/agents/STATE.md', 'docs/agents/REPORTS.md', 'docs/agents/OPEN.md', 'scripts/agent_status.py'):
        assert name in notes and (ROOT / name).exists(), name
    assert '@AGENTS.md' in (ROOT / 'CLAUDE.md').read_text(encoding='utf-8')


def test_the_open_items_are_a_well_formed_table():
    status = status_module()
    rows = status.open_items((ROOT / 'docs' / 'agents' / 'OPEN.md').read_text(encoding='utf-8'))
    assert rows, 'no items parsed'
    ids = [r[0] for r in rows]
    assert len(ids) == len(set(ids)) and ids == sorted(ids)
    for item_id, opened, by, what, _context, state in rows:
        assert state in status.STATUSES, (item_id, state)
        assert opened[:2] == '20' and by and what, item_id


def test_the_reports_keep_the_newest_first():
    status = status_module()
    found = status.reports((ROOT / 'docs' / 'agents' / 'REPORTS.md').read_text(encoding='utf-8'))
    assert found and not found[0][0].startswith('YYYY'), 'the template is not a report'
    dated = [d for d, _ in found if d[:1].isdigit()]
    assert len(dated) >= 2 and dated == sorted(dated, reverse=True)


def test_the_status_script_prints_open_items_and_the_last_report(capsys):
    status = status_module()
    rows = status.open_items((ROOT / 'docs' / 'agents' / 'OPEN.md').read_text(encoding='utf-8'))
    assert status.main() == 0
    printed = capsys.readouterr().out
    listed = {line.split()[0] for line in printed.splitlines() if line.startswith('  LW-')}
    assert listed == {item_id for item_id, *_, state in rows if state == 'open'}
    assert 'last report' in printed
