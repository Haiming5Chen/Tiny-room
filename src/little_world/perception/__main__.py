"""How well the Fetch table's camera finds its cube, and what that buys (ADR 0032).

    python -m little_world.perception [--pictures 20] [--fetch] [--jobs 2] [--out report.md]

The cube is set down at placements round where the Fetch program plans it - moved up to
8 cm and turned up to 45 degrees - and the table's camera looks for it, once without noise
and then with the RealSense D435's noise, a number of pictures each, the machine at its
start and out of the picture. Prints how far from where the cube really was it was seen.
With `--fetch`, the arm on a cart also runs the Fetch program with the cube set down
elsewhere before the run, blind and looking.
"""
from statistics import median

SHIFTS = tuple((dx, dy) for dx in (-.02, 0., .04, .08) for dy in (-.08, -.04, 0., .04, .08))
TURNS = (0., 15., 30., 45.)
# Where the cube is set down for the Fetch runs: along the table (away from the cart) and
# sideways (to its left), metres, and turned, degrees.
PLACES = ((0., .03, 0.), (0., -.03, 0.), (0., .05, 0.), (0., -.05, 0.), (0., .08, 0.), (0., -.08, 0.),
          (.03, 0., 0.), (.06, 0., 0.), (-.02, 0., 0.), (.03, .05, 0.), (.03, -.05, 0.),
          (0., 0., 20.), (0., 0., 40.), (0., .05, 30.))


