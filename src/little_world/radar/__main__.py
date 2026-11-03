"""python -m little_world.radar fetch | ingest FILE | digest | brief | rate ID VERDICT [NOTE] | topics
                          | collect [--add FILE] | recall | search WORDS | related TOPIC"""
import argparse
from dataclasses import replace
from datetime import date, timedelta
import json
from pathlib import Path
import sys

from . import collection
from .brief import brief, proposals, write
from .digest import markdown, plan
from .page import html
from .fetch import fetch, pinned_mujoco, sources
from .items import PARSERS
from .profile import project_root, topics
from .score import LEAST, match
from .store import DEFAULT, VERDICTS, Store


def main(argv=None, out=sys.stdout):
    parser = argparse.ArgumentParser(prog='python -m little_world.radar', description=__doc__)
    parser.add_argument('--db', default=str(DEFAULT), help=f'the radar\'s SQLite file (default {DEFAULT})')
    parser.add_argument('--root', default=None, help='the project folder holding docs/adr (default: found from here)')
    commands = parser.add_subparsers(dest='command', required=True)
    fetch_cmd = commands.add_parser('fetch', help='read the feeds into the radar')
    fetch_cmd.add_argument('--days', type=int, default=7, help='how far back the dated feeds reach')
    ingest = commands.add_parser('ingest', help='read a saved document into the radar')
    ingest.add_argument('file')
    ingest.add_argument('--format', choices=sorted(PARSERS), default='jsonl')
    ingest.add_argument('--since-version', default=None, help='mujoco-changelog: versions after this one')
    show = commands.add_parser('digest', help='write the digest of items first seen lately')
    show.add_argument('--days', type=int, default=7)
    show.add_argument('--least', type=float, default=LEAST, help='the cosine an item needs to match a topic')
    show.add_argument('--out', default=None, help='a Markdown file (default: print it)')
    show.add_argument('--html', default=None, help='also write the digest as a self-contained page')
    show.add_argument('--fragment', action='store_true', help='the page without its own document skeleton')
    agents = commands.add_parser('brief', help="write the radar's part of the agents' frontier file")
    agents.add_argument('--days', type=int, default=14)
    agents.add_argument('--least', type=float, default=LEAST, help='the cosine an item needs to match a topic')
    agents.add_argument('--file', default=None, help='default: docs/agents/FRONTIER.md in the project')
    rate = commands.add_parser('rate', help='record a verdict on an item')
    rate.add_argument('id')
    rate.add_argument('verdict', choices=VERDICTS)
    rate.add_argument('note', nargs='*')
    commands.add_parser('topics', help='list what the radar looks for')
    keep = commands.add_parser('collect', help="keep what is filed or judged in the project's collection (ADR 0034)")
    keep.add_argument('--days', type=int, default=None, help='only items first seen this many days ago or since')
    keep.add_argument('--least', type=float, default=LEAST, help='the cosine an item needs to match a topic')
    keep.add_argument('--add', action='append', default=[], metavar='FILE',
                      help='also merge entries gathered by hand, in the collection\'s shape (repeatable)')
    keep.add_argument('--file', default=None, help=f'default: {collection.PATH} in the project')
    back = commands.add_parser('recall', help='read the collection back into the radar\'s store')
    back.add_argument('--file', default=None, help=f'default: {collection.PATH} in the project')
    ask = commands.add_parser('search', help='the collection\'s entries closest to some words')
    ask.add_argument('words', nargs='*')
    ask.add_argument('--check', action='store_true',
                     help='measure the search on the questions with known answers in docs/radar/queries.jsonl')
    near = commands.add_parser('related', help='the collection\'s entries closest to a topic or a proposal')
    near.add_argument('subject', help="a topic as `topics` names it ('ADR 0032') or a proposal ('FR-016')")
    for cmd in (ask, near):
        cmd.add_argument('-n', type=int, default=10, help='how many entries (default 10)')
        cmd.add_argument('--verdict', action='append', choices=(*VERDICTS, 'none'), default=None,
                         help="only entries judged so ('none': not yet judged); repeatable")
        cmd.add_argument('--file', default=None, help=f'default: {collection.PATH} in the project')
        cmd.add_argument('--latent', type=float, default=None, metavar='SHARE',
                         help='the latent-semantic cosine\'s share of a hit\'s score, 0 to 1 (default 0.5, words and '
                              'meaning mixed equally, ADR 0062; 0: words alone)')
    args = parser.parse_args(argv)
    root = project_root(args.root)

    if args.command == 'topics':
        for t in topics(root):
            print(f'{t.kind:8} {t.id:28} {t.title}', file=out)
        return 0
    if args.command in ('search', 'related'):
        try:
            from .search import LATENT, Index, about, background, check     # numpy: the rest stays standard library
        except ImportError as error:
            parser.error(f"search needs numpy, which comes with MuJoCo: pip install -e '.[mujoco]' ({error})")
        if args.latent is None:
            args.latent = LATENT            # words and meaning mixed: words alone fell short as the collection grew (ADR 0062)
        if not 0. <= args.latent <= 1.:
            parser.error('--latent is a share between 0 and 1')
        path = Path(args.file) if args.file else Path(root) / collection.PATH
        kept = collection.read(path)
        index = Index(kept.values(), background(root))
        if args.command == 'search' and args.check:
            questions = [json.loads(line) for line in (Path(root) / 'docs' / 'radar' / 'queries.jsonl')
                         .read_text(encoding='utf-8').splitlines() if line.strip()]
            print(f'{len(questions)} questions with known answers, {len(kept)} entries:', file=out)
            for share, top, mrr, ranks in check(index, questions, (0., LATENT, 1.)):
                label = 'words alone' if share == 0. else 'latent alone' if share == 1. else f'latent share {share:g}'
                print(f'  {label:16} an answer in the top 3 for {top} of {len(questions)}; mean reciprocal rank {mrr:.3f}',
                      file=out)
                print(f'  {"":16} ranks {" ".join("-" if r is None else str(r) for r in ranks)}', file=out)
            return 0
        if args.command == 'search' and not args.words:
            parser.error('search needs some words (or --check)')
        try:
            question = ' '.join(args.words) if args.command == 'search' else about(args.subject, root)
        except KeyError as error:
            parser.error(str(error.args[0]))
        wanted = None if args.verdict is None else {'' if v == 'none' else v for v in args.verdict}
        least = .05 if args.command == 'search' else .02     # a topic's long text meets a short entry at a lower cosine
        hits = index.ask(question, args.n, wanted, least, latent=args.latent)
        print(f'{len(hits)} of {len(kept)} entries in {path.name}:', file=out)
        for h in hits:
            e = h.entry
            judged = f'{e.verdict:5}' if e.verdict else '  -  '
            print(f'{h.score:.2f} {judged} {e.item.title[:96]}', file=out)
            why = [*h.words, *(f'~{w}' for w in h.near)]
            print(f'           {e.item.url or e.id}' + (f'  ({", ".join(why)})' if why else ''), file=out)
            if e.note:
                print(f'           {e.note[:120]}', file=out)
        return 0
    with Store(args.db) as store:
        if args.command == 'fetch':
            since = date.today() - timedelta(days=args.days)
            found, report = fetch(sources(pinned_mujoco(root)), since)
            new = store.add(found)
            print('\n'.join(report), file=out)
            print(f'{new} new items; {store.count()} in the radar.', file=out)
        elif args.command == 'ingest':
            text = Path(args.file).read_text(encoding='utf-8')
            if args.format == 'mujoco-changelog':
                found = PARSERS[args.format](text, args.since_version or pinned_mujoco(root))
            else:
                found = PARSERS[args.format](text)
            print(f'{store.add(found)} new of {len(found)} items; {store.count()} in the radar.', file=out)
        elif args.command == 'digest':
            since = (date.today() - timedelta(days=args.days)).isoformat()
            found = plan(match(store.items(since), topics(root), args.least), store.verdicts(),
                         date.today().isoformat(), since, pinned_mujoco(root))
            text = markdown(found)
            if args.html:
                Path(args.html).write_text(html(found, fragment=args.fragment), encoding='utf-8')
                print(f'wrote {args.html}', file=out)
            if args.out:
                Path(args.out).write_text(text, encoding='utf-8')
                print(f'wrote {args.out}', file=out)
            elif not args.html:
                print(text, file=out, end='')
        elif args.command == 'brief':
            since = (date.today() - timedelta(days=args.days)).isoformat()
            path = Path(args.file) if args.file else Path(root) / 'docs' / 'agents' / 'FRONTIER.md'
            written = proposals(path.read_text(encoding='utf-8')) if path.exists() else []
            write(path, brief(match(store.items(since), topics(root), args.least), store.verdicts(),
                              date.today().isoformat(), since, written, pinned=pinned_mujoco(root)))
            print(f'wrote {path}', file=out)
        elif args.command == 'rate':
            store.rate(args.id, args.verdict, ' '.join(args.note))
            print(f'{args.id}: {args.verdict}', file=out)
        elif args.command == 'collect':
            path = Path(args.file) if args.file else Path(root) / collection.PATH
            since = (date.today() - timedelta(days=args.days)).isoformat() if args.days is not None else ''
            found = collection.from_store(store, match(store.items(since), topics(root), args.least), since)
            added = [e for extra in args.add for e in collection.parse(Path(extra).read_text(encoding='utf-8'))]
            filing = {m.item.id: tuple(t.id for t in (m.topic, m.second) if t is not None)
                      for m in match([e.item for e in added], topics(root), args.least)}
            found += [e if e.filed else replace(e, filed=filing.get(e.id, ())) for e in added]
            kept, new, changed = collection.gather(collection.read(path), found)
            collection.write(path, kept.values())
            print(f'{new} new, {changed} changed; {len(kept)} entries in {path}', file=out)
        elif args.command == 'recall':
            path = Path(args.file) if args.file else Path(root) / collection.PATH
            kept = collection.read(path)
            new = collection.to_store(store, kept.values())
            judged = sum(1 for e in kept.values() if e.verdict)
            print(f'{new} new to the radar of {len(kept)} entries, {judged} judged; {store.count()} in the radar.',
                  file=out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
