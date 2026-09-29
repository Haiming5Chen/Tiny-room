"""The digest as one self-contained page: the summary at a glance, details on demand.

`html(digest)` renders what `digest.plan` sorted: the counts and the verdicts as a bar,
each topic's items as rows led by their verdict, the simulator's releases as a chart, and
what is still to judge with the command that records a verdict. Every item's summary,
score and matched words sit behind a disclosure, so the page reads as a list of decisions
first. Standard library only; the page has its own styles and a few lines of script for
the verdict filter, and works offline (its fonts fall back to the system's).

Everything that came from a feed is escaped, and only http(s) links are made links.
"""
from html import escape

from .digest import attention
from .store import VERDICTS

FONTS = ('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,600..800'
         '&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap')

STYLE = '''
:root {
  color-scheme: dark;
  --bg: #0e1418; --panel: #141c22; --line: #25313a; --ink: #dbe6ed; --muted: #8196a4;
  --adopt: #5ed4b0; --learn: #8db4f2; --watch: #f5b861; --skip: #66767f; --open: #3a4852;
  --breaking: #f08a5d; --link: #dbe6ed;
  --display: "Archivo", "Arial Narrow", system-ui, sans-serif;
  --body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace;
}
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) {
    color-scheme: light;
    --bg: #f3f6f7; --panel: #ffffff; --line: #d6dfe4; --ink: #13202a; --muted: #566876;
    --adopt: #11866a; --learn: #2e5eae; --watch: #a6620f; --skip: #7f8c96; --open: #c3ced5;
    --breaking: #c4502a; --link: #13202a;
  }
}
:root[data-theme="light"] {
  color-scheme: light;
  --bg: #f3f6f7; --panel: #ffffff; --line: #d6dfe4; --ink: #13202a; --muted: #566876;
  --adopt: #11866a; --learn: #2e5eae; --watch: #a6620f; --skip: #7f8c96; --open: #c3ced5;
  --breaking: #c4502a; --link: #13202a;
}
body { background: var(--bg); color: var(--ink); font: 15px/1.55 var(--body); margin: 0; }
.page { max-width: 880px; margin: 0 auto; padding-inline: 16px; padding-block: 28px 64px;
        display: grid; gap: 34px; }
a { color: var(--link); text-decoration-color: color-mix(in srgb, var(--muted) 60%, transparent);
    text-underline-offset: 3px; }
a:hover { text-decoration-color: currentColor; }
:focus-visible { outline: 2px solid var(--adopt); outline-offset: 2px; }
.eyebrow, .label { font: 600 11.5px/1.2 var(--body); letter-spacing: .09em; text-transform: uppercase; color: var(--muted); }
h1 { font: 800 clamp(30px, 6vw, 44px)/1.05 var(--display); font-stretch: 80%; margin: 6px 0 10px;
     letter-spacing: -.01em; text-wrap: balance; }
h2 { font: 700 21px/1.2 var(--display); font-stretch: 85%; margin: 0; text-wrap: balance; }
h2 small { font: 500 13px var(--mono); color: var(--muted); margin-left: 8px; }
h3 { font: 600 15px/1.35 var(--body); margin: 0; display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap; }
h3 code { font: 500 12.5px var(--mono); color: var(--muted); }
.lede { color: var(--muted); max-width: 62ch; margin: 0; }
.summary { display: grid; gap: 12px; }
.band { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.figure { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px; }
.figure b { display: block; font: 700 30px/1.1 var(--display); font-variant-numeric: tabular-nums; }
.figure span { color: var(--muted); font-size: 13px; }
.split { display: flex; height: 10px; border-radius: 5px; overflow: hidden; background: var(--open); }
.split i { display: block; height: 100%; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 13px; color: var(--muted); }
.legend span::before { content: ""; display: inline-block; width: 9px; height: 9px; border-radius: 2px;
                       background: var(--c); margin-right: 6px; vertical-align: 0; }
.filters { display: flex; flex-wrap: wrap; gap: 8px; }
.filters button { font: 500 13px var(--body); color: var(--ink); background: var(--panel); cursor: pointer;
                  border: 1px solid var(--line); border-radius: 999px; padding: 5px 12px; }
.filters button[aria-pressed="true"] { border-color: var(--ink); }
section { display: grid; gap: 18px; }
.group { display: grid; gap: 8px; }
ul.items { list-style: none; margin: 0; padding: 0; display: grid; gap: 2px;
           border-top: 1px solid var(--line); }
.item { display: grid; grid-template-columns: 74px minmax(0, 1fr); gap: 4px 12px; padding: 10px 0;
        border-bottom: 1px solid var(--line); }
.pill { font: 600 11px/1 var(--body); letter-spacing: .06em; text-transform: uppercase; text-align: center;
        border-radius: 4px; padding: 5px 0; align-self: start; margin-top: 2px;
        color: var(--bg); background: var(--c, var(--open)); }
.pill.open { color: var(--muted); background: transparent; border: 1px dashed var(--open); }
.title { font-weight: 500; overflow-wrap: anywhere; }
.meta { grid-column: 2; font: 12.5px/1.5 var(--mono); color: var(--muted); display: flex; flex-wrap: wrap; gap: 2px 14px; }
.why { grid-column: 2; margin: 2px 0 0; }
details { grid-column: 2; font-size: 14px; color: var(--muted); }
summary { cursor: pointer; font-size: 13px; width: fit-content; }
details p { margin: 6px 0 0; max-width: 72ch; }
.words { font-family: var(--mono); font-size: 12.5px; }
.chart { overflow-x: auto; }
.chart svg { display: block; width: 100%; min-width: 520px; height: auto; }
.chart text { font: 12px var(--mono); fill: var(--muted); }
.chart .v { fill: var(--ink); font-weight: 500; }
.note { color: var(--muted); font-size: 14px; margin: 0; }
.cmd { font: 13px var(--mono); background: var(--panel); border: 1px solid var(--line); border-radius: 6px;
       padding: 8px 10px; overflow-x: auto; white-space: nowrap; }
ol.judge { margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; }
ol.judge li { display: grid; grid-template-columns: minmax(0, 1fr); }
ol.judge code { font: 12.5px var(--mono); color: var(--muted); overflow-wrap: anywhere; }
@media (max-width: 560px) {
  .band { grid-template-columns: 1fr; }
  .item { grid-template-columns: 1fr; }
  .meta, .why, details { grid-column: 1; }
  .pill { width: 74px; }
}
.chart .bar { fill: var(--open); } .chart .brk { fill: var(--breaking); } .chart .filed { fill: var(--adopt); }
'''

