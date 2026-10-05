"""The radar's collection: what the project has read and what it made of it, kept in the
repository (ADR 0034).

The store (store.py) is one machine's working memory: every item of every feed, in a file
outside the repository. The collection is the project's: the items filed under one of its
topics or judged, one JSON object a line in `docs/radar/collection.jsonl`, sorted by id, so
an agent on any machine - or the weekly reading, which runs in a fresh session each time -
starts from what was read before, and a decision record can cite what it adopted.

An entry is an `Item` and what was made of it: when it was first seen, the topics it was
filed under, how much of it was read ('title' when only the title was, 'abstract', 'full'),
and a verdict with its note and date. A summary is arXiv's own abstract (arXiv's metadata
is CC0) or a few lines written while reading it; a journal's abstract is not copied.

Two agents may add the same paper in two checkouts. Entries with one id merge - the longer
summary, the larger attention, the sources and topics joined, the earliest sighting, the
latest verdict - so the file can be merged line by line (`.gitattributes`: merge=union) and
read back as one entry a paper. Standard library only.
"""
from dataclasses import dataclass, replace
from datetime import date
import json
from pathlib import Path
import re

from .items import KINDS, Item, _date
from .store import VERDICTS

PATH = Path('docs') / 'radar' / 'collection.jsonl'
READ = ('title', 'abstract', 'full')
SUMMARY = 1500          # characters of a summary kept: an abstract, not a paper
ORDER = ('id', 'source', 'kind', 'title', 'url', 'published', 'seen', 'read', 'filed', 'verdict', 'note', 'rated',
         'attention', 'tags', 'summary')
_ITEM = tuple(Item.__dataclass_fields__)
_REFERENCE = re.compile(r'\b(?:ADR|FR|LW)[- ]?\d{3,4}\b')


@dataclass(frozen=True)
class Entry:
    item: Item
    seen: str = ''          # first seen, 'YYYY-MM-DD'
    filed: tuple = ()       # the topics it was filed under: 'ADR 0032', 'Next: grasping from a camera'
    read: str = ''          # '', 'title', 'abstract' or 'full'
    verdict: str = ''       # '' or one of store.VERDICTS
    note: str = ''          # why, for this project
    rated: str = ''         # when the verdict was given

    @property
    def id(self):
        return self.item.id

    @property
    def text(self):
        """The words it is searched by: its title twice, its summary and the note on it, less
        the project's own references (ADR 0032, FR-016), which say where it is used, not what
        it is about."""
        return _REFERENCE.sub(' ', ' '.join((self.item.title, self.item.title, self.item.summary, self.note)))


def public(item):
    """The item as the repository may keep it: a journal's abstract is the publisher's, so
    only its title, link and date stay; any other summary is cut to SUMMARY characters."""
    summary = '' if item.source == 'journal' or item.id.startswith('journal:') else item.summary
    if len(summary) > SUMMARY:
        summary = summary[:SUMMARY].rsplit(' ', 1)[0] + ' ...'
    return replace(item, summary=summary) if summary != item.summary else item


def entry(data, where=''):
    """One entry from a dict with the collection's fields; anything unknown, missing or
    malformed is refused, naming `where`."""
    unknown = set(data) - set(ORDER)
    if unknown or not data.get('id') or not data.get('title'):
        raise ValueError(f'{where}needs id and title; unknown fields {sorted(unknown)}')
    if data.get('kind', 'paper') not in KINDS:
        raise ValueError(f'{where}kind must be one of {KINDS}')
    if data.get('verdict', '') not in ('', *VERDICTS):
        raise ValueError(f'{where}verdict must be one of {VERDICTS}')
    if data.get('read', '') not in ('', *READ):
        raise ValueError(f'{where}read must be one of {READ}')
    if not isinstance(data.get('filed', []), list) or not isinstance(data.get('tags', []), list):
        raise ValueError(f'{where}filed and tags are lists')
    fields = {k: data[k] for k in _ITEM if k in data}
    fields['tags'] = tuple(fields.get('tags', ()))
    fields['attention'] = float(fields.get('attention', 0.))
    fields['published'] = _date(fields.get('published', ''))
    item = public(Item(**{'source': 'gathered', **fields}))
    return Entry(item, _date(data.get('seen', '')), tuple(data.get('filed', ())), data.get('read', ''),
                 data.get('verdict', ''), ' '.join(str(data.get('note', '')).split()), _date(data.get('rated', '')))


