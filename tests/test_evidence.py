"""The evidence anyone can measure again, the quick tier and the documents' links (ADR 0073).

The documents' numbers were all measured on one machine. `little-world evidence` runs thirteen
headline measurements again wherever it is run and prints each beside its recorded number; this
keeps its registry honest - every claim names a decision record and a test that exist - and
runs the quickest claim. The quick tier's list and the repository's links are checked here too:
both are things a newcomer meets before any physics.
"""
import io
import re
from importlib import util
from pathlib import Path

import pytest

from little_world import evidence
from little_world.evidence import BY_ID, CLAIMS, Claim, Quantity

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_claim_names_a_decision_record_and_a_test_that_exist():
    assert len(CLAIMS) >= 12 and len(BY_ID) == len(CLAIMS), "each id once"
    for claim in CLAIMS:
        assert claim.says and claim.quantities and claim.seconds > 0, claim.id
        assert (ROOT / 'docs' / 'adr' / claim.adr).exists(), (claim.id, claim.adr)
        file, _, name = claim.test.partition('::')
        source = (ROOT / 'tests' / file).read_text(encoding='utf-8')
        assert name and re.search(rf'^def {re.escape(name)}\(', source, re.M), (claim.id, claim.test)
        assert len({q.name for q in claim.quantities}) == len(claim.quantities), claim.id
    assert [c.id for c in CLAIMS if c.flaw] == ['curb', 'slope-creep'], "the flaws it lists are listed as such"
    assert sum(c.seconds for c in CLAIMS if c.quick) < 40 < sum(c.seconds for c in CLAIMS) < 300


def test_a_number_holds_within_its_tolerance_and_a_word_only_when_it_is_the_same():
    seconds = Quantity('cube in the bin at', 36.87, 1., 's')
    assert seconds.holds(36.87) and seconds.holds(37.8) and not seconds.holds(38.0)
    assert not seconds.holds(None), "a goal not reached does not hold"
    assert seconds.show(36.868) == '36.87 s' and seconds.show(None) == 'not reached'
    met = Quantity('every goal met', True)
    assert met.holds(True) and not met.holds(False) and met.show(True) == 'yes'
    why = Quantity('why', 'felt it')
    assert why.holds('felt it') and not why.holds('timed out on it')
    count = Quantity('looked again', 0)
    assert count.holds(0) and not count.holds(1)


def test_a_check_prints_each_number_beside_its_record_and_counts_what_holds():
    made = Claim('made-up', 'A made-up claim.', '0036-paired-runs.md', 'test_paired_runs.py::test_x',
                 (Quantity('time', 2.0, .5, 's'), Quantity('upright', True)), lambda: {'time': 2.4, 'upright': False}, 1)
    out = io.StringIO()
    results = evidence.check([made], out)
    said = out.getvalue()
    assert 'recorded 2 s' in said and 'here 2.4 s' in said and 'holds (within 0.5 s)' in said
    assert re.search(r'upright\s+recorded yes\s+here no\s+DIFFERS', said)
    assert evidence.summary(results) == (1, 2)

    def cannot():
        raise RuntimeError('no such field')
    out = io.StringIO()
    results = evidence.check([Claim('broken', 'Cannot run.', '0036-paired-runs.md', 't.py::t', (Quantity('x', 1., .1),), cannot, 1)], out)
    assert 'could not be measured' in out.getvalue() and 'RuntimeError: no such field' in out.getvalue()
    assert evidence.summary(results) == (0, 1), "a claim that cannot be measured does not hold"


def test_the_evidence_page_is_what_the_registry_writes():
    page = (ROOT / 'docs' / 'EVIDENCE.md').read_text(encoding='utf-8')
    assert page == evidence.markdown() + '\n', 'run  little-world evidence --markdown > docs/EVIDENCE.md'
    assert all(f'## `{c.id}`' in page for c in CLAIMS)