SCRIPT = '''
(function () {
  var buttons = document.querySelectorAll('.filters button');
  function show(verdict) {
    buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.show === verdict)); });
    document.querySelectorAll('.item[data-verdict]').forEach(function (li) {
      li.hidden = verdict !== 'all' && li.dataset.verdict !== verdict;
    });
    document.querySelectorAll('.group, section.filed').forEach(function (box) {
      box.hidden = !box.querySelector('.item[data-verdict]:not([hidden])');
    });
  }
  buttons.forEach(function (b) { b.addEventListener('click', function () { show(b.dataset.show); }); });
})();
'''


def _link(text, url):
    text = escape(text)
    if url.startswith(('https://', 'http://')):
        return f'<a href="{escape(url, quote=True)}" rel="noopener">{text}</a>'
    return text


def _item(e):
    item, m = e.item, e.match
    verdict = e.verdict or 'open'
    meta = [escape(s) for s in (item.source.replace('+', ' + '), item.published, attention(item)) if s]
    if m.second is not None:
        meta.append(f'also {escape(m.second.id)}')
    why = f'<p class="why">{escape(e.note)}</p>' if e.note else ''
    words = escape(', '.join(m.words)) or 'no shared words'
    return (f'<li class="item" data-verdict="{verdict}">'
            f'<span class="pill{" open" if verdict == "open" else ""}" style="--c: var(--{verdict})">'
            f'{"to judge" if verdict == "open" else verdict}</span>'
            f'<span class="title">{_link(item.title, item.url)}</span>'
            f'<span class="meta">{"".join(f"<span>{x}</span>" for x in meta)}</span>{why}'
            f'<details><summary>What matched</summary><p class="words">{words} · cosine {m.score:.2f}</p>'
            + (f'<p>{escape(item.summary[:900])}{"…" if len(item.summary) > 900 else ""}</p>' if item.summary else '')
            + f'<p class="words">{escape(item.id)}</p></details></li>')


def _groups(groups):
    out = []
    for g in groups:
        t = g.topic
        head = (f'<code>{escape(t.id)}</code> {escape(t.title)}' if t.kind == 'decision' else escape(t.title))
        out.append(f'<div class="group"><h3>{head}</h3><ul class="items">'
                   + ''.join(_item(e) for e in g.entries) + '</ul></div>')
    return ''.join(out)


def _split(d):
    """The filed items as one bar: judged by verdict, and what is left to judge."""
    judged = {v: d.verdicts[v] for v in VERDICTS}
    rest = max(0, d.filed - sum(judged.values()))
    total = max(1, d.filed)
    parts = [(v, n) for v, n in judged.items() if n] + ([('open', rest)] if rest else [])
    bar = ''.join(f'<i style="width:{100 * n / total:.2f}%; background: var(--{v})" title="{n} {v}"></i>'
                  for v, n in parts)
    legend = ''.join(f'<span style="--c: var(--{v})">{n} {"to judge" if v == "open" else v}</span>' for v, n in parts)
    return f'<div class="split" role="img" aria-label="Verdicts on filed items">{bar}</div><div class="legend">{legend}</div>'