def _yaw(quaternion):
    from math import atan2, degrees
    w, x, y, z = quaternion
    return degrees(atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def measure(pictures=20, design='mobile_manipulator'):
    """For the ideal camera and the D435: per placement, the sightings' errors - (position
    error in m, turn error in degrees) each, or None for a picture that did not find it."""
    from little_world import Entity, World
    from little_world.fields import FETCH_CUBE, FIELDS, TABLE
    from little_world.inventory.sweep import design as named
    from little_world.inventory.sweep import eye
    from little_world.physics.mujoco_backend import MujocoBackend
    field = FIELDS['fetch']
    backend = MujocoBackend()
    scene = field.scene(Entity('machine', named(design)))
    planned = (FETCH_CUBE[0], FETCH_CUBE[1], TABLE[4] + .02)
    out = {'ideal': [], 'noisy': []}
    with World(backend, scene) as world:
        world.start()
        cube = backend.model.body('objects/fetch_cube').id
        at = (0., 0., 0.)
        for shift in SHIFTS:
            for turn in TURNS:
                backend.shift('objects/fetch_cube', (shift[0] - at[0], shift[1] - at[1]), turn - at[2])
                at = (*shift, turn)
                truth = backend.data.xpos[cube].copy()
                for kind, count in (('ideal', 1), ('noisy', pictures)):
                    camera = eye(backend, field, scene, ideal=kind == 'ideal')
                    errors = []
                    for _ in range(count):
                        seen = camera('objects/fetch_cube', planned)
                        if seen is None:
                            errors.append(None)
                            continue
                        position = sum((a - b) ** 2 for a, b in zip(seen.centre, truth)) ** .5
                        errors.append((position, abs((seen.yaw - turn + 45) % 90 - 45)))
                    out[kind].append(((*shift, turn), errors))
    return out


def report(measured, pictures):
    lines = ['# The Fetch table camera finding its cube', '',
             f'The cube set down at {len(SHIFTS) * len(TURNS)} placements round where the program plans it '
             f'(moved {min(d for d, _ in SHIFTS) * 100:+.0f} to {max(d for d, _ in SHIFTS) * 100:+.0f} cm '
             f'towards the camera\'s side of the table, {min(d for _, d in SHIFTS) * 100:+.0f} to '
             f'{max(d for _, d in SHIFTS) * 100:+.0f} cm sideways, turned {TURNS[0]:g} to {TURNS[-1]:g} deg), '
             'the machine at its start. Each sighting against where the cube really was (ADR 0032).', '',
             '| Camera | Pictures | Found | Position error, median / largest | Turn error, median / largest |',
             '| --- | --- | --- | --- | --- |']
    for kind, title, count in (('ideal', 'Without noise', 1), ('noisy', 'Intel RealSense D435 noise', pictures)):
        errors = [e for _, row in measured[kind] for e in row]
        found = [e for e in errors if e is not None]
        if not found:
            lines.append(f'| {title} | {len(errors)} | none | - | - |')
            continue
        position = sorted(1000 * p for p, _ in found)
        turn = sorted(t for _, t in found)
        over = sum(1 for t in turn if t > 5.)
        lines.append(f'| {title} | {len(errors)} ({count} a placement) | {len(found)} of {len(errors)} | '
                     f'{median(position):.1f} / {position[-1]:.1f} mm | {median(turn):.1f} / {turn[-1]:.1f} deg'
                     + (f', {over} over 5 |' if over else ' |'))
    worst = max(((p, e[0]) for p, row in measured['noisy'] for e in row if e is not None), key=lambda x: x[1], default=None)
    if worst is not None:
        (dx, dy, turn), error = worst
        lines += ['', f'The largest error with noise: {1000 * error:.1f} mm, the cube moved {100 * dx:+.0f} cm, '
                  f'{100 * dy:+.0f} cm and turned {turn:g} deg.']
    misses = sorted({p for p, row in measured['noisy'] for e in row if e is None})
    if misses:
        lines.append('Not found in some pictures at: ' + '; '.join(f'{100 * dx:+.0f} cm, {100 * dy:+.0f} cm, {t:g} deg'
                                                                   for dx, dy, t in misses) + '.')
    lines += ['', 'A picture is the D435\'s 848 x 480 depth pixels over the region round the planned place, cast '
              'as rays from the camera (MuJoCo `mj_multiRay`), with its noise (depth error z^2 x 0.08 px / '
              '(f x 50 mm)). The cube\'s size is known; its place and turn are measured.', '']
    return '\n'.join(lines)


def _fetch(args):
    from little_world.fields.disturbance import Disturbance
    from little_world.inventory.sweep import run
    blueprint, program, (dx, dy, turn) = args
    moved = Disturbance('set down elsewhere', 'move', part='objects/fetch_cube', offset=(dx, dy), turn=turn)
    return run('fetch', blueprint, program=program, disturbance=moved)


def fetch(jobs=1, design='mobile_manipulator'):
    """The Fetch program, blind and looking, with the cube set down at each of PLACES before
    the run: {'blind': runs, 'looking': runs}, in the order of PLACES."""
    from concurrent.futures import ProcessPoolExecutor
    from little_world.inventory.sweep import design as named, solve
    bp = named(design)
    programs = {'blind': solve('fetch', bp, look=False), 'looking': solve('fetch', bp)}
    work = [(bp, programs[kind], place) for kind in programs for place in PLACES]
    if jobs > 1:
        with ProcessPoolExecutor(jobs) as pool:
            runs = list(pool.map(_fetch, work))
    else:
        runs = [_fetch(w) for w in work]
    return {'blind': runs[:len(PLACES)], 'looking': runs[len(PLACES):]}


def fetch_report(runs):
    from little_world.inventory.sweep import missed_by, off
    lines = ['## The Fetch program with the cube set down elsewhere', '',
             'The arm on a cart as designed, the cube moved and turned before the run starts; the program '
             'planned for it where the field puts it, run blind (`sweep --blind`) and looking.', '',
             '| Cube set down | Blind | Looking | Seen off the plan | Seen off where it was |', '| --- | --- | --- | --- | --- |']

    def cell(r):
        if r.error:
            return f'not run: {r.error}'
        if all(x.status in ('met', 'kept') for x in r.results):
            return f'every goal, {max(x.time for x in r.results if x.time is not None):.1f} s'
        return 'missed: ' + ', '.join(x.label.lower() for x in r.results if x.status not in ('met', 'kept'))
    for (dx, dy, turn), blind, looking in zip(PLACES, runs['blind'], runs['looking']):
        name = f'{100 * dx:+.0f} cm along, {100 * dy:+.0f} cm sideways' + (f', turned {turn:g} deg' if turn else '')
        seen = looking.seen[-1] if looking.seen else None
        lines.append(f'| {name} | {cell(blind)} | {cell(looking)} | '
                     + (f'{100 * off(seen):.1f} cm | {1000 * missed_by(seen):.1f} mm |' if seen else '- | - |'))
    fetched = {k: sum(1 for r in v if not r.error and all(x.status in ('met', 'kept') for x in r.results))
               for k, v in runs.items()}
    lines += ['', f'Every goal blind in {fetched["blind"]} of {len(PLACES)} placements, looking in '
              f'{fetched["looking"]} of {len(PLACES)}.', '']
    return '\n'.join(lines)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(prog='python -m little_world.perception',
                                     description="How well the Fetch table's camera finds its cube.")
    parser.add_argument('--pictures', type=int, default=20, help='pictures with noise at each placement')
    parser.add_argument('--fetch', action='store_true', help='also run the Fetch program with the cube set down elsewhere')
    parser.add_argument('--jobs', type=int, default=1, help='worker processes for the Fetch runs')
    parser.add_argument('--out', help='write the report here as well as printing it')
    args = parser.parse_args(argv)
    text = report(measure(args.pictures), args.pictures)
    if args.fetch:
        text += '\n' + fetch_report(fetch(args.jobs))
    print(text)
    if args.out:
        from pathlib import Path
        Path(args.out).write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