def parse(text):
    """The entries of a collection file, or of a file gathered by hand in the same shape,
    one per id, in file order."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip():
            try:
                data = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f'line {number}: {error}') from None
            found.append(entry(data, f'line {number}: '))
    return list(combine(found).values())


def _joined(a, b):
    return tuple(dict.fromkeys([*a, *b]))


def merge(a, b):
    """One entry from two with the same id; `b` is the later word on a verdict given on the
    same day, and on a title or a link the two disagree about."""
    if a.id != b.id:
        raise ValueError(f'{a.id} is not {b.id}')
    x, y = a.item, b.item
    sources = '+'.join(_joined(x.source.split('+'), y.source.split('+')))
    item = Item(x.id, sources, y.title or x.title, y.summary if len(y.summary) > len(x.summary) else x.summary,
                y.url or x.url, x.published or y.published, y.kind if y.kind != 'paper' else x.kind,
                max(x.attention, y.attention), _joined(x.tags, y.tags))
    judged = b if b.verdict and (not a.verdict or b.rated >= a.rated) else a
    seen = min(s for s in (a.seen, b.seen) if s) if a.seen or b.seen else ''
    read = max(a.read, b.read, key=lambda r: READ.index(r) if r else -1)
    return Entry(item, seen, _joined(a.filed, b.filed), read, judged.verdict, judged.note, judged.rated)


def combine(entries, into=None):
    """{id: entry}, entries with one id merged in order."""
    out = dict(into or {})
    for e in entries:
        out[e.id] = merge(out[e.id], e) if e.id in out else e
    return out


def dumps(entries):
    """The collection file: one line an entry, sorted by id, fields in a fixed order and
    empty ones left out, so a change is one line of a diff."""
    lines = []
    for e in sorted(entries, key=lambda e: e.id):
        values = {**{k: getattr(e.item, k) for k in _ITEM}, 'seen': e.seen, 'filed': list(e.filed), 'read': e.read,
                  'verdict': e.verdict, 'note': e.note, 'rated': e.rated}
        values['tags'] = list(values['tags'])
        data = {k: values[k] for k in ORDER if values[k] not in ('', [], 0., None)}
        lines.append(json.dumps(data, ensure_ascii=False))
    return '\n'.join(lines) + ('\n' if lines else '')


def read(path):
    """{id: entry} of a collection file; {} if there is none yet."""
    path = Path(path)
    return {e.id: e for e in parse(path.read_text(encoding='utf-8'))} if path.exists() else {}


def write(path, entries):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(entries), encoding='utf-8')


def from_store(store, matches, since=''):
    """Entries for what the store holds that is filed under a topic (`matches`: score.match
    over its items) or judged; the sighting is the store's first one."""
    verdicts = store.verdicts()
    seen = dict(store.db.execute('SELECT id, first_seen FROM items WHERE first_seen >= ?', (since,)))
    out = []
    for m in matches:
        judged = verdicts.get(m.item.id)
        if m.item.id not in seen or (m.topic is None and judged is None):
            continue
        filed = tuple(t.id for t in (m.topic, m.second) if t is not None)
        verdict, note, rated = judged or ('', '', '')
        out.append(Entry(public(m.item), seen[m.item.id], filed, '', verdict, note or '', rated or ''))
    return out


def gather(collection, entries):
    """The collection with `entries` merged in, and how many entries were new and how many
    changed."""
    out = dict(collection)
    new = changed = 0
    for e in entries:
        if e.id not in out:
            out[e.id], new = e, new + 1
            continue
        merged = merge(out[e.id], e)
        if merged != out[e.id]:
            out[e.id], changed = merged, changed + 1
    return out, new, changed


def to_store(store, entries):
    """The collection back into a store - on a new machine, or in the weekly reading's fresh
    session - so its digest and brief know what was read and judged before. Returns how many
    items were new to the store."""
    new = 0
    entries = list(entries)
    for e in entries:
        new += store.add([e.item], seen=e.seen or date.today().isoformat())
    for e in entries:
        if e.verdict:
            store.rate(e.id, e.verdict, e.note, when=e.rated or None)
    return new
