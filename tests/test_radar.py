"""Contracts for the frontier radar (ADR 0021).

Every document here is invented - titles, abstracts, names - in the shape of the real
feeds, so the parsers are tested without the network and nothing third-party is copied.
"""
from datetime import date
import io
import json

import pytest

from little_world.radar.fetch import Source, fetch, pinned_mujoco, request, sources
from little_world.radar.items import (Item, arxiv_api, arxiv_rss, github_releases, github_search, hf_models,
                                      hf_papers, jsonl, mujoco_changelog)
from little_world.radar.profile import project_root, read_profile, topics
from little_world.radar.score import match, stem, words
from little_world.radar.store import Store

RSS = '''<?xml version='1.0' encoding='UTF-8'?>
<rss xmlns:arxiv="http://arxiv.org/schemas/atom" xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
  <channel>
    <title>cs.RO updates on arXiv.org</title>
    <item>
      <title>Creep-Free Grasps under Soft Contact</title>
      <link>https://arxiv.org/abs/2609.00001</link>
      <description>arXiv:2609.00001v1 Announce Type: new
Abstract: Soft contact models let a grasped object slip slowly under a sustained load, even well inside
the friction cone. We remove the creep with a post-solve projection and measure grasp slip.</description>
      <guid isPermaLink="false">oai:arXiv.org:2609.00001v1</guid>
      <category>cs.RO</category>
      <pubDate>Fri, 25 Sep 2026 00:00:00 -0400</pubDate>
      <arxiv:announce_type>new</arxiv:announce_type>
      <dc:creator>A. Walker, B. Stone</dc:creator>
    </item>
    <item>
      <title>Tip-Over Margins for Mobile Manipulators on Side Slopes</title>
      <link>https://arxiv.org/abs/2609.00002</link>
      <description>arXiv:2609.00002v1 Announce Type: cross
Abstract: A mobile manipulator's static stability depends on its center of mass and support polygon.</description>
      <guid isPermaLink="false">oai:arXiv.org:2609.00002v1</guid>
      <category>cs.RO</category>
      <pubDate>Fri, 25 Sep 2026 00:00:00 -0400</pubDate>
      <arxiv:announce_type>cross</arxiv:announce_type>
    </item>
    <item>
      <title>An Older Paper, Revised</title>
      <link>https://arxiv.org/abs/2601.00003</link>
      <description>arXiv:2601.00003v3 Announce Type: replace
Abstract: Not new.</description>
      <guid isPermaLink="false">oai:arXiv.org:2601.00003v3</guid>
      <arxiv:announce_type>replace</arxiv:announce_type>
    </item>
  </channel>
</rss>'''

ATOM = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>arXiv Query</title>
  <entry>
    <id>http://arxiv.org/abs/2609.00004v2</id>
    <published>2026-09-24T17:59:59Z</published>
    <title>A Conveyor Belt as a Moving Contact Surface</title>
    <summary>  We simulate conveyor belts by giving a surface a velocity field
      seen by contacts, with no extra joints.  </summary>
    <author><name>C. Rivers</name></author>
    <link href="http://arxiv.org/abs/2609.00004v2" rel="alternate" type="text/html"/>
    <category term="cs.RO"/>
  </entry>
