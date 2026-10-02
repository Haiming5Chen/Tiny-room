"""Fetching the feeds, politely, with the standard library.

Meant to be run by the builder on their own machine - `python -m little_world.radar
fetch`, daily or weekly. A source is a URL and a parser; `get` is a parameter, so tests
read documents rather than the network. Limits kept: arXiv asks for one request every
three seconds; GitHub's search allows ten a minute without a token (a GITHUB_TOKEN in
the environment raises that, and is sent to api.github.com only).
"""
from dataclasses import dataclass
from datetime import date, timedelta
import os
from pathlib import Path
import re
import time
import urllib.request

from . import items as parse

USER_AGENT = 'little-world-radar/0.1 (a personal research digest)'
WATCHED = ('huggingface/lerobot', 'newton-physics/newton', 'mujocolab/mjlab', 'google-deepmind/mujoco_playground')
# Journals' table-of-contents feeds (ADR 0026): what reaches print, not only preprints.
JOURNALS = (('Science Robotics', 'https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=scirobotics'),
            ('IEEE Robotics and Automation Letters', 'https://ieeexplore.ieee.org/rss/TOC7083369.XML'),
            ('IEEE Transactions on Robotics', 'https://ieeexplore.ieee.org/rss/TOC8860.XML'))


@dataclass(frozen=True)
class Source:
    name: str
    url: str            # may hold {since} and {day} ('YYYY-MM-DD') or {repo}
    parse: object       # (text, context) -> items
    pause: float = 1.   # seconds to wait after each request
    daily: bool = False  # one request per day of the window


def pinned_mujoco(root):
    """The MuJoCo version the project pins in pyproject.toml, e.g. '3.3.7'."""
    path = Path(root) / 'pyproject.toml'
    found = re.search(r'mujoco==([\d.]+)', path.read_text(encoding='utf-8')) if path.exists() else None
    return found.group(1) if found else '0'


def sources(pinned='0'):
    return (
        Source('arXiv cs.RO', 'https://rss.arxiv.org/rss/cs.RO', lambda t, c: parse.arxiv_rss(t), 3.),
        Source('HF daily papers', 'https://huggingface.co/api/daily_papers?date={day}', lambda t, c: parse.hf_papers(t),
               1., daily=True),
        Source('HF robotics models', 'https://huggingface.co/api/models?pipeline_tag=robotics&sort=trendingScore&limit=50',
               lambda t, c: parse.hf_models(t)),
        Source('HF LeRobot models', 'https://huggingface.co/api/models?filter=lerobot&sort=trendingScore&limit=50',
               lambda t, c: parse.hf_models(t)),
        Source('GitHub MuJoCo repos', 'https://api.github.com/search/repositories?q=topic:mujoco+pushed:%3E={since}'
               '&sort=stars&order=desc&per_page=50', lambda t, c: parse.github_search(t), 7.),
        Source('GitHub new robotics repos', 'https://api.github.com/search/repositories?q=topic:robotics+created:%3E={since}'
               '&sort=stars&order=desc&per_page=50', lambda t, c: parse.github_search(t), 7.),
        Source('MuJoCo changelog', 'https://raw.githubusercontent.com/google-deepmind/mujoco/main/doc/changelog.rst',
               lambda t, c: parse.mujoco_changelog(t, pinned)),
        *(Source(f'{repo} releases', f'https://api.github.com/repos/{repo}/releases?per_page=5',
                 (lambda r: lambda t, c: parse.github_releases(t, r))(repo)) for repo in WATCHED),
        *(Source(name, url, (lambda n: lambda t, c: parse.journal_rss(t, n))(name), 2.) for name, url in JOURNALS),
    )


def request(url, environ=os.environ):
    """The request for a feed: named, and carrying a GitHub token to GitHub's API only."""
    headers = {'User-Agent': USER_AGENT}
    if url.startswith('https://api.github.com/'):
        headers['Accept'] = 'application/vnd.github+json'
        if environ.get('GITHUB_TOKEN'):
            headers['Authorization'] = f'Bearer {environ["GITHUB_TOKEN"]}'
    return urllib.request.Request(url, headers=headers)


def http_get(url):
    with urllib.request.urlopen(request(url), timeout=30) as response:
        return response.read().decode('utf-8', errors='replace')


def fetch(feeds, since, today=None, get=http_get, sleep=time.sleep):
    """(items, report): every feed's items, and a line per feed saying what it gave or
    why it failed. One feed failing does not stop the others; it is reported."""
    today = today or date.today()
    found, report = [], []
    for feed in feeds:
        days = [since + timedelta(days=k) for k in range((today - since).days + 1)] if feed.daily else [None]
        got, errors = 0, []
        for day in days:
            url = feed.url.format(since=since.isoformat(), day=(day or today).isoformat())
            try:
                new = feed.parse(get(url), day)
            except Exception as error:     # a feed down, renamed or rate-limited: say so, go on
                errors.append(f'{type(error).__name__}: {error}'[:160])
                new = []
            found.extend(new)
            got += len(new)
            sleep(feed.pause)
        report.append(f'{feed.name}: {got} items' + (f'; failed {len(errors)}x - {errors[0]}' if errors else ''))
    return found, report
