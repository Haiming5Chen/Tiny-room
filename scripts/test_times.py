"""Which tests are slow: write tests/slow.txt from a suite run's JUnit XML (ADR 0073).

    python -m pytest -q --junitxml=times.xml          # the whole headless suite, timed
    python scripts/test_times.py times.xml             # what the quick tier would keep
    python scripts/test_times.py times.xml --write     # rewrite tests/slow.txt

A test that took SLOW seconds or more is listed, slowest first, with what it took where it was
measured; tests/conftest.py marks the listed tests `slow`, and `pytest -m "not slow"` is the
quick tier. Standard library only.
"""
import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SLOW = 2.           # s: a test this slow is left out of the quick tier
LIST = Path(__file__).resolve().parents[1] / 'tests' / 'slow.txt'
HEAD = ('# Tests left out of the quick tier (pytest -m "not slow"): each took 2 s or more of the headless suite\n'
        '# on two cores of a cloud Linux machine, MuJoCo 3.10.0. Seconds, then file::test. Written by\n'
        '# scripts/test_times.py from a run\'s JUnit XML; tests/conftest.py reads it (ADR 0073).\n')


def cases(paths):
    """(seconds, 'test_file.py::test_name[param]') for each test that ran in these JUnit files."""
    out = []
    for path in paths:
        for case in ET.parse(path).getroot().iter('testcase'):
            if case.find('skipped') is None:
                out.append((float(case.get('time', 0.)), f"{case.get('classname').split('.')[-1]}.py::{case.get('name')}"))
    return out


def read(path=LIST):
    """The listed tests: {'test_file.py::test_name[param]': seconds}; empty when there is no list."""
    if not Path(path).exists():
        return {}
    rows = [line.split(None, 1) for line in Path(path).read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.startswith('#')]
    return {name.strip(): float(seconds) for seconds, name in rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('xml', nargs='+', help="a suite run's JUnit XML files")
    parser.add_argument('--write', action='store_true', help='rewrite tests/slow.txt')
    args = parser.parse_args(argv)
    ran = cases(args.xml)
    slow = sorted((c for c in ran if c[0] >= SLOW), reverse=True)
    quick = [c for c in ran if c[0] < SLOW]
    print(f'{len(ran)} tests ran in {sum(t for t, _ in ran) / 60:.1f} min of test time: '
          f'{len(quick)} quick ({sum(t for t, _ in quick) / 60:.1f} min), '
          f'{len(slow)} slow ({sum(t for t, _ in slow) / 60:.1f} min)')
    if args.write:
        LIST.write_text(HEAD + ''.join(f'{t:6.1f} {name}\n' for t, name in slow), encoding='utf-8')
        print(f'wrote {LIST.relative_to(LIST.parents[1])}: {len(slow)} tests')
    return 0


if __name__ == '__main__':
    sys.exit(main())