</feed>'''

HF_PAPERS = json.dumps([
    {'paper': {'id': '2609.00001', 'title': 'Creep-Free Grasps under Soft Contact', 'upvotes': 41,
               'summary': 'Soft contact models let a grasped object slip slowly under a sustained load, even well '
                          'inside the friction cone. We remove the creep with a post-solve projection, measure '
                          'grasp slip on four hands and release the code.',
               'publishedAt': '2026-09-25T02:00:00.000Z', 'githubRepo': 'https://github.com/example/creepfree'},
     'numComments': 3},
    {'paper': {'id': '2609.00005', 'title': 'A Giant Video World Model', 'upvotes': 250,
               'summary': 'Scaling video prediction to trillions of frames.', 'publishedAt': '2026-09-25T02:00:00Z'}},
])
HF_MODELS = json.dumps([{'id': 'example-org/tiny-vla', 'likes': 320, 'downloads': 9000, 'pipeline_tag': 'robotics',
                         'library_name': 'lerobot', 'tags': ['lerobot', 'robotics', 'vla', 'license:apache-2.0'],
                         'createdAt': '2026-09-20T10:00:00.000Z'}])
GITHUB = json.dumps({'total_count': 1, 'items': [
    {'full_name': 'example/mujoco-conveyor', 'html_url': 'https://github.com/example/mujoco-conveyor',
     'description': 'Conveyor belts and part feeders for MuJoCo scenes', 'stargazers_count': 1234,
     'created_at': '2026-09-02T08:00:00Z', 'topics': ['mujoco', 'conveyor', 'simulation']}]})
RELEASES = json.dumps([
    {'tag_name': 'v0.7.0', 'name': 'v0.7.0', 'html_url': 'https://github.com/example/lerobot-like/releases/v0.7.0',
     'published_at': '2026-09-21T00:00:00Z', 'body': '## Highlights\n- New policy\n- Faster datasets', 'draft': False},
    {'tag_name': 'v0.8.0-draft', 'draft': True}])
CHANGELOG = '''=========
Changelog
=========

Upcoming version (not yet released)
-----------------------------------

General
^^^^^^^
- Something not released yet.

Version 3.4.0 (December 5, 2025)
--------------------------------

General
^^^^^^^
- Added the :ref:`surfacevel <body-geom-surfacevel>` attribute: a geom's surface moves as seen by
  contacts, a conveyor belt without extra joints.

  - A nested detail belongs to its entry.
- Changed ``noslip`` iterations to also cover elliptic friction cones.

Bug fixes
^^^^^^^^^
1. :commit:`abc1234` Fixed a crash when a model has no bodies (:issue:`42`).

.. youtube:: abcdef
   :align: right

Actuation
^^^^^^^^^
.. admonition:: Breaking API changes
   :class: attention

   .. image:: https://example.com/picture.gif
      :width: 40%

   4. :commit:`def5678` The :ref:`pid<actuator-pid>` gains are now in torque space.

5. Added a :ref:`dcmotor<actuator-dcmotor>` preset.

   .. admonition:: Breaking API changes
      :class: attention

      Its default input changed.

Version 3.3.7 (October 1, 2025)
-------------------------------

