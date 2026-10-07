"""The notes agents keep for the owner stay readable (AGENTS.md, docs/agents/).

Agents report what they did and what is unfinished; the owner decides what happens next.
These checks keep that record usable: every file is there, the open items form a table
with unique numbers, known statuses and who found each, the reports keep the newest
first, every proposal in the frontier file has its six fields and a known status, and the
log is one dated line per entry that each agent can read from where it left off.
"""
from datetime import datetime
from importlib import util
from pathlib import Path
import re


from little_world.radar.brief import BEGIN, END, FIELDS, STATUSES, proposals

ROOT = Path(__file__).resolve().parents[1]


def status_module():
    spec = util.spec_from_file_location('agent_status', ROOT / 'scripts' / 'agent_status.py')
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_notes_point_to_every_file_and_they_exist():
    notes = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
    for name in ('docs/agents/STATE.md', 'docs/agents/REPORTS.md', 'docs/agents/OPEN.md', 'docs/agents/FRONTIER.md',
                 'docs/agents/LOG.md', 'docs/agents/README.md', 'scripts/agent_status.py'):
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
    assert status.main([]) == 0
    printed = capsys.readouterr().out
    listed = {line.split()[0] for line in printed.splitlines() if line.startswith('  LW-')}
    assert listed == {item_id for item_id, *_, state in rows if state == 'open'}
    assert 'last report' in printed


def test_the_frontier_proposals_have_their_fields_in_order_and_a_known_status():
    """docs/agents/FRONTIER.md (ADR 0026): numbered proposals, each with Status, From, Idea, In
    Little World, How we would know and Cost and needs; a done one names its decision record;
    the radar's section comes after them, between its two markers, once."""
    text = (ROOT / 'docs' / 'agents' / 'FRONTIER.md').read_text(encoding='utf-8')
    assert text.count(BEGIN) == text.count(END) == 1 and text.rindex('### FR-') < text.index(BEGIN) < text.index(END)
    found = proposals(text)
    ids = [p[0] for p in found]
    assert ids and ids == sorted(set(ids)), ids
    for proposal_id, title, state, body in found:
        assert title and state in STATUSES, (proposal_id, state)
        labels = [label for label in re.findall(r'^- ([A-Z][A-Za-z ]+):', body, re.MULTILINE) if label in FIELDS]
        assert labels == list(FIELDS), (proposal_id, labels)
        if state == 'done':
            assert re.search(r'ADR \d{4}', body), proposal_id


def test_the_status_script_lists_the_proposals_that_wait_on_the_owner(capsys):
    status = status_module()
    text = (ROOT / 'docs' / 'agents' / 'FRONTIER.md').read_text(encoding='utf-8')
    assert status.frontier(text) == [p[:3] for p in proposals(text)]
    assert status.main([]) == 0
    listed = {line.split()[0]: line.split()[1] for line in capsys.readouterr().out.splitlines()
              if line.startswith('  FR-')}
    assert listed == {pid: state for pid, _, state, _ in proposals(text) if state in ('proposed', 'accepted', 'doing')}


def test_the_log_is_one_dated_line_per_entry_and_merges_keep_both_sides():
    status = status_module()
    text = (ROOT / 'docs' / 'agents' / 'LOG.md').read_text(encoding='utf-8')
    entries = status.log_entries(text)
    assert entries, 'no entries parsed'
    written = [line for line in text.splitlines() if line.startswith('- 20')]
    assert written == [line for *_, line in entries], 'a line that looks like an entry is not one'
    for when, who, what, _ in entries:
        assert datetime.strptime(when, '%Y-%m-%d %H:%M') and who and what
    assert 'docs/agents/LOG.md merge=union' in (ROOT / '.gitattributes').read_text(encoding='utf-8')
    assert '.agent-status/' in (ROOT / '.gitignore').read_text(encoding='utf-8').split()


def test_reading_and_writing_the_log_never_run_git(tmp_path, monkeypatch, capsys):
    """`--new` and `--add` (Codex's, tests/test_agent_status.py) work in any checkout, git or
    not; only the status summary asks git, and only to read."""
    status = status_module()
    monkeypatch.setattr(status, 'ROOT', tmp_path)

    def no_git(*args):
        raise AssertionError(f'git {args}')
    monkeypatch.setattr(status, 'git', no_git)
    assert status.main(['--add', 'Claude (Cowork)', 'started: a test (tests/)']) == 0
    added = capsys.readouterr().out
    assert status.ENTRY.match(added.rstrip('\n')) and (tmp_path / 'docs/agents/LOG.md').read_text() == added
    assert status.main(['--new', 'codex']) == 0 and capsys.readouterr().out == added
    assert status.main(['--new', 'codex']) == 0 and capsys.readouterr().out == ''
