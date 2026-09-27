"""What the radar reads: one `Item` shape, and a parser per feed it reads.

A parser takes a document's text and returns items; fetching is elsewhere (fetch.py),
so each parser is tested on a document rather than on the network. Identifiers are
chosen so the same thing arriving by two routes is one item: a paper is 'arxiv:<id>'
whether it came from arXiv's own feed or Hugging Face's daily papers.
"""
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
import json
import re
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Item:
    id: str                 # 'arxiv:2609.01234', 'github:owner/repo', 'hf-model:org/name', 'mujoco:3.11.0#4'
    source: str             # the feed it came from: 'arxiv', 'hf-papers', 'hf-models', 'github', 'mujoco'
    title: str
    summary: str = ''
    url: str = ''
    published: str = ''     # ISO date, 'YYYY-MM-DD'
    kind: str = 'paper'     # 'paper', 'model', 'repo', 'release' or 'change'
    attention: float = 0.   # upvotes, stars or likes: what others make of it
    tags: tuple = ()


KINDS = ('paper', 'model', 'repo', 'release', 'change')


def _local(tag):
    """An XML tag without its namespace."""
    return tag.rsplit('}', 1)[-1]


def _children(element):
    return {_local(child.tag): child for child in element}


def _text(element):
    return ' '.join((element.text or '').split()) if element is not None else ''


def _date(value):
    """'YYYY-MM-DD' from an ISO timestamp, an RFC 822 date or 'September 22, 2026'."""
    value = (value or '').strip()
    if not value:
        return ''
    if re.match(r'\d{4}-\d{2}-\d{2}', value):
        return value[:10]
    for parse in (parsedate_to_datetime, lambda v: datetime.strptime(v, '%B %d, %Y')):
        try:
            return parse(value).date().isoformat()
        except (TypeError, ValueError, IndexError):
            continue
    return ''


def arxiv_id(url_or_id):
    """'2609.01234' from 'http://arxiv.org/abs/2609.01234v2', 'oai:arXiv.org:2609.01234v1'."""
    found = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', url_or_id or '')
    return found.group(1) if found else ''


# -- papers --------------------------------------------------------------------------------

def arxiv_rss(text):
    """arXiv's daily listing feed (rss.arxiv.org/rss/<category>): new submissions and
    cross-lists. Replacements - new versions of older papers - are not new, and are left out.
    The description reads 'arXiv:<id> Announce Type: new Abstract: <abstract>'."""
    items = []
    for element in ET.fromstring(text).iter():
        if _local(element.tag) != 'item':
            continue
        fields = _children(element)
        announce = _text(fields.get('announce_type'))
        if announce.startswith('replace'):
            continue
        description = _text(fields.get('description'))
        abstract = description.split('Abstract:', 1)[1].strip() if 'Abstract:' in description else description
        link = _text(fields.get('link'))
        pid = arxiv_id(link) or arxiv_id(_text(fields.get('guid')))
        if not pid:
            continue
        categories = tuple(_text(c) for c in element if _local(c.tag) == 'category')
        items.append(Item(f'arxiv:{pid}', 'arxiv', _text(fields.get('title')), abstract,
                          f'https://arxiv.org/abs/{pid}', _date(_text(fields.get('pubDate'))), 'paper', 0., categories))
    return items


def arxiv_api(text):
    """arXiv's query API (export.arxiv.org/api/query): an Atom feed of entries."""
    items = []
    for entry in ET.fromstring(text):
        if _local(entry.tag) != 'entry':
            continue
        fields = _children(entry)
        pid = arxiv_id(_text(fields.get('id')))
        if not pid:
            continue
        categories = tuple(c.get('term', '') for c in entry if _local(c.tag) == 'category')
        items.append(Item(f'arxiv:{pid}', 'arxiv', _text(fields.get('title')), _text(fields.get('summary')),
                          f'https://arxiv.org/abs/{pid}', _date(_text(fields.get('published'))), 'paper', 0., categories))
    return items


