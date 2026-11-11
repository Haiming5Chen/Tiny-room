"""Every relative link and image in the repository's Markdown points at a file that exists.

    python scripts/check_links.py            # README.md, the other top-level notes and docs/
    python scripts/check_links.py FILE...    # only these

Links to the web, to mail and to a place on the same page are not followed. Standard library only.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'!?\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)|(?:src|href)="([^"]+)"')
FENCE = re.compile(r'^(```|~~~)')


def pages(root=ROOT):
    return sorted([*root.glob('*.md'), *(root / 'docs').rglob('*.md')])


def broken(page, root=ROOT):
    """[(line number, target)] for the relative links of `page` that lead nowhere."""
    out, fenced = [], False
    for number, line in enumerate(Path(page).read_text(encoding='utf-8').splitlines(), 1):
        if FENCE.match(line.strip()):
            fenced = not fenced
        if fenced:
            continue
        for match in LINK.finditer(re.sub(r'`[^`]*`', '', line)):
            target = (match.group(1) or match.group(2)).split('#')[0]
            if not target or re.match(r'[a-z][a-z0-9+.-]*:', target, re.I):
                continue
            path = (root / target.lstrip('/')) if target.startswith('/') else (Path(page).parent / target)
            if not path.exists():
                out.append((number, target))
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    found = [(page, *bad) for page in ([Path(a) for a in argv] or pages()) for bad in broken(page)]
    for page, number, target in found:
        print(f'{Path(page).resolve().relative_to(ROOT)}:{number}: {target}')
    print(f'{len(found)} broken link{"s" if len(found) != 1 else ""} in {len(argv) or len(pages())} pages')
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