def _chart(releases):
    """One row per release: all its changes as a bar, the breaking ones from its start,
    the count that touch a topic here at its end."""
    top = max(r.changes for r in releases)
    row, left, width = 24, 150, 380
    height = row * len(releases) + 30
    rows = []
    for i, r in enumerate(reversed(releases)):
        y = 22 + i * row
        full = width * r.changes / top
        broken = width * r.breaking / top
        rows.append(f'<text class="v" x="0" y="{y + 12}">{escape(r.version)}</text>'
                    f'<text x="62" y="{y + 12}">{escape(r.date)}</text>'
                    f'<rect class="bar" x="{left}" y="{y + 2}" width="{full:.1f}" height="12" rx="2"></rect>'
                    f'<rect class="brk" x="{left}" y="{y + 2}" width="{broken:.1f}" height="12" rx="2"></rect>'
                    f'<text x="{left + full + 8:.1f}" y="{y + 12}">{r.changes}'
                    + (f' · <tspan class="filed">{r.filed} filed</tspan>' if r.filed else '') + '</text>')
    axis = (f'<text x="{left}" y="12">changes per release</text>'
            f'<rect class="brk" x="{left + 150}" y="3" width="10" height="10" rx="2"></rect>'
            f'<text x="{left + 166}" y="12">breaking</text>')
    return (f'<div class="chart"><svg viewBox="0 0 640 {height}" role="img" '
            f'aria-label="MuJoCo changes per release since the pinned version">{axis}{"".join(rows)}</svg></div>')


def html(d, fragment=False):
    """The page. `fragment` leaves out the document's own skeleton (doctype, head, body),
    for a host that wraps the page in its own."""
    parts = [f'<header><div class="eyebrow">Little World · {escape(d.day)}</div>'
             '<h1>Frontier radar</h1>'
             '<p class="lede">New papers, models, repositories and simulator changes, each filed under the '
             'decision record, planned step or learning goal it shares the most words with. '
             'Open an item to see what matched.</p></header>',
             '<div class="summary"><div class="band">'
             f'<div class="figure"><b>{d.total}</b><span>new since {escape(d.since)}</span></div>'
             f'<div class="figure"><b>{d.filed}</b><span>filed under a topic</span></div>'
             f'<div class="figure"><b>{sum(d.verdicts.values())}</b><span>judged</span></div></div>{_split(d)}</div>',
             '<div class="filters" role="group" aria-label="Show items">'
             + ''.join(f'<button type="button" data-show="{v}" aria-pressed="{str(v == "all").lower()}">'
                       f'{"All" if v == "all" else "To judge" if v == "open" else v.title()}</button>'
                       for v in ('all', *VERDICTS[:3], 'open', VERDICTS[3])) + '</div>']
    for key, title, groups in d.sections:
        count = sum(len(g.entries) for g in groups)
        parts.append(f'<section class="filed" id="{key}"><h2>{escape(title)}<small>{count}</small></h2>{_groups(groups)}</section>')
    if d.releases:
        changes = sum(r.changes for r in d.releases)
        breaking = sum(r.breaking for r in d.releases)
        unfiled = ', '.join(f'{n} {escape(s)}' for s, n in d.unfiled_changes.most_common())
        parts.append('<section class="filed" id="simulator">'
                     f'<h2>Under the simulator: MuJoCo {escape(d.pinned or "?")} → {escape(d.releases[-1].version)}'
                     f'<small>{changes}</small></h2>'
                     f'<p class="note">{changes} changes in {len(d.releases)} releases, {breaking} of them breaking; '
                     f'{sum(r.filed for r in d.releases)} touch a topic here.</p>{_chart(d.releases)}'
                     + _groups(d.changes) + (f'<p class="note">No topic: {unfiled}.</p>' if unfiled else '') + '</section>')
    if d.loud:
        parts.append('<section id="loud"><h2>Much attention, no topic here</h2>'
                     '<p class="note">What others are looking at that none of the topics asks for: '
                     'a gap in the profile, or noise.</p><ul class="items">'
                     + ''.join(f'<li class="item"><span class="pill open">{escape(attention(e.item).split(" ")[0])}</span>'
                               f'<span class="title">{_link(e.item.title, e.item.url)}</span>'
                               f'<span class="meta"><span>{escape(e.item.source)}</span>'
                               f'<span>{escape(attention(e.item))}</span></span></li>' for e in d.loud)
                     + '</ul></section>')
    if d.triage:
        parts.append('<section id="judge"><h2>To judge</h2>'
                     '<p class="note">adopt: change the project · learn: study it · watch: look again later · '
                     'skip: not for this project. Record a verdict with its reason:</p>'
                     '<div class="cmd">python -m little_world.radar rate &lt;id&gt; adopt "why"</div><ol class="judge">'
                     + ''.join(f'<li><span>{_link(e.item.title, e.item.url)}</span><code>{escape(e.item.id)}</code></li>'
                               for e in d.triage) + '</ol></section>')
    body = f'<main class="page">{"".join(parts)}</main><script>{SCRIPT}</script>'
    head = ('<title>Frontier radar</title>'
            f'<link rel="preconnect" href="https://fonts.googleapis.com">'
            f'<link rel="stylesheet" href="{FONTS}"><style>{STYLE}</style>')
    if fragment:
        return head + body + '\n'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f'{head}</head><body>{body}</body></html>\n')
