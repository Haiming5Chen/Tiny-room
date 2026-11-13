"""Is set-up i the same start in both arms? Each run's set-up, fingerprinted (FR-041).

A paired result - a disturbance against no disturbance (ADR 0036), a recovery against its
baselines (ADR 0051), a squeeze against a ramp (ADR 0070) - reads set-up i's two runs as one
run until the factor under test. The pairs were matched by their labels ('repeat 12'), and a
label names a draw, not a start: a scratch driver once drew the same labels with the payload
placed elsewhere (`site=None`, ADR 0052), and its pairs were not pairs. A study of paired robot
evaluations found the same episode index need not mean the same start, under some resets, and asks
for the starts to be checked before any paired statistic (arXiv 2611.00896).

So every run keeps a fingerprint of its set-up, taken when the program takes over, and a
paired statistic first checks that both arms began from the same one. A fingerprint has parts,
each a digest:

- `engine`: the MuJoCo release;
- `model`: the compiled model as MuJoCo saves it - every body, geom, mass, friction, gain and
  option (`mj_saveModel`);
- `start`: every joint's position and speed before the first step;
- `settled`: the same when the program takes over, after the field's settling;
- `program`: the blocks of the program that runs, '' when none does;
- `draw`: the draw's own values - where it set the machine down, its payload, its friction - and label.

Each physical digest comes in two grades: `exact`, the bytes, and `rounded` - the model's numbers to
six significant figures, the joints' positions to a micrometre (or microradian) and their speeds to
a micrometre a second - so that two machines whose arithmetic differs in the last bits can still
say they began alike. A comparison names what it tests (`factor`): those
parts may differ, every other must not. Standard library only; the backend computes the
digests (`MujocoBackend.digests`).
"""
import hashlib
import json
from dataclasses import dataclass, fields

PARTS = ('engine', 'model', 'start', 'settled', 'program', 'draw')
GRADES = ('exact', 'rounded')


@dataclass(frozen=True)
class Fingerprint:
    """A set-up's digests: each physical part is (exact, rounded); `program` and `draw` are text
    digests, the same in both grades."""
    engine: str = ''
    model: tuple = ('', '')
    start: tuple = ('', '')
    settled: tuple = ('', '')
    program: str = ''
    draw: str = ''

    def part(self, name, grade='exact'):
        value = getattr(self, name)
        return value[GRADES.index(grade)] if isinstance(value, (tuple, list)) else value

    def code(self, grade='exact', without=()):
        """A short code for the whole set-up - eight hexadecimal digits - to quote a run by."""
        text = '|'.join(f'{p}={self.part(p, grade)}' for p in PARTS if p not in without)
        return hashlib.sha256(text.encode()).hexdigest()[:8]


def fingerprint(backend, start, program=None, variation=None):
    """The set-up's fingerprint now, as the program takes over: `backend.digests` of the model and the
    joints, the joints as they were before the first step (`start`, (qpos, qvel) as kept), the
    program's blocks and the draw's own values (a label alone names a draw, not where it put things)."""
    from dataclasses import asdict, is_dataclass
    now, before = backend.digests(), backend.digests(start, model=False)
    return Fingerprint(now['engine'], now['model'], before['state'], now['state'],
                       text_digest(asdict(program)) if program is not None and is_dataclass(program) else '',
                       text_digest(asdict(variation)) if variation is not None and is_dataclass(variation) else '')


def text_digest(value):
    """A digest of anything JSON can write: a program's blocks, a draw."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:16]


def differ(a, b, grade='exact', factor=()):
    """The parts in which two fingerprints differ, leaving out those named as the factor under
    test; () when they began alike."""
    return tuple(p for p in PARTS if p not in factor and a.part(p, grade) != b.part(p, grade))


@dataclass(frozen=True)
class Verified:
    """What the check of a paired comparison found."""
    pairs: int                  # pairs compared
    same: int                   # began alike in every part but the factor's
    unknown: int                # pairs with a run that has no fingerprint (recorded before FR-041)
    mismatched: tuple = ()      # ((label, parts that differ), ...)
    grade: str = 'exact'
    factor: tuple = ()

    @property
    def clean(self):
        return not self.mismatched and not self.unknown

    def line(self):
        """One sentence for a report."""
        tested = f' ({", ".join(self.factor)} under test)' if self.factor else ''
        if not self.pairs:
            return 'Set-ups verified: no pairs.'
        if self.unknown == self.pairs:
            return f'Set-ups verified: not - the {self.pairs} pairs\' runs were recorded without fingerprints.'
        text = (f'Set-ups verified: {self.same} of {self.pairs} pairs began from the same start, '
                f'{self.grade}{tested}.')
        if self.mismatched:
            shown = '; '.join(f'{label}: {", ".join(parts)}' for label, parts in self.mismatched[:3])
            more = f' and {len(self.mismatched) - 3} more' if len(self.mismatched) > 3 else ''
            text += f' Not the same start: {shown}{more} - read those pairs as two runs.'
        if self.unknown:
            text += f' {self.unknown} without a fingerprint.'
        return text


def check(pairs, grade='exact', factor=()):
    """Check (label, fingerprint a, fingerprint b) pairs; None for a run without one."""
    pairs = tuple(pairs)
    unknown = sum(1 for _, a, b in pairs if a is None or b is None)
    mismatched = tuple((label, differ(a, b, grade, factor)) for label, a, b in pairs
                       if a is not None and b is not None and differ(a, b, grade, factor))
    return Verified(len(pairs), len(pairs) - unknown - len(mismatched), unknown, mismatched, grade, tuple(factor))


def to_dict(f):
    return None if f is None else {x.name: getattr(f, x.name) for x in fields(f)}


def from_dict(d):
    if not d:
        return None
    return Fingerprint(d.get('engine', ''), tuple(d.get('model', ('', ''))), tuple(d.get('start', ('', ''))),
                       tuple(d.get('settled', ('', ''))), d.get('program', ''), d.get('draw', ''))