def test_the_command_lists_and_refuses_and_measures_the_quickest_claim(capsys, tmp_path):
    assert evidence.main(['--list']) == 0
    listed = capsys.readouterr().out
    assert all(c.id in listed for c in CLAIMS)
    with pytest.raises(SystemExit):
        evidence.main(['--only', 'no-such-claim'])
    capsys.readouterr()
    pytest.importorskip('mujoco')
    report = tmp_path / 'mine.json'
    assert evidence.main(['--only', 'pick-place', 'slope-creep', '--json', str(report)]) == 0
    said = capsys.readouterr().out
    assert '4 of 4 measurements hold here' in said and 'A known flaw, recorded as it is' in said
    import json
    written = json.loads(report.read_text(encoding='utf-8'))
    assert written['held'] == written['total'] == 4 and [c['id'] for c in written['claims']] == ['pick-place', 'slope-creep']
    assert written['claims'][0]['measured']['cube lifted at'] == pytest.approx(1.902, abs=.2)


def test_the_slow_list_names_tests_that_exist_and_is_read_back():
    times = script('test_times')
    listed = times.read()
    assert 40 < len(listed) < 120 and all(seconds >= times.SLOW for seconds in listed.values())
    for name in listed:
        file, _, test = name.partition('::')
        source = (ROOT / 'tests' / file).read_text(encoding='utf-8')
        assert re.search(rf'^def {re.escape(test.split("[")[0])}\(', source, re.M), f'{name}: listed in tests/slow.txt, not in the suite'
    assert 'test_felt_reach.py::test_the_cube_moved_under_a_jaw_is_felt_at_once_and_not_pressed_for_two_seconds' in listed
    assert 'test_evidence.py::test_a_number_holds_within_its_tolerance_and_a_word_only_when_it_is_the_same' not in listed


def test_the_quick_tier_leaves_out_what_is_listed_slow_and_every_window_test(request):
    """Collected here, as pytest collected this run: the marks tests/conftest.py gives."""
    items = request.session.items
    slow = {f'{Path(str(i.fspath)).name}::{i.name}' for i in items if i.get_closest_marker('slow')}
    window = {f'{Path(str(i.fspath)).name}::{i.name}' for i in items if i.get_closest_marker('window')}
    listed = set(script('test_times').read())
    ran = {f'{Path(str(i.fspath)).name}::{i.name}' for i in items}
    assert listed & ran <= slow, "what tests/slow.txt lists is marked slow"
    assert window <= slow, "a window test is never in the quick tier"
    if 'test_whats_new.py::test_one_click_from_the_top_bar_the_cube_moved_after_the_look_is_looked_for_again_and_fetched' in ran:
        assert 'test_whats_new.py::test_one_click_from_the_top_bar_the_cube_moved_after_the_look_is_looked_for_again_and_fetched' in window


def test_every_relative_link_in_the_documents_leads_to_a_file(tmp_path):
    links = script('check_links')
    pages = links.pages()
    assert ROOT / 'README.md' in pages and ROOT / 'docs' / 'EVIDENCE.md' in pages and len(pages) > 100
    found = [(str(page.relative_to(ROOT)), number, target) for page in pages for number, target in links.broken(page)]
    assert not found, found[:10]
    page = tmp_path / 'page.md'
    page.write_text('[there](page.md) [gone](nowhere.md) [web](https://example.org/x.md) [here](#top)\n'
                    '```\n[in code](also-nowhere.md)\n```\n<img src="missing.png">\n', encoding='utf-8')
    assert links.broken(page, tmp_path) == [(1, 'nowhere.md'), (5, 'missing.png')]


def test_the_readme_is_short_and_starts_someone_in_three_commands():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert len(readme.splitlines()) < 200, "the long lists live in docs/FEATURES.md and docs/MANUAL.md"
    start = readme.index('## Try it')
    block = readme[start:readme.index('```', readme.index('```sh', start) + 5)]
    commands = [line for line in block.splitlines() if line and not line.startswith(('#', '`')) and not line[0].isupper()]
    assert len(commands) == 3 and commands[-1].endswith('little-world'), commands
    for needed in ('little-world doctor', 'little-world evidence', 'docs/EVALUATION.md', 'docs/FEATURES.md', 'docs/MANUAL.md',
                   'docs/TROUBLESHOOTING.md', 'pytest -q -m "not slow"'):
        assert needed in readme, needed