def hf_papers(text):
    """Hugging Face's daily papers (huggingface.co/api/daily_papers?date=...): papers the
    community put forward that day, with their upvotes. Keyed by arXiv id, so a paper also
    in arXiv's feed is the same item, with the upvotes as its attention."""
    items = []
    for entry in json.loads(text):
        paper = entry.get('paper', entry)
        pid = arxiv_id(paper.get('id', ''))
        if not pid:
            continue
        summary = paper.get('summary') or entry.get('summary') or ''
        repo = paper.get('githubRepo') or ''
        tags = (f'code:{repo}',) if repo else ()
        items.append(Item(f'arxiv:{pid}', 'hf-papers', ' '.join((paper.get('title') or entry.get('title') or '').split()),
                          ' '.join(summary.split()), f'https://huggingface.co/papers/{pid}',
                          _date(paper.get('publishedAt') or entry.get('publishedAt')), 'paper',
                          float(paper.get('upvotes') or 0), tags))
    return items


# -- models and repositories ---------------------------------------------------------------

def hf_models(text):
    """Hugging Face Hub's model list (huggingface.co/api/models?...): a model card's text is
    not in the list, so its tags stand in for a summary; its likes are its attention."""
    items = []
    for entry in json.loads(text):
        name = entry.get('id') or entry.get('modelId')
        if not name:
            continue
        tags = tuple(t for t in entry.get('tags', ()) if ':' not in t)
        summary = ' '.join(filter(None, (entry.get('pipeline_tag'), entry.get('library_name'), ' '.join(tags))))
        items.append(Item(f'hf-model:{name}', 'hf-models', name, summary, f'https://huggingface.co/{name}',
                          _date(entry.get('createdAt') or entry.get('lastModified')), 'model',
                          float(entry.get('likes') or 0), tags))
    return items


def github_search(text):
    """GitHub's repository search (api.github.com/search/repositories?q=...): stars are its
    attention, its topics its tags."""
    items = []
    for repo in json.loads(text).get('items', ()):
        name = repo.get('full_name')
        if not name:
            continue
        topics = tuple(repo.get('topics') or ())
        summary = ' '.join(filter(None, (repo.get('description') or '', ' '.join(topics))))
        items.append(Item(f'github:{name}', 'github', name, summary, repo.get('html_url') or f'https://github.com/{name}',
                          _date(repo.get('created_at')), 'repo', float(repo.get('stargazers_count') or 0), topics))
    return items


def github_releases(text, repo):
    """A watched repository's releases (api.github.com/repos/<repo>/releases)."""
    items = []
    for release in json.loads(text):
        tag = release.get('tag_name')
        if not tag or release.get('draft'):
            continue
        body = ' '.join((release.get('body') or '').split())
        title = f'{repo} {release.get("name") or tag}'
        items.append(Item(f'release:{repo}@{tag}', 'github', title, body[:4000], release.get('html_url') or '',
                          _date(release.get('published_at')), 'release', 0., (repo,)))
    return items


# -- a dependency's own changelog ----------------------------------------------------------

_VERSION = re.compile(r'^Version (\d+(?:\.\d+)+) \(([^)]+)\)\s*$')
_UNDERLINE = re.compile(r'^([-=^~"\'`#*+])\1{2,}\s*$')
_ENTRY = re.compile(r'^(\s*)(\d+\.|#\.|[-*+])\s+(.*)$')
_OPTION = re.compile(r'^\s*:[a-z-]+:(\s|$)')          # a directive's option, as ':class: attention'
_ROLE = re.compile(r':[a-zA-Z:]+:`([^`<]*?)(?:\s*<[^>]*>)?`')


def version_key(version):
    return tuple(int(part) for part in re.findall(r'\d+', version))


def _plain(rst):
    """reStructuredText inline markup to plain words: commit hashes dropped, roles and
    literals and links reduced to their text."""
    text = re.sub(r':commit:`[^`]*`\s*', '', rst)
    text = re.sub(r':issue:`(\d+)`', r'issue \1', text)
    text = _ROLE.sub(r'\1', text)
    text = re.sub(r'`([^`<]*?)\s*<[^>]*>`_+', r'\1', text)
    return ' '.join(text.replace('``', '').replace('`', '').split())


