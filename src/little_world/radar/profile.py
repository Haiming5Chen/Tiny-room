"""What the radar looks for: the project's own decisions, its next steps, and what its
builder wants to learn.

Each decision record in docs/adr is a topic on its own - its title and its opening, the
problem it solved - so the radar's interests follow the project as it grows. The profile
(docs/radar/profile.md) adds words to a decision the record does not use, and topics of
two other kinds: 'Next: ...' for what the roadmap plans, 'Learn: ...' for what to study.
"""
from dataclasses import dataclass
from pathlib import Path
import re

KINDS = ('decision', 'next', 'learn')
OPENING = 2000          # characters of a decision record read after its title: its problem
TITLE_WEIGHT = 3        # a title's words count this many times over


@dataclass(frozen=True)
class Topic:
    id: str             # 'ADR 0017', 'Next: conveyor and feeder', 'Learn: sim-to-real'
    title: str
    text: str           # the words it is matched on
    kind: str           # 'decision', 'next' or 'learn'
    link: str = ''      # the document it came from, relative to the project root


def project_root(start=None):
    """The folder holding docs/adr: the working folder or one above it, else the source tree's."""
    here = Path(start or Path.cwd()).resolve()
    for folder in (here, *here.parents):
        if (folder / 'docs' / 'adr').is_dir():
            return folder
    return Path(__file__).resolve().parents[3]


def decisions(root):
    """One topic per decision record: 'ADR 0017' from docs/adr/0017-friction-that-holds.md."""
    out = []
    for path in sorted((Path(root) / 'docs' / 'adr').glob('[0-9][0-9][0-9][0-9]-*.md')):
        lines = path.read_text(encoding='utf-8').splitlines()
        title = next((l.lstrip('#').strip() for l in lines if l.startswith('#')), path.stem)
        body = '\n'.join(l for l in lines if not l.startswith('#'))[:OPENING]
        out.append(Topic(f'ADR {path.name[:4]}', title, ' '.join([title] * TITLE_WEIGHT + [body]), 'decision',
                         f'docs/adr/{path.name}'))
    return out


def roadmap_next(root):
    """The roadmap's own 'Next: ...' sentences, as one topic."""
    path = Path(root) / 'docs' / 'ROADMAP.md'
    if not path.exists():
        return []
    text = ' '.join(path.read_text(encoding='utf-8').split())
    found = re.findall(r'Next(?: in [^:]+)?: ([^.]+\.)', text)
    if not found:
        return []
    return [Topic('Next: roadmap', 'The roadmap\'s next steps', ' '.join(found[-2:]), 'next', 'docs/ROADMAP.md')]


def read_profile(text):
    """[(heading, words)] from the profile's '## heading' sections."""
    sections, heading, words = [], None, []
    for line in text.splitlines():
        if line.startswith('## '):
            if heading is not None:
                sections.append((heading, ' '.join(words)))
            heading, words = line[3:].strip(), []
        elif heading is not None and line.strip() and not line.lstrip().startswith(('>', '<!--')):
            words.append(line.strip().lstrip('-* '))
    if heading is not None:
        sections.append((heading, ' '.join(words)))
    return sections


def topics(root=None):
    """Every topic the radar scores against, decisions first."""
    root = project_root(root)
    found = {t.id: t for t in decisions(root)}
    extra = []
    path = Path(root) / 'docs' / 'radar' / 'profile.md'
    for heading, words in read_profile(path.read_text(encoding='utf-8')) if path.exists() else ():
        record = re.fullmatch(r'ADR (\d{4})', heading)
        if record:
            if heading not in found:
                raise ValueError(f'profile: {heading} has no decision record in docs/adr')
            t = found[heading]
            found[heading] = Topic(t.id, t.title, f'{t.text} {words} {words} {words}', t.kind, t.link)
            continue
        kind = {'Next': 'next', 'Learn': 'learn'}.get(heading.split(':', 1)[0])
        if kind is None or ':' not in heading:
            raise ValueError(f'profile: "{heading}" should read "ADR nnnn", "Next: ..." or "Learn: ..."')
        name = heading.split(':', 1)[1].strip()
        extra.append(Topic(heading, name[:1].upper() + name[1:], f'{name} {name} {words}', kind,
                           'docs/radar/profile.md'))
    return [*found.values(), *roadmap_next(root), *extra]
