"""The radar's brief for agents (ADR 0026): what the frontier offered lately, filed under the
decisions it could change, written into `docs/agents/FRONTIER.md` between two markers.

The file is where filing becomes thinking: agents read the brief, and write proposals - how
an item could be adapted to Little World, how we would know it worked, what it costs - which
the owner decides on. Everything outside the markers is theirs and is never touched here.
Standard library only.
"""
from collections import Counter
from pathlib import Path
import re

BEGIN, END = '<!-- radar:begin -->', '<!-- radar:end -->'
STATUSES = ('proposed', 'accepted', 'doing', 'done', 'declined')
FIELDS = ('Status', 'From', 'Idea', 'In Little World', 'How we would know', 'Cost and needs')
_ORDER = {'adopt': 0, 'learn': 1, 'watch': 2, None: 3, 'skip': 4}
_HEAD = re.compile(r'^### (FR-\d{3}) · (.+)$', re.M)


def proposals(text):
    """[(id, title, status, body)] for each '### FR-nnn · title' section of the frontier file,
    in order. `status` is the first word after '- Status:'; `body` ends at the next proposal,
    the next '## ' heading or the generated section."""
    found = []
    heads = list(_HEAD.finditer(text))
    for k, head in enumerate(heads):
        body = text[head.end():heads[k + 1].start() if k + 1 < len(heads) else len(text)]
        stops = [i for i in (body.find('\n## '), body.find(BEGIN)) if i >= 0]
        body = body[:min(stops)] if stops else body
        status = re.search(r'^- Status: (\w+)', body, re.M)
        found.append((head.group(1), head.group(2).strip(), status.group(1) if status else '', body))
    return found


def cited(item, found, shared=frozenset()):
    """The proposals that name an item: by its id (`arxiv:2510.13626`, or the part after the
    colon, as in an arXiv link), or by its link unless other items share it (MuJoCo's
    changelog entries all point at one page). An id is matched whole: `3.7.0#1` is not
    named by `3.7.0#13`."""
    keys = [item.id.split(':', 1)[-1]] + ([item.url] if item.url and item.url not in shared else [])
    named = re.compile('|'.join(rf'(?<![\w.]){re.escape(k)}(?![\w#])' for k in keys if k))
    return [pid for pid, _, _, body in found if named.search(body)]


def _safe(text):
    """Feed text made inert in Markdown: no HTML, so no comment can close the markers."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _named(item):
    """An item's title, linked when its address is http(s), with its journal if it has one."""
    title = _safe(item.title).replace('[', '\\[').replace(']', '\\]')
    address = item.url
    for raw, coded in ((' ', '%20'), ('(', '%28'), (')', '%29'), ('<', '%3C'), ('>', '%3E')):
        address = address.replace(raw, coded)
    named = f'[{title}]({address})' if address.startswith(('https://', 'http://')) else title
    return named + (f' ({_safe(item.tags[0])})' if item.source == 'journal' and item.tags else '')


def brief(matches, verdicts, today, since, found=(), per_topic=3, pinned=''):
    """The generated section: items filed under a decision or step, verdicts first, each with
    the proposals that cite it; then what was judged worth adopting or learning and has no
    proposal yet - where an agent's thinking is wanted next."""
    filed = [m for m in matches if m.topic is not None]
    judged = sum(1 for m in matches if m.item.id in verdicts)
    links = Counter(m.item.url for m in matches)
    shared = frozenset(url for url, n in links.items() if n > 1)

    def verdict(m):
        return verdicts.get(m.item.id, (None, '', ''))

    def rank(m):
        return _ORDER[verdict(m)[0]], -m.score
    lines = [BEGIN, '', f'*Written by `python -m little_world.radar brief` on {today}; edits inside these markers '
             'are replaced at the next run.*', '',
             f'Since {since}: {len(matches)} items read, {len(filed)} filed under a decision or a step, '
             f'{judged} judged' + (f'; MuJoCo pinned at {pinned}' if pinned else '') + '.']
    topics = {}
    for m in filed:
        if verdict(m)[0] != 'skip':
            topics.setdefault(m.topic.id, []).append(m)
    for _, ms in sorted(topics.items(), key=lambda kv: (min(rank(m) for m in kv[1]), kv[0])):
        ms.sort(key=rank)
        lines += ['', f'**{ms[0].topic.id}** · {ms[0].topic.title}']
        for m in ms[:per_topic]:
            word, note, _ = verdict(m)
            props = cited(m.item, found, shared)
            why = note or 'matched ' + ', '.join(m.words[:3])
            lines.append(f'- {f"**{word}** " if word else ""}{_named(m.item)} · {_safe(why)}' +
                         (f' · {", ".join(props)}' if props else ''))
        if len(ms) > per_topic:
            lines.append(f'- and {len(ms) - per_topic} more (`python -m little_world.radar digest --html page.html`)')
    waiting = [m for m in filed if verdict(m)[0] in ('adopt', 'learn') and not cited(m.item, found, shared)]
    if waiting:
        lines += ['', 'Judged worth adopting or learning, with no proposal yet:']
        lines += [f'- {_named(m.item)} ({m.topic.id})' for m in sorted(waiting, key=rank)]
    return '\n'.join(lines + ['', END])


def write(path, section):
    """Put the section between the markers of the file, or at its end the first time."""
    path = Path(path)
    text = path.read_text(encoding='utf-8') if path.exists() else ''
    if BEGIN in text and END in text:
        text = text[:text.index(BEGIN)] + section + text[text.index(END) + len(END):]
    else:
        text = text.rstrip('\n') + '\n\n' + section + '\n'
    path.write_text(text, encoding='utf-8')
