"""python -m little_world.radar fetch | ingest FILE | digest | rate ID VERDICT [NOTE] | topics"""
import argparse
from datetime import date, timedelta
from pathlib import Path
import sys

from .digest import digest
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
    rate = commands.add_parser('rate', help='record a verdict on an item')
    rate.add_argument('id')
    rate.add_argument('verdict', choices=VERDICTS)
    rate.add_argument('note', nargs='*')
    commands.add_parser('topics', help='list what the radar looks for')
    args = parser.parse_args(argv)
    root = project_root(args.root)

    if args.command == 'topics':
        for t in topics(root):
            print(f'{t.kind:8} {t.id:28} {t.title}', file=out)
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
            page = digest(match(store.items(since), topics(root), args.least), store.verdicts(),
                          date.today().isoformat(), since, pinned_mujoco(root))
            if args.out:
                Path(args.out).write_text(page, encoding='utf-8')
                print(f'wrote {args.out}', file=out)
            else:
                print(page, file=out, end='')
        elif args.command == 'rate':
            store.rate(args.id, args.verdict, ' '.join(args.note))
            print(f'{args.id}: {args.verdict}', file=out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