General
^^^^^^^
- A change the project already has.
'''


# -- parsers ---------------------------------------------------------------------------------

def test_arxiv_listing_keeps_new_and_cross_listed_papers_not_replacements():
    found = arxiv_rss(RSS)
    assert [i.id for i in found] == ['arxiv:2609.00001', 'arxiv:2609.00002']
    first = found[0]
    assert first.title == 'Creep-Free Grasps under Soft Contact' and first.published == '2026-09-25'
    assert first.summary.startswith('Soft contact models') and 'Announce' not in first.summary
    assert first.url == 'https://arxiv.org/abs/2609.00001' and first.tags == ('cs.RO',)


def test_arxiv_query_entries_lose_their_version_and_whitespace():
    (item,) = arxiv_api(ATOM)
    assert item.id == 'arxiv:2609.00004' and item.published == '2026-09-24'
    assert item.summary == 'We simulate conveyor belts by giving a surface a velocity field seen by contacts, with no extra joints.'


def test_models_repos_and_releases_carry_their_attention():
    (paper, loud) = hf_papers(HF_PAPERS)
    assert paper.id == 'arxiv:2609.00001' and paper.attention == 41 and 'code:https://github.com/example/creepfree' in paper.tags
    (model,) = hf_models(HF_MODELS)
    assert model.id == 'hf-model:example-org/tiny-vla' and model.kind == 'model' and model.attention == 320
    assert 'license:apache-2.0' not in model.tags and 'lerobot' in model.summary
    (repo,) = github_search(GITHUB)
    assert repo.id == 'github:example/mujoco-conveyor' and repo.attention == 1234 and 'part feeders' in repo.summary
    (release,) = github_releases(RELEASES, 'example/lerobot-like')
    assert release.id == 'release:example/lerobot-like@v0.7.0' and release.kind == 'release'


def test_the_changelog_gives_the_entries_newer_than_the_pinned_version():
    found = mujoco_changelog(CHANGELOG, since='3.3.7')
    assert [i.id for i in found] == [f'mujoco:3.4.0#{n}' for n in range(1, 6)]
    surface, noslip, fix, gains, preset = found
    assert surface.summary.startswith('Added the surfacevel attribute: a geom') and 'nested detail' in surface.summary
    assert surface.title == ('MuJoCo 3.4.0: Added the surfacevel attribute: a geom\'s surface moves as seen by contacts, '
                             'a conveyor belt without extra joints.') and surface.published == '2025-12-05'
    assert noslip.summary == 'Changed noslip iterations to also cover elliptic friction cones.'
    assert surface.tags == ('General',) and fix.tags == ('Bug fixes',)
    assert fix.summary == 'Fixed a crash when a model has no bodies (issue 42).'     # no commit hash, no video
    assert gains.tags == ('Actuation', 'breaking') and gains.summary == 'The pid gains are now in torque space.'
    assert preset.tags == ('Actuation', 'breaking') and preset.summary.endswith('Its default input changed.')
    assert len(mujoco_changelog(CHANGELOG, since='3.2.0')) == 6


def test_gathered_items_are_checked_line_by_line():
    (item,) = jsonl('{"id": "web:example", "title": "A page", "kind": "repo", "attention": 5}\n\n')
    assert item.source == 'gathered' and item.attention == 5. and item.kind == 'repo'
    with pytest.raises(ValueError, match='line 1'):
        jsonl('{"id": "x", "title": "y", "colour": "red"}')
    with pytest.raises(ValueError, match='kind'):
        jsonl('{"id": "x", "title": "y", "kind": "rumour"}')


# -- scoring -------------------------------------------------------------------------------------

def test_stems_join_the_forms_papers_use():
    assert stem('manipulation') == stem('manipulators') == stem('manipulating') == 'manipul'
    assert stem('slipping') == stem('slips') == 'slip' and stem('policies') == 'policy'
    assert stem('simulated') == stem('simulation') == stem('simulator')
    assert stem('glass') == 'glass' and stem('rolling') == 'roll'
    assert [w for _, w in words('We propose a novel grasp-slip model, e.g. for 2 hands.')] == ['grasp', 'slip', 'model', 'hands']


def test_items_are_filed_under_the_decision_they_touch_with_the_words_that_matched():
    everything = topics()
    ids = {t.id for t in everything}
    assert {'ADR 0014', 'ADR 0017', 'Next: conveyor and feeder', 'Learn: robot learning'} <= ids
    found = {m.item.id: m for m in match(arxiv_rss(RSS) + arxiv_api(ATOM) + [
        Item('arxiv:2609.00009', 'arxiv', 'Protein Folding with Language Models',
             'We fold proteins with a large language model trained on sequences.')], everything)}
    assert found['arxiv:2609.00001'].topic.id == 'ADR 0017'
    assert {'friction cone', 'creep'} & set(found['arxiv:2609.00001'].words)
    assert found['arxiv:2609.00002'].topic.id == 'ADR 0015'
    assert found['arxiv:2609.00004'].topic.id == 'Next: conveyor and feeder'
    assert found['arxiv:2609.00009'].topic is None


def test_the_robot_models_the_app_imports_are_watched_under_the_decision_that_uses_them():
    """MuJoCo Menagerie is where the registered arms come from; its first run had much
    attention and no topic (OPEN LW-013). It files under the robots' tool moves (ADR 0019)."""
    found = match([Item('github:google-deepmind/mujoco_menagerie', 'github', 'mujoco_menagerie',
                        'A collection of high-quality models for the MuJoCo physics engine, curated by '
                        'Google DeepMind: Franka Panda, Kinova Gen3, Universal Robots UR5e and more.', kind='repo'),
                   Item('github:x/fr3', 'github', 'Franka FR3 model update in MuJoCo Menagerie',
                        'New collision meshes and actuator gains for the Franka FR3 arm model.', kind='release')],
                  topics())
    assert [m.topic.id for m in found] == ['ADR 0019', 'ADR 0019']
    assert 'menagerie' in found[0].words


def test_the_profile_reads_topics_and_refuses_a_heading_it_does_not_know(tmp_path):
    assert read_profile('# x\n## ADR 0001\nwords here\n> a note\n## Learn: a\n- b\n') == \
        [('ADR 0001', 'words here'), ('Learn: a', 'b')]
    (tmp_path / 'docs' / 'adr').mkdir(parents=True)
    (tmp_path / 'docs' / 'adr' / '0001-first.md').write_text('# First\n\nThe problem.\n')
    (tmp_path / 'docs' / 'radar').mkdir()
    (tmp_path / 'docs' / 'radar' / 'profile.md').write_text('## Someday: maybe\nwords\n')
    with pytest.raises(ValueError, match='Someday'):
        topics(tmp_path)
    (tmp_path / 'docs' / 'radar' / 'profile.md').write_text('## ADR 0002\nwords\n')
    with pytest.raises(ValueError, match='no decision record'):
        topics(tmp_path)
    (tmp_path / 'docs' / 'radar' / 'profile.md').write_text('## ADR 0001\nextra words\n## Next: soon\nplans\n')
    first, soon = topics(tmp_path)
    assert first.id == 'ADR 0001' and 'extra words' in first.text and soon.kind == 'next'
    assert project_root(tmp_path / 'docs') == tmp_path


# -- the store and the digest ----------------------------------------------------------------------

def test_the_same_paper_from_two_feeds_is_one_item_seen_once():
    with Store(':memory:') as store:
        assert store.add(arxiv_rss(RSS), seen='2026-09-25') == 2
        assert store.add(hf_papers(HF_PAPERS), seen='2026-09-26') == 1
        paper = next(i for i in store.items() if i.id == 'arxiv:2609.00001')
        assert paper.source == 'arxiv+hf-papers' and paper.attention == 41
        assert paper.summary.endswith('release the code.')            # the longer summary
        assert 'code:https://github.com/example/creepfree' in paper.tags
        assert [i.id for i in store.items('2026-09-26')] == ['arxiv:2609.00005']
        store.rate('arxiv:2609.00001', 'adopt', 'ADR 0017 cites it')
        assert store.verdicts()['arxiv:2609.00001'][:2] == ('adopt', 'ADR 0017 cites it')
        with pytest.raises(ValueError):
            store.rate('arxiv:2609.00001', 'love')
        with pytest.raises(KeyError):
            store.rate('arxiv:2609.99999', 'skip')


def digest_of(found, rated=()):
    from little_world.radar.digest import plan
    with Store(':memory:') as store:
        store.add(found)
        for item_id, verdict, note in rated:
            store.rate(item_id, verdict, note)
        return plan(match(store.items(), topics()), store.verdicts(), '2026-09-27', '2026-09-20', '3.3.7')


def test_the_digest_files_items_by_topic_leads_with_verdicts_and_leaves_the_rest_to_judge():
    from little_world.radar.digest import markdown
    found = arxiv_rss(RSS) + hf_papers(HF_PAPERS) + github_search(GITHUB) + mujoco_changelog(CHANGELOG, '3.3.7')
    d = digest_of(found, [('arxiv:2609.00002', 'learn', 'how a tilt table is predicted')])
    page = markdown(d)
    assert page.startswith('# Frontier radar · 2026-09-27')
    assert '9 new since 2026-09-20: ' in page and '1 judged (1 learn)' in page
    assert '### ADR 0017 · Friction that holds' in page
    assert '- **learn** [Tip-Over Margins' in page and 'how a tilt table is predicted' in page   # the reason, not the words
    assert '## Under the simulator: MuJoCo 3.3.7 → 3.4.0' in page and '5 changes in 1 releases, 2 breaking' in page
    assert '## Much attention, no topic here' in page and 'A Giant Video World Model' in page and '250 upvotes' in page
    judge = page.split('## To judge', 1)[1]
    assert '`arxiv:2609.00001`' in judge and 'arxiv:2609.00002' not in judge
    (release,) = d.releases
    assert (release.version, release.changes, release.breaking) == ('3.4.0', 5, 2)


def test_the_page_shows_the_same_digest_and_trusts_nothing_it_was_fed():
    """Titles, summaries and links come from feeds: all of it is escaped, and only http(s)
    addresses become links."""
    from little_world.radar.page import html
    hostile = Item('web:x', 'gathered', 'Grasp slip <script>alert(1)</script> and creep',
                   'friction cone creep grasp slip under soft contact "quoted"', 'javascript:alert(1)')
    d = digest_of(arxiv_rss(RSS) + mujoco_changelog(CHANGELOG, '3.3.7') + [hostile],
                  [('arxiv:2609.00001', 'adopt', 'noslip <b>already</b> does this')])
    page = html(d)
    assert page.startswith('<!doctype html>') and '<title>Frontier radar</title>' in page
    assert '<script>alert(1)</script>' not in page and '&lt;script&gt;alert(1)&lt;/script&gt;' in page
    assert 'javascript:' not in page and '&lt;b&gt;already&lt;/b&gt;' in page
    assert page.count('data-verdict="adopt"') == 1 and 'data-show="open"' in page
    assert 'MuJoCo 3.3.7 → 3.4.0' in page and page.count('class="brk"') == 2     # one bar, one legend key
    fragment = html(d, fragment=True)
    assert not fragment.startswith('<!doctype') and '<body>' not in fragment and '<title>' in fragment


# -- fetching and the command line -----------------------------------------------------------------

def test_fetching_reads_every_feed_and_reports_the_one_that_failed():
    asked = []

    def get(url):
        asked.append(url)
        if 'daily_papers' in url:
            return HF_PAPERS
        if 'rss.arxiv.org' in url:
            return RSS
        raise OSError('HTTP Error 503')
    feeds = (Source('arXiv', 'https://rss.arxiv.org/rss/cs.RO', lambda t, d: arxiv_rss(t), 3.),
             Source('HF', 'https://huggingface.co/api/daily_papers?date={day}', lambda t, d: hf_papers(t), daily=True),
             Source('GitHub', 'https://api.github.com/search/repositories?q=pushed:>={since}', lambda t, d: []))
    pauses = []
    found, report = fetch(feeds, date(2026, 9, 25), date(2026, 9, 27), get, pauses.append)
    assert len(found) == 2 + 3 * 2
    assert [u for u in asked if 'daily' in u][-1].endswith('date=2026-09-27') and len(asked) == 5
    assert asked[-1].endswith('pushed:>=2026-09-25')
    assert report[0] == 'arXiv: 2 items' and report[2].startswith('GitHub: 0 items; failed 1x - OSError')
    assert pauses[0] == 3.


def test_the_feeds_are_polite_and_a_token_goes_to_github_only():
    assert pinned_mujoco(project_root()) == '3.3.7'
    names = [s.name for s in sources('3.3.7')]
    assert 'arXiv cs.RO' in names and 'MuJoCo changelog' in names
    github = request('https://api.github.com/search/repositories?q=x', {'GITHUB_TOKEN': 'abc'})
    arxiv = request('https://rss.arxiv.org/rss/cs.RO', {'GITHUB_TOKEN': 'abc'})
    assert github.get_header('Authorization') == 'Bearer abc' and arxiv.get_header('Authorization') is None
    assert 'little-world-radar' in arxiv.get_header('User-agent')


def test_the_command_line_ingests_digests_and_rates(tmp_path):
    from little_world.radar.__main__ import main
    db, gathered, page = tmp_path / 'r.sqlite', tmp_path / 'g.jsonl', tmp_path / 'digest.md'
    gathered.write_text(json.dumps({'id': 'web:grip', 'title': 'Grasp slip and creep under soft contact',
                                    'summary': 'friction cone creep grasp slip', 'kind': 'paper'}) + '\n')
    out = io.StringIO()
    assert main(['--db', str(db), 'ingest', str(gathered)], out) == 0
    assert main(['--db', str(db), 'digest', '--out', str(page), '--html', str(tmp_path / 'digest.html')], out) == 0
    assert main(['--db', str(db), 'rate', 'web:grip', 'watch', 'too', 'early'], out) == 0
    assert main(['--db', str(db), 'topics'], out) == 0
    text = out.getvalue()
    assert '1 new of 1 items' in text and 'web:grip: watch' in text and 'ADR 0017' in text
    assert 'Grasp slip and creep' in page.read_text()
    assert 'Grasp slip and creep' in (tmp_path / 'digest.html').read_text()