def mujoco_changelog(text, since='0'):
    """MuJoCo's changelog (doc/changelog.rst): one item per entry of every version newer
    than `since` - the version this project pins - tagged with its section (General,
    Engine, Actuation, MJX, Bug fixes, ...) and with 'breaking' when it sits under a
    'Breaking API changes' admonition. What changed under the simulator this project wraps.

    Entries are numbered ('4. ...') or bulleted ('- ...'). Numbered ones count wherever
    they are indented - inside an admonition too; an indented bullet is a detail of the
    entry above it. Other directives (images, videos) and their options are left out."""
    items = []
    lines = text.splitlines()
    state = {'version': None, 'date': '', 'section': '', 'entry': None, 'indent': 0, 'breaking': False,
             'admonition': None}

    def close():
        entry = state['entry']
        state['entry'] = None
        if entry is None or state['version'] is None:
            return
        words = _plain(' '.join(entry))
        if not words:
            return
        version = state['version']
        first = re.split(r'(?<=\.)\s', words, 1)[0]
        first = first if len(first) <= 140 else first[:139].rsplit(' ', 1)[0] + '...'
        n = sum(1 for i in items if i.id.startswith(f'mujoco:{version}#'))
        tags = tuple(t for t in (state['section'], 'breaking' if state['breaking'] else '') if t)
        items.append(Item(f'mujoco:{version}#{n + 1}', 'mujoco', f'MuJoCo {version}: {first}', words,
                          'https://mujoco.readthedocs.io/en/latest/changelog.html', state['date'], 'change', 0., tags))

    for i, line in enumerate(lines):
        stripped = line.strip()
        following = lines[i + 1].strip() if i + 1 < len(lines) else ''
        indent = len(line) - len(line.lstrip())
        if not stripped:
            if state['entry'] is not None and i + 1 < len(lines) and lines[i + 1][:1] not in (' ', ''):
                close()
            continue
        if _UNDERLINE.match(stripped):
            continue
        if _UNDERLINE.match(following) and indent == 0:       # a heading
            close()
            heading = _VERSION.match(stripped)
            state['admonition'] = None
            if heading:
                newer = version_key(heading.group(1)) > version_key(since)
                state.update(version=heading.group(1) if newer else None, date=_date(heading.group(2)), section='')
            elif stripped.startswith(('Version', 'Upcoming')):
                state['version'] = None
            else:
                state['section'] = stripped
            continue
        if stripped.startswith('.. '):                        # a directive: an admonition, an image, a video
            breaking = stripped.startswith('.. admonition:: Breaking')
            if state['entry'] is not None and indent > state['indent']:
                state['breaking'] = state['breaking'] or breaking    # inside the open entry: it is breaking
                continue
            close()
            if breaking:
                state['admonition'] = indent
            elif state['admonition'] is not None and indent <= state['admonition']:
                state['admonition'] = None
            continue
        if _OPTION.match(line):
            continue
        if state['admonition'] is not None and indent <= state['admonition']:
            state['admonition'] = None                        # the admonition's block has ended
        entry = _ENTRY.match(line)
        numbered = entry is not None and entry.group(2)[0] != '-' and entry.group(2) not in '*+'
        if entry and (numbered or indent <= 1) and (state['entry'] is None or numbered or indent <= state['indent']):
            close()
            state.update(entry=[entry.group(3)], indent=indent, breaking=state['admonition'] is not None)
        elif state['entry'] is not None:
            state['entry'].append(stripped)                   # a continuation, or a detail of the entry
    close()
    return items


# -- gathered by hand, or by an assistant with a browser -----------------------------------

def jsonl(text):
    """One JSON object per line with Item's fields: what a person or an assistant gathered
    from pages the feeds do not cover."""
    items = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        data = json.loads(line)
        unknown = set(data) - set(Item.__dataclass_fields__)
        if unknown or not data.get('id') or not data.get('title'):
            raise ValueError(f'line {number}: needs id and title; unknown fields {sorted(unknown)}')
        if data.get('kind', 'paper') not in KINDS:
            raise ValueError(f'line {number}: kind must be one of {KINDS}')
        data['tags'] = tuple(data.get('tags', ()))
        data['attention'] = float(data.get('attention', 0.))
        data['published'] = _date(data.get('published', ''))
        items.append(Item(**{'source': 'gathered', **data}))
    return items


PARSERS = {'arxiv-rss': arxiv_rss, 'arxiv-api': arxiv_api, 'hf-papers': hf_papers, 'hf-models': hf_models,
           'github-search': github_search, 'mujoco-changelog': mujoco_changelog, 'jsonl': jsonl}
