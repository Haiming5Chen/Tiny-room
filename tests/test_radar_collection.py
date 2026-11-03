"""The radar's collection and its search (ADR 0034): what was read and judged stays in the
repository, merges when two agents add the same paper, keeps no publisher's abstract, comes
back into a fresh store, and can be searched by words - and by a latent space, when asked."""
import json
from pathlib import Path

import pytest

from little_world.radar import collection
from little_world.radar.__main__ import main
from little_world.radar.items import Item
from little_world.radar.search import LATENT, Index, about, background, check
from little_world.radar.store import VERDICTS, Store

ROOT = Path(__file__).resolve().parents[1]


def line(**fields):
    return json.dumps({'id': 'arxiv:2609.00001', 'title': 'A paper', **fields})


def test_an_entry_survives_the_file_and_two_sightings_merge_into_one():
    first = line(source='arxiv', summary='short', seen='2026-10-05', verdict='watch', note='later', rated='2026-10-05',
                 filed=['ADR 0032'], tags=['cs.RO'], read='title')
    second = line(source='hf-papers', summary='a longer summary of the same paper', seen='2026-10-07',
                  verdict='adopt', note='now', rated='2026-10-07', filed=['ADR 0033'], attention=12, read='abstract')
    [e] = collection.parse(f'{first}\n{second}\n')
    assert e.item.source == 'arxiv+hf-papers' and e.item.summary == 'a longer summary of the same paper'
    assert (e.seen, e.verdict, e.note, e.rated, e.read) == ('2026-10-05', 'adopt', 'now', '2026-10-07', 'abstract')
    assert e.filed == ('ADR 0032', 'ADR 0033') and e.item.tags == ('cs.RO',) and e.item.attention == 12.
    assert collection.parse(collection.dumps([e])) == [e]
    older = collection.entry(json.loads(line(verdict='skip', rated='2026-09-01')))
    assert collection.merge(e, older).verdict == 'adopt', 'an older verdict does not replace a newer one'


def test_the_file_is_one_sorted_line_an_entry_and_bad_lines_are_refused_by_number():
    text = collection.dumps([collection.entry({'id': i, 'title': i}) for i in ('web:b', 'arxiv:2609.00002', 'journal:a')])
    assert [json.loads(row)['id'] for row in text.splitlines()] == ['arxiv:2609.00002', 'journal:a', 'web:b']
    for bad, said in ((line(verdict='maybe'), 'verdict'), (line(read='skimmed'), 'read'), (line(colour='red'), 'unknown'),
                      ('{"id": "x"}', 'needs id and title'), ('{', 'line 2')):
        with pytest.raises(ValueError, match=said):
            collection.parse(line() + '\n' + bad)


def test_a_journal_abstract_is_not_kept_and_a_long_summary_is_cut():
    [kept] = collection.parse(line(id='journal:10.1126/scirobotics.abc', source='journal', summary='the publisher\'s words'))
    assert kept.item.summary == ''
    [long] = collection.parse(line(summary='word ' * 1000))
    assert len(long.item.summary) <= collection.SUMMARY + 4 and long.item.summary.endswith(' ...')


def items():
    return [Item('arxiv:2609.00001', 'arxiv', 'Rolling resistance of rubber wheels on concrete floors',
                 'We measure the rolling resistance of rubber wheels and casters on concrete.'),
            Item('arxiv:2609.00002', 'arxiv', 'A survey of protein folding', 'Proteins fold.'),
            Item('arxiv:2609.00003', 'arxiv', 'Grasping cubes with a parallel gripper', 'Jaws close on a cube.')]


def test_collect_keeps_what_is_filed_or_judged_and_recall_brings_it_back(tmp_path):
    db, kept = tmp_path / 'radar.sqlite', tmp_path / 'collection.jsonl'
    with Store(db) as store:
        store.add(items(), seen='2026-10-05')
        store.rate('arxiv:2609.00003', 'learn', 'the jaws')
    with open(tmp_path / 'out', 'w') as out:
        assert main(['--db', str(db), '--root', str(ROOT), 'collect', '--file', str(kept)], out=out) == 0
    found = collection.read(kept)
    assert 'arxiv:2609.00002' not in found, 'neither filed nor judged'
    assert found['arxiv:2609.00001'].filed and found['arxiv:2609.00001'].seen == '2026-10-05'
    assert found['arxiv:2609.00003'].verdict == 'learn' and found['arxiv:2609.00003'].note == 'the jaws'
    with Store(tmp_path / 'fresh.sqlite') as fresh:
        assert collection.to_store(fresh, found.values()) == len(found)
        assert fresh.verdicts()['arxiv:2609.00003'][:2] == ('learn', 'the jaws')
        assert collection.to_store(fresh, found.values()) == 0, 'recalled twice, kept once'


def test_collect_merges_entries_gathered_by_hand_and_files_them(tmp_path):
    gathered, kept = tmp_path / 'found.jsonl', tmp_path / 'collection.jsonl'
    gathered.write_text(line(id='arxiv:2609.00009', title='Rolling resistance of caster wheels on concrete floors',
                             summary='rolling resistance, casters, concrete', verdict='learn', rated='2026-10-05') + '\n')
    args = ['--db', str(tmp_path / 'r.sqlite'), '--root', str(ROOT), 'collect', '--file', str(kept), '--add', str(gathered)]
    with open(tmp_path / 'out', 'w') as out:
        assert main(args, out=out) == 0 and main(args, out=out) == 0
    assert (tmp_path / 'out').read_text().splitlines() == [f'1 new, 0 changed; 1 entries in {kept}',
                                                           f'0 new, 0 changed; 1 entries in {kept}']
    [e] = collection.read(kept).values()
    assert e.verdict == 'learn' and e.filed, 'filed under a topic on the way in'


