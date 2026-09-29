"""The digest: a week's arrivals filed under what they could change, ending in a triage.

`plan` sorts scored items into what a reader needs, in order: the decisions an item
could change, the roadmap's next steps, what to learn, the simulator's own changes since
the pinned version, what has much attention elsewhere but no topic here, and what is
still to judge. `markdown` writes it short, for a terminal or a pull request - verdicts
and their reasons first, three items a topic; `page.html` writes all of it as one page
that shows the same summary and opens the details on demand.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .items import version_key
from .store import VERDICTS

SHOWN = 3               # items per topic in the Markdown digest; the page shows them all
LOUD, TRIAGE = 8, 15
UNIT = {'paper': 'upvotes', 'repo': 'stars', 'model': 'likes'}
SECTIONS = (('decision', 'Decisions it could change'), ('next', 'Next on the roadmap'), ('learn', 'To learn'))
ORDER = {'adopt': 0, 'learn': 1, 'watch': 2, None: 3, 'skip': 4}    # reading order of verdicts


@dataclass(frozen=True)
class Entry:
    match: object           # score.Match
    verdict: str | None = None
    note: str = ''

    @property
    def item(self):
        return self.match.item


@dataclass
class Group:
    topic: object
    entries: list = field(default_factory=list)

    @property
    def heading(self):
        t = self.topic
        return f'{t.id} · {t.title}' if t.kind == 'decision' else f'{t.kind.title()}: {t.title}'


@dataclass(frozen=True)
class Release:
    version: str
    date: str
    changes: int
    breaking: int
    filed: int


@dataclass
class Digest:
    day: str
    since: str
    pinned: str | None
    total: int
    filed: int
    sources: Counter
    verdicts: Counter                                 # verdict -> items judged, among these
    sections: list = field(default_factory=list)       # (key, title, [Group])
    releases: list = field(default_factory=list)       # Release, oldest first
    changes: list = field(default_factory=list)        # [Group] of simulator changes with a topic
    unfiled_changes: Counter = field(default_factory=Counter)
    loud: list = field(default_factory=list)           # [Entry] with attention and no topic
    triage: list = field(default_factory=list)         # [Entry] filed and not yet judged


def attention(item):
    unit = UNIT.get(item.kind)
    return f'{item.attention:,.0f} {unit}' if unit and item.attention else ''


def _groups(entries):
    by_topic = defaultdict(list)
    for e in entries:
        by_topic[e.match.topic.id].append(e)
    groups = [Group(found[0].match.topic, found) for found in by_topic.values()]
    # What was adopted leads, what was skipped trails; within that, the best match first.
    for g in groups:
        g.entries.sort(key=lambda e: (ORDER[e.verdict], -e.match.score))
    return sorted(groups, key=lambda g: (min(ORDER[e.verdict] for e in g.entries), -g.entries[0].match.score))


def plan(matches, verdicts, day, since, pinned=None):
    """Everything a digest shows, in reading order."""
    entries = [Entry(m, *(verdicts[m.item.id][:2] if m.item.id in verdicts else (None, ''))) for m in matches]
    filed = [e for e in entries if e.match.topic is not None]
    d = Digest(day, since, pinned, len(entries), len(filed),
               Counter(s for e in entries for s in e.item.source.split('+')),
               Counter(e.verdict for e in entries if e.verdict))
    for key, title in SECTIONS:
        found = [e for e in filed if e.match.topic.kind == key and e.item.kind != 'change']
        if found:
            d.sections.append((key, title, _groups(found)))
    changes = [e for e in entries if e.item.kind == 'change']
    by_version = defaultdict(list)
    for e in changes:
        by_version[e.item.id.split(':', 1)[1].split('#')[0]].append(e)
    for version in sorted(by_version, key=version_key):
        found = by_version[version]
        d.releases.append(Release(version, found[0].item.published, len(found),
                                  sum('breaking' in e.item.tags for e in found),
                                  sum(e.match.topic is not None for e in found)))
    d.changes = _groups([e for e in changes if e.match.topic is not None])
    d.unfiled_changes = Counter(e.item.tags[0] if e.item.tags else 'other' for e in changes if e.match.topic is None)
    d.loud = sorted((e for e in entries if e.match.topic is None and e.item.attention > 0),
                    key=lambda e: -e.item.attention)[:LOUD]
    d.triage = [e for e in sorted(filed, key=lambda e: -e.match.score)
                if e.verdict is None and e.item.kind != 'change'][:TRIAGE]
    return d


# -- Markdown: short ------------------------------------------------------------------------

def _md_title(item):
    title = item.title.replace('[', '(').replace(']', ')')
    return f'[{title}]({item.url})' if item.url.startswith(('https://', 'http://')) else title


def _md_entry(e):
    verdict = f'**{e.verdict}** ' if e.verdict else ''
    why = e.note if e.verdict and e.note else ', '.join(e.match.words)
    return f'- {verdict}{_md_title(e.item)} · {why}'


def _md_groups(groups):
    lines = []
    for g in groups:
        lines += ['', f'### {g.heading}', *(_md_entry(e) for e in g.entries[:SHOWN])]
        if len(g.entries) > SHOWN:
            lines.append(f'- and {len(g.entries) - SHOWN} more on the page')
    return lines


def summary_line(d):
    judged = sum(d.verdicts.values())
    counts = ' · '.join(f'{d.verdicts[v]} {v}' for v in VERDICTS if d.verdicts[v])
    return (f'{d.total} new since {d.since}: {d.filed} filed under a topic, {judged} judged'
            + (f' ({counts})' if counts else '') + '.')


def markdown(d):
    """The digest as a short Markdown page: verdicts with their reasons first, then the
    words that matched; three items a topic."""
    lines = [f'# Frontier radar · {d.day}', '', summary_line(d)]
    for _key, title, groups in d.sections:
        lines += ['', f'## {title}', *_md_groups(groups)]
    if d.releases:
        changes = sum(r.changes for r in d.releases)
        breaking = sum(r.breaking for r in d.releases)
        lines += ['', f'## Under the simulator: MuJoCo {d.pinned or "?"} → {d.releases[-1].version}',
                  f'{changes} changes in {len(d.releases)} releases, {breaking} breaking; '
                  f'{sum(r.filed for r in d.releases)} touch a topic here.', *_md_groups(d.changes)]
        if d.unfiled_changes:
            lines += ['', 'No topic: ' + ', '.join(f'{n} {s}' for s, n in d.unfiled_changes.most_common()) + '.']
    if d.loud:
        lines += ['', '## Much attention, no topic here',
                  *(f'- {_md_title(e.item)} · {attention(e.item)}' for e in d.loud)]
    if d.triage:
        lines += ['', '## To judge', 'adopt · learn · watch · skip: `python -m little_world.radar rate <id> <verdict> "<why>"`',
                  *(f'- [ ] `{e.item.id}` {e.item.title}' for e in d.triage)]
    return '\n'.join(lines) + '\n'


def digest(matches, verdicts, day, since, pinned=None):
    """The Markdown digest of scored items (see `plan`)."""
    return markdown(plan(matches, verdicts, day, since, pinned))
