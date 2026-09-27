"""The digest: a week's arrivals as a short Markdown page, filed under what they could
change, ending in a triage to fill in.

Sections: the decisions an item could change, the roadmap's next steps, what to learn,
the simulator's own changes since the pinned version, what has much attention but no
topic here - the frontier the profile does not yet know about - and the triage.
"""
from collections import Counter, defaultdict

from .items import version_key

PER_TOPIC = 5
UNIT = {'paper': 'upvotes', 'repo': 'stars', 'model': 'likes'}


def _attention(item):
    unit = UNIT.get(item.kind)
    return f', {item.attention:,.0f} {unit}' if unit and item.attention else ''


def _line(m, verdicts):
    item = m.item
    title = item.title.replace('[', '(').replace(']', ')')
    link = f'[{title}]({item.url})' if item.url else title
    date = f', {item.published}' if item.published else ''
    also = f' · also {m.second.id}' if m.second is not None else ''
    words = f'*{", ".join(m.words)}*' if m.words else 'no words'
    judged = ''
    if item.id in verdicts:
        verdict, note, _ = verdicts[item.id]
        judged = f' · **{verdict}**' + (f': {note}' if note else '')
    return f'- {link} - {item.source}{date}{_attention(item)} · {words} ({m.score:.2f}){also}{judged}'


def _heading(topic):
    return f'{topic.id}: {topic.title}' if topic.kind == 'decision' else f'{topic.kind.title()}: {topic.title}'


def _grouped(matches, kind, verdicts):
    by_topic = defaultdict(list)
    for m in matches:
        if m.topic is not None and m.topic.kind == kind and m.item.kind != 'change':
            by_topic[m.topic.id].append(m)
    lines = []
    for topic_id, found in sorted(by_topic.items(), key=lambda kv: -kv[1][0].score):
        topic = found[0].topic
        lines.append(f'\n### {topic.id}: {topic.title}' if kind == 'decision' else f'\n### {topic.title}')
        lines.extend(_line(m, verdicts) for m in found[:PER_TOPIC])
        if len(found) > PER_TOPIC:
            lines.append(f'- and {len(found) - PER_TOPIC} more')
    return lines


def _changes(matches, pinned, verdicts):
    changes = [m for m in matches if m.item.kind == 'change']
    if not changes:
        return []
    versions = sorted({m.item.id.split(':', 1)[1].split('#')[0] for m in changes}, key=version_key)
    lines = [f'\n## Under the simulator: MuJoCo {pinned or "?"} -> {versions[-1]}',
             f'{len(changes)} changes in {len(versions)} releases; '
             f'{sum(1 for m in changes if m.topic is not None)} touch a topic here.']
    by_topic = defaultdict(list)
    for m in changes:
        if m.topic is not None:
            by_topic[m.topic.id].append(m)
    for topic_id, found in sorted(by_topic.items(), key=lambda kv: -kv[1][0].score):
        lines.append(f'\n### {_heading(found[0].topic)}')
        lines.extend(_line(m, verdicts) for m in found[:PER_TOPIC])
        if len(found) > PER_TOPIC:
            lines.append(f'- and {len(found) - PER_TOPIC} more')
    rest = Counter(m.item.tags[0] if m.item.tags else 'other' for m in changes if m.topic is None)
    if rest:
        lines.append('\nNo topic: ' + ', '.join(f'{n} {section}' for section, n in rest.most_common()) + '.')
    return lines


def digest(matches, verdicts, day, since, pinned=None, popular=8, triage=15):
    """The Markdown page for items first seen since `since`, as of `day`."""
    matched = [m for m in matches if m.topic is not None]
    sources = Counter(s for m in matches for s in m.item.source.split('+'))
    lines = [f'# Frontier radar, {day}', '',
             f'{len(matches)} items first seen since {since} '
             f'({", ".join(f"{n} {s}" for s, n in sources.most_common())}); {len(matched)} match a topic here. '
             'Each line: source, date, attention, the words that matched and the cosine score.']
    for title, kind in (('Decisions it could change', 'decision'), ('Next on the roadmap', 'next'),
                        ('To learn', 'learn')):
        found = _grouped(matches, kind, verdicts)
        if found:
            lines += ['', f'## {title}', *found]
    lines += _changes(matches, pinned, verdicts)
    loud = sorted((m for m in matches if m.topic is None and m.item.attention > 0),
                  key=lambda m: -m.item.attention)[:popular]
    if loud:
        lines += ['', '## Much attention, no topic here',
                  'What others are looking at that none of the topics asks for: a gap in the profile, or noise.']
        for m in loud:
            item = m.item
            lines.append(f'- [{item.title}]({item.url}) - {item.source}{_attention(item)}')
    open_items = [m for m in matched if m.item.id not in verdicts and m.item.kind != 'change'][:triage]
    if open_items:
        lines += ['', '## Triage',
                  'adopt: change the project · learn: study it · watch: look again later · skip. Record with '
                  '`python -m little_world.radar rate <id> <verdict> "<why>"`.']
        lines.extend(f'- [ ] `{m.item.id}` {m.item.title}' for m in open_items)
    return '\n'.join(lines) + '\n'