def entry(id, title, summary='', verdict=''):
    return collection.entry({'id': id, 'title': title, 'summary': summary, 'verdict': verdict})


def test_search_ranks_by_words_and_says_which_words_matched():
    index = Index([entry('a', 'Rolling resistance of rubber wheels', 'casters on concrete', 'adopt'),
                   entry('b', 'Protein folding'), entry('c', 'Wheels and casters for robots')])
    hits = index.ask('rolling resistance of wheels')
    assert [h.entry.id for h in hits] == ['a', 'c'] and 'rolling resistance' in hits[0].words
    assert hits[0].latent == 0. and hits[0].near == (), 'words alone unless the latent share is asked for'
    assert [h.entry.id for h in index.ask('wheels', verdicts={''})] == ['c']
    assert Index([]).ask('anything') == []


def test_the_latent_space_finds_an_entry_that_shares_no_word_with_the_question():
    """'grip' and 'grasp' never meet in an entry, but the project's writing uses them in the
    same company (jaws, cube, lifts); with as many latent directions as the writing has
    subjects, a question about gripping finds the grasping paper. One direction more and the
    space spends it on telling grip from grasp - the reason the number of directions matters."""
    writing = (['The gripper jaws grip the cube, and the arm lifts it while the jaws hold it.'] * 4 +
               ['The jaws grasp the cube, and the arm lifts it while the jaws hold it.'] * 4 +
               ['The wheels roll on the concrete floor; the casters roll behind the wheels.'] * 8)
    entries = [entry('grasp', 'Grasping a cube', 'the jaws grasp and lift'),
               entry('wheel', 'Wheel rolling resistance', 'casters on concrete floors roll')]
    assert Index(entries, writing).ask('grip', least=.01) == [], 'no word in common'
    [hit] = Index(entries, writing, dimensions=2).ask('grip', least=.01, latent=1.)
    assert hit.entry.id == 'grasp' and hit.lexical == 0. and hit.latent > .9 and 'jaws' in hit.near
    assert Index(entries, writing, dimensions=3).ask('grip', least=.01, latent=1.) == []


def test_the_check_counts_answers_in_the_top_three_for_words_and_for_the_latent_space():
    index = Index([entry(str(k), f'paper {k} about {topic}') for k, topic in
                   enumerate(('wheels', 'grasping', 'cameras', 'motors', 'conveyors'))])
    rows = check(index, [{'question': 'cameras', 'expect': ['2']}, {'question': 'nothing like it', 'expect': ['9']}],
                 (0., 1.))
    assert rows[0] == (0., 1, .5, [1, None])
    assert [share for share, *_ in rows] == [0., 1.]


def test_a_topic_or_a_proposal_can_be_the_question():
    assert 'Looking again' in about('FR-015', ROOT) and about('ADR 0032', ROOT)
    for unknown in ('FR-999', 'ADR 9999'):
        with pytest.raises(KeyError):
            about(unknown, ROOT)
    paragraphs = background(ROOT)
    assert len(paragraphs) > 100 and not any('radar:begin' in p for p in paragraphs)


def test_the_collection_in_the_repository_is_sorted_judged_public_and_merges_by_line():
    path = ROOT / collection.PATH
    rows = [json.loads(row) for row in path.read_text(encoding='utf-8').splitlines()]
    ids = [r['id'] for r in rows]
    assert len(rows) >= 80 and ids == sorted(set(ids))
    kept = collection.read(path)
    assert all(e.verdict in ('', *VERDICTS) and e.seen for e in kept.values())
    assert not any(e.item.summary for e in kept.values() if e.item.source == 'journal')
    assert collection.dumps(kept.values()) == path.read_text(encoding='utf-8'), 'written as dumps writes it'
    assert 'docs/radar/collection.jsonl merge=union' in (ROOT / '.gitattributes').read_text(encoding='utf-8')


def test_the_questions_with_known_answers_are_answerable_and_the_search_answers_most(tmp_path):
    """The measurement ADR 0034 reports, repeated: every expected entry is in the collection,
    and the search puts one in the top three for at least 15 of the 20 questions. Words alone
    did for 17 when it was written (81 entries), 16 at 134, 15 at 177 and 14 at 238, as more
    entries shared the questions' words (OPEN LW-027); words and meaning mixed equally - the
    command line's default since ADR 0062 - for 17 at 183 entries and 16 at 238."""
    questions = [json.loads(row) for row in (ROOT / 'docs' / 'radar' / 'queries.jsonl').read_text().splitlines()]
    kept = collection.read(ROOT / collection.PATH)
    assert len(questions) == 20 and all(e in kept for q in questions for e in q['expect'])
    [(_, top, mrr, _)] = check(Index(kept.values(), background(ROOT)), questions, (LATENT,))
    assert top >= 15 and mrr >= .65
    out = tmp_path / 'out'
    with open(out, 'w') as stream:
        assert main(['--root', str(ROOT), 'search', '--check'], out=stream) == 0
        assert main(['--root', str(ROOT), 'search', 'camera', 'stops', 'updating', '-n', '1'], out=stream) == 0
        assert main(['--root', str(ROOT), 'related', 'FR-016', '-n', '2', '--latent', '.5'], out=stream) == 0
    printed = out.read_text()
    assert 'words alone' in printed and 'latent alone' in printed and 'Blackout vs. Freeze' in printed
    with pytest.raises(SystemExit), open(tmp_path / 'err', 'w') as err:
        main(['--root', str(ROOT), 'search'], out=err)
