"""`little-world evidence`: the project's headline measurements, re-run here (ADR 0073).

The documents make physical claims with numbers; the tests hold them inside tolerances and
say pass or fail. This runs thirteen of them again on the machine in front of you and prints
each number beside the one that was recorded - on Linux, MuJoCo 3.10.0, where every number
in the documents was measured - so that anyone can see what holds on their own machine and
what moved. Two record known flaws, kept in the list on purpose: the slope creep (OPEN LW-039)
and the energy a curb's contact gives the cart from nowhere (OPEN LW-047). One checks the
physics check itself (FR-040).

    little-world evidence               every claim, about four minutes on two cores
    little-world evidence --quick       the six that take seconds
    little-world evidence --only fetch tilt
    little-world evidence --list        what is claimed, without running anything
    little-world evidence --json FILE   also write what was measured, to attach to a report
    little-world evidence --markdown    docs/EVIDENCE.md, as this registry writes it

A physics engine is deterministic on one machine and one build, not across them: a different
processor, operating system or MuJoCo release may move a number. That is what the tolerances
are for, and what "differs" reports. Standard library only until a claim is measured.
"""
import argparse
import json
import platform
import sys
import time
from dataclasses import dataclass

RECORDED_ON = 'Linux x86_64, Python 3.13, MuJoCo 3.10.0, 10 Nov 2026'


@dataclass(frozen=True)
class Quantity:
    name: str
    recorded: object            # a number, or True / False / a word for what must be the same
    within: float | None = None     # how far a number may be from the recorded one and still hold; None: the same
    unit: str = ''

    def holds(self, measured):
        if self.within is None or isinstance(self.recorded, (bool, str)) or measured is None:
            return measured == self.recorded
        return isinstance(measured, (int, float)) and abs(measured - self.recorded) <= self.within

    def show(self, value):
        if value is None:
            return 'not reached'
        if isinstance(value, bool):
            return 'yes' if value else 'no'
        if isinstance(value, (int, float)):
            return f'{value:.4g}{" " + self.unit if self.unit else ""}'
        return str(value)


@dataclass(frozen=True)
class Claim:
    id: str
    says: str                   # the claim, as the documents make it
    adr: str                    # the decision record's file under docs/adr/
    test: str                   # the test that holds it: file::test
    quantities: tuple
    measure: object             # () -> {quantity name: what was measured}
    seconds: float              # about how long it takes on two cores
    quick: bool = False
    flaw: str = ''              # set when the claim records something known to be wrong


def _run(field, design, **more):
    from little_world.inventory import sweep
    return sweep.run(field, sweep.design(design), **more)


def _when(run, goal):
    found = run.result(goal)
    return found.time if found is not None and found.status == 'met' else None


def _met(run):
    return all(r.status in ('met', 'kept') for r in run.results) and not run.error


def sprint():
    r = _run('sprint', 'mobile_platform')
    start, finish = _when(r, 'start'), _when(r, 'finish')
    return {'5 m from the start line': None if None in (start, finish) else finish - start,
            'stayed upright': r.result('upright').status == 'kept'}


def curb():
    r = _run('curbs', 'mobile_platform')
    nowhere = [a for a in (r.physics.flagged if r.physics else ()) if 'field/curb_10mm' in a.bodies]
    return {'10 mm curb cleared at': _when(r, 'curb_10'), '20 mm curb cleared': _when(r, 'curb_20') is not None,
            '35 mm curb cleared': _when(r, 'curb_35') is not None,
            'energy from nowhere at the 10 mm curb, as a lift of the cart': 1000 * max((a.lifted for a in nowhere), default=0.)}


def physics():
    """The physics check's controls (FR-040): a 5 cm block dropped 5 cm onto a fixed slab, and one
    started 5 mm inside it; what the slab's contact gave back beyond what it took, as a lift of the block."""
    from little_world import World
    from little_world.components import Transform, box
    from little_world.core.scene import Scene
    from little_world.fields import field_entities, fixed
    from little_world.inventory.artifacts import GIVE, Watch
    from little_world.physics.mujoco_backend import MujocoBackend
    out = {}
    for name, lift in (('dropped 5 cm onto a slab: given back', .05), ('started 5 mm inside it: pushed out with', -.005)):
        entities = field_entities([fixed('slab', (.6, .6, .04), 'slab', (0., 0., .3))],
                                  [box('block', (.05, .05, .05), 'cube', dynamic=True, transform=Transform((0., 0., .345 + lift)))])
        backend, watch = MujocoBackend(), Watch()
        with World(backend, Scene(entities)) as world:
            world.start()
            for _ in range(750):
                state = world.step({})
                watch.update(backend, state.time)
        out[name] = 1000 * GIVE * watch.result().worst
    return out


def tilt():
    r = _run('tilt', 'mobile_manipulator')
    return {'went over at': r.tipped, 'its design predicts': r.predicted}


def tilt_cart():
    r = _run('tilt', 'mobile_platform')
    return {'held at the table\'s 60 deg': r.tipped is None and _when(r, 'held_60') is not None,
            'its design predicts': r.predicted}


def doorway():
    r = _run('doorway', 'mobile_platform')
    return {'through the doorway at': _when(r, 'through'), 'parked in the bay at': _when(r, 'parked'),
            'door frame untouched': r.result('frame').status == 'kept'}


def pick_place():
    r = _run('pick_place', 'arm_lab')
    return {'cube lifted at': _when(r, 'lifted'), 'resting in the tray at': _when(r, 'placed')}


def fetch():
    r = _run('fetch', 'mobile_manipulator')
    return {'every goal met': _met(r), 'cube in the bin at': _when(r, 'delivered'), 'looked again': r.regrasped}


def fetch_felt():
    from little_world.fields.disturbance import DEFAULTS
    moved = next(d for d in DEFAULTS['fetch'] if d.label == 'cube moved 5 cm sideways, 2 s later')
    r = _run('fetch', 'mobile_manipulator', disturbance=moved)
    return {'every goal met': _met(r), 'the arm rose off the cube at': r.recovered[0] if r.recovered else None,
            'why': r.message if not r.recovered else 'felt it' if r.recovered[0] < 18.5 else 'timed out on it',
            'cube in the bin at': _when(r, 'delivered')}


def slope_creep():
    """A 5 cm wooden block on a concrete slope, friction 0.4: inside its 21.8 deg friction angle it
    should stand still; how fast it creeps from 1 to 3 s (OPEN LW-039)."""
    from math import cos, radians, sin
    from little_world import World
    from little_world.components import Transform, box
    from little_world.core.scene import Scene
    from little_world.fields import field_entities, fixed
    from little_world.physics.mujoco_backend import MujocoBackend
    out = {}
    for theta in (5., 15.):
        s = radians(theta)
        turn = (cos(s / 2), sin(s / 2), 0., 0.)
        up = (0., -sin(s), cos(s))
        at = tuple(c + .04 * u for c, u in zip((0., 0., .3), up))
        entities = field_entities([fixed('ramp', (.6, .6, .04), 'slab', (0., 0., .3), turn)],
                                  [box('block', (.05, .05, .04), 'cube', dynamic=True, transform=Transform(at, turn))])
        with World(MujocoBackend(), Scene(entities)) as world:
            world.start()
            marks = {}
            for _ in range(round(3. / world.timestep)):
                state = world.step({})
                if round(state.time, 3) in (1., 3.):
                    marks[round(state.time, 3)] = state.bodies['objects/block'].pose.position
        out[f'creep on {theta:.0f} deg'] = 1000 * sum((a - b) ** 2 for a, b in zip(marks[1.], marks[3.])) ** .5 / 2.
    return out


def conveyor():
    from little_world import Entity, World
    from little_world.fields import FIELDS
    from little_world.fields.goals import GoalTracker
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    field = FIELDS['conveyor']
    with World(MujocoBackend(), field.scene(Entity('machine', mobile_manipulator_blueprint()))) as world:
        state = world.start()
        tracker = GoalTracker(field.goals, 'machine/root')
        for _ in range(round(4. / world.timestep)):
            state = world.step(field.commands(state))
            tracker.update(state)
        found = {r.id: r for r in tracker.results(finished=True)}
    at = lambda goal: found[goal].time if found[goal].status == 'met' else None
    return {'first pallet at the stop at': at('pallet_1'), 'second queued behind it at': at('pallet_2'),
            'the cube still on its pallet': found['cube_1'].status == 'met'}


def cell():
    """Real's factory cell: the Panda puts two small blocks in their slots, the second fed 3.6 mm
    off its place and turned 10 degrees."""
    from little_world.factory.controller import FactoryCycle
    from little_world.factory.scene import factory_scene, stock_name
    from little_world.physics.mujoco_backend import MujocoBackend
    backend = MujocoBackend()
    backend.compile(factory_scene(stock=1), .002)
    try:
        cycle = FactoryCycle(backend)
        cycle.feeder = {0: (0., 0., 0.), 1: (.003, -.002, 10.)}.__getitem__
        cycle.production(['objects/' + stock_name(i) for i in range(2)], 'Amber')
        for _ in range(int(40 / .002)):
            backend.step(cycle.commands(.002))
            if cycle.state == 'failed' or (cycle.state == 'completed' and cycle.run['done'] == 2):
                break
        placed = list(cycle.run['placements'])
        done = cycle.state == 'completed' and len(placed) == 2
    finally:
        backend.close()
    return {'both parts placed': done,
            'furthest from its slot': max((p.dx ** 2 + p.dy ** 2) ** .5 for p in placed) if done else None,
            'most it was left turned': max(abs(p.yaw) for p in placed) if done else None,
            'slowest part': max(p.seconds for p in placed) if done else None}


def twice():
    """The same run, twice: every step's state the same to the last bit (ADR 0036)."""
    first, second = [], []
    _run('pick_place', 'arm_lab', trace=first)
    _run('pick_place', 'arm_lab', trace=second)
    return {'steps compared': len(first), 'the two runs differ at': next(
        (i for i, (a, b) in enumerate(zip(first, second)) if a != b), 'no step') if len(first) == len(second) else 'their lengths'}


Q = Quantity
CLAIMS = (
    Claim('sprint', 'The kit cart covers the 5 m sprint in 11.8 s: its drive assist\'s 0.425 m/s sets the time, not its motors.',
          '0013-test-fields.md', 'test_fields.py::test_the_sprint_is_timed_by_the_drive_assist_speed',
          (Q('5 m from the start line', 11.85, .35, 's'), Q('stayed upright', True)), sprint, 17, quick=True),
    Claim('curb', 'On all four wheels the kit cart clears a 10 mm curb, slowly - at 10.4 s - and not a 20 or 35 mm one.',
          '0041-the-cart-stands-on-all-four.md', 'test_fields.py::test_on_all_four_wheels_the_cart_stalls_at_a_curb_and_gets_over_only_slewed_onto_a_drive_wheel',
          (Q('10 mm curb cleared at', 10.36, 1.5, 's'), Q('20 mm curb cleared', False), Q('35 mm curb cleared', False),
           Q('energy from nowhere at the 10 mm curb, as a lift of the cart', 4.59, 2., 'mm')), curb, 14,
          flaw='Before it climbs, the contact between a swivel caster\'s wheel and the curb\'s edge gives the cart energy it never '
               'took (FR-040, OPEN LW-047): one contact point between a cylinder and a box (multiccd off, ADR 0027), with noslip on. '
               'With multiccd on the check is clean and the curb is cleared at 11.4 s.'),
    Claim('tilt', 'On the tilt table the arm on its cart goes over at 54.6 deg, a degree before the 55.6 its design predicts.',
          '0029-tilt-test-squares-the-machine.md', 'test_tipping.py::test_on_the_tilt_table_the_angle_runs_out_as_the_arm_cart_goes_over',
          (Q('went over at', 54.61, 1., 'deg'), Q('its design predicts', 55.58, .05, 'deg')), tilt, 22),
    Claim('tilt-cart', 'The cart without its arm still stands at the table\'s 60 deg; its design predicts 72.',
          '0059-how-near-it-is-to-tipping.md', 'test_tipping.py::test_the_cart_without_its_arm_keeps_twelve_degrees_at_the_tables_top',
          (Q('held at the table\'s 60 deg', True), Q('its design predicts', 71.95, .05, 'deg')), tilt_cart, 20),
    Claim('doorway', 'The kit cart drives through a doorway and parks in the bay beyond without touching the frame.',
          '0018-fetch-drive-to-a-point.md', 'test_more_fields.py::test_the_doorway_program_takes_the_platform_through_without_touching_the_frame',
          (Q('through the doorway at', 14.37, 1., 's'), Q('parked in the bay at', 16.54, 1., 's'), Q('door frame untouched', True)),
          doorway, 22),
    Claim('pick-place', 'The arm lab lifts its cube by finger contact and rests it in the tray.',
          '0016-arm-tasks-tool-moves-poses-grasp-checks.md', 'test_arm_tasks.py::test_the_pick_and_place_template_meets_the_fields_goals',
          (Q('cube lifted at', 1.902, .2, 's'), Q('resting in the tray at', 5.724, .5, 's')), pick_place, 2, quick=True),
    Claim('fetch', 'The arm on its cart drives 1.8 m to a table, finds the cube with its camera, picks it up, brings it back '
          'and sets it in the bin: every goal met, the cube in the bin at 36.9 s, without looking twice.',
          '0042-set-down-not-dropped.md', 'test_fetch.py::test_the_mobile_manipulator_fetches_the_cube_by_itself',
          (Q('every goal met', True), Q('cube in the bin at', 36.87, 1., 's'), Q('looked again', 0)), fetch, 35),
    Claim('fetch-felt', 'The cube moved 5 cm just after the camera looked: a jaw comes down on it, the arm\'s servos feel it and '
          'the arm rises 0.2 s later, looks again and fetches it.',
          '0071-a-reach-that-feels-what-it-meets.md', 'test_felt_reach.py::test_the_cube_moved_under_a_jaw_is_felt_at_once_and_not_pressed_for_two_seconds',
          (Q('every goal met', True), Q('the arm rose off the cube at', 17.44, .5, 's'), Q('why', 'felt it'),
           Q('cube in the bin at', 40.83, 1.5, 's')), fetch_felt, 45),
    Claim('physics', 'A contact gives back no more energy than it took: a block dropped onto a slab is given none of its fall back; '
          'one started 5 mm inside the slab is pushed out with as much as lifting it 5 mm takes, and the check flags it.',
          '0074-energy-from-nowhere.md', 'test_artifacts.py::test_a_block_started_inside_a_slab_is_pushed_out_with_energy_from_nowhere_and_flagged',
          (Q('dropped 5 cm onto a slab: given back', 0., .05, 'mm'), Q('started 5 mm inside it: pushed out with', 4.99, .2, 'mm')),
          physics, 2, quick=True),
    Claim('slope-creep', 'A block resting on a slope inside its friction angle should stand still. It creeps: 0.2 mm/s on 5 deg, '
          '1.4 mm/s on 15 deg.',
          '0061-how-close-to-slipping.md', 'test_friction_use.py::test_a_block_on_a_slope_uses_tan_theta_over_mu_of_its_friction_until_it_slides',
          (Q('creep on 5 deg', .21, .1, 'mm/s'), Q('creep on 15 deg', 1.36, .4, 'mm/s')), slope_creep, 2, quick=True,
          flaw='MuJoCo\'s pyramidal friction cones let a resting contact creep (OPEN LW-039); every friction result here rests on them.'),
    Claim('conveyor', 'A roller conveyor carries two pallets at 0.1 m/s to a stop: the first arrives at 1.7 s, the second queues behind it.',
          '0067-a-roller-conveyor.md', 'test_conveyor.py::test_pallets_ride_at_the_rollers_speed_to_the_stop_and_queue',
          (Q('first pallet at the stop at', 1.72, .15, 's'), Q('second queued behind it at', 1.92, .15, 's'),
           Q('the cube still on its pallet', True)), conveyor, 4, quick=True),
    Claim('cell', 'In Real\'s factory cell the Panda puts each part within a millimetre of its slot and squares up one fed turned '
          '10 deg, 12 to 14 s a part.',
          '0065-the-panda-holds-itself-up.md', 'test_process_window.py::test_a_production_run_says_where_each_part_was_left_and_a_fed_part_off_centre_is_still_placed',
          (Q('both parts placed', True), Q('furthest from its slot', .62, .6, 'mm'), Q('most it was left turned', 1.6, 1.4, 'deg'),
           Q('slowest part', 13.93, 1.5, 's')), cell, 20),
    Claim('twice', 'A run repeated on the same machine is the same run, bit for bit: paired comparisons rest on it.',
          '0036-paired-runs.md', 'test_paired_runs.py::test_the_two_runs_of_a_fetch_pair_are_one_run_until_the_cube_is_moved',
          (Q('the two runs differ at', 'no step'),), twice, 4, quick=True),
)
BY_ID = {c.id: c for c in CLAIMS}


def here():
    try:
        import mujoco
        engine = mujoco.__version__
    except Exception:
        engine = 'not installed'
    return f'{platform.system()} {platform.machine()}, Python {platform.python_version()}, MuJoCo {engine}'


def check(claims, out=None):
    """Measure each claim and print it beside what was recorded. Returns [(claim, {name: measured}, error)]."""
    out = out or sys.stdout
    results = []
    for claim in claims:
        print(f'\n{claim.id}  -  {claim.says}', file=out)
        print(f'    docs/adr/{claim.adr}  /  tests/{claim.test}', file=out)
        if claim.flaw:
            print(f'    A known flaw, recorded as it is: {claim.flaw}', file=out)
        out.flush()
        started = time.perf_counter()
        try:
            measured, error = claim.measure(), ''
        except Exception as problem:                # a claim that cannot be measured here is a finding, not a crash
            measured, error = {}, f'{type(problem).__name__}: {problem}'
        took = time.perf_counter() - started
        width = max(len(q.name) for q in claim.quantities)
        for q in claim.quantities:
            value = measured.get(q.name)
            verdict = 'could not be measured' if error else 'holds' if q.holds(value) else 'DIFFERS'
            margin = f' (within {q.show(q.within)})' if q.within is not None and not isinstance(q.recorded, (bool, str)) else ''
            print(f'    {q.name:<{width}}   recorded {q.show(q.recorded):<12} here {q.show(value) if not error else "-":<12} {verdict}{margin}', file=out)
        if error:
            print(f'    {error}', file=out)
        print(f'    ({took:.0f} s)', file=out)
        results.append((claim, measured, error))
    return results


def summary(results):
    total = sum(len(c.quantities) for c, _, _ in results)
    held = sum(1 for c, m, e in results if not e for q in c.quantities if q.holds(m.get(q.name)))
    return held, total


def markdown():
    """docs/EVIDENCE.md, from the registry."""
    lines = ['# Evidence: what is claimed, where it was measured, and how to measure it again', '',
             'Written by `little-world evidence --markdown` from `src/little_world/evidence.py`; a test keeps the two the same.', '',
             'Every physical claim in this project has a number, a decision record that explains it and a test that holds',
             'it. This page lists thirteen headline claims with the numbers recorded for them',
             f'({RECORDED_ON}) and the tolerance inside which a re-run still counts as holding. Run', '',
             '```sh', 'little-world evidence            # all of them, about four minutes on two cores',
             'little-world evidence --quick    # the six that take seconds',
             'little-world evidence --only fetch tilt --json mine.json', '```', '',
             'and each number is measured again on your machine and printed beside the recorded one. A physics engine',
             'is deterministic on one machine and build, not across processors, operating systems or MuJoCo releases:',
             'a number that moves on your machine is a finding worth an issue, with the `--json` file attached.', '',
             'One claim is a flaw recorded as it is, not something to be proud of; [the evaluation](EVALUATION.md) lists more.', '']
    for c in CLAIMS:
        lines += [f'## `{c.id}`', '', c.says, '']
        if c.flaw:
            lines += [f'*A known flaw:* {c.flaw}', '']
        lines += ['| Measured | Recorded | Holds within |', '| --- | --- | --- |']
        for q in c.quantities:
            exact = q.within is None or isinstance(q.recorded, (bool, str))
            lines.append(f'| {q.name} | {q.show(q.recorded)} | {"the same" if exact else q.show(q.within)} |')
        lines += ['', f'Why: [docs/adr/{c.adr}](adr/{c.adr}). Held by `tests/{c.test}`. '
                  f'Again: `little-world evidence --only {c.id}` (about {c.seconds:.0f} s).', '']
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='little-world evidence', description=__doc__.split('\n\n')[0])
    parser.add_argument('--quick', action='store_true', help='only the claims that take seconds')
    parser.add_argument('--only', nargs='+', metavar='ID', help='only these claims')
    parser.add_argument('--list', action='store_true', help='say what is claimed and run nothing')
    parser.add_argument('--json', metavar='FILE', help='also write what was measured here')
    parser.add_argument('--markdown', action='store_true', help='print docs/EVIDENCE.md')
    args = parser.parse_args(argv)
    if args.markdown:
        print(markdown())
        return 0
    unknown = [i for i in args.only or () if i not in BY_ID]
    if unknown:
        parser.error(f'no claim called {", ".join(unknown)}; they are: {", ".join(BY_ID)}')
    claims = [c for c in CLAIMS if (not args.only or c.id in args.only) and (not args.quick or c.quick)]
    if args.list:
        for c in claims:
            print(f'{c.id:<12} about {c.seconds:>3.0f} s   {c.says}')
        return 0
    print(f'Here:      {here()}\nRecorded:  {RECORDED_ON}')
    try:
        import mujoco  # noqa: F401
    except ImportError:
        print('\nMuJoCo is not installed, so nothing can be measured: run  little-world doctor  for the line that installs it.')
        return 1
    started = time.perf_counter()
    results = check(claims)
    held, total = summary(results)
    took = time.perf_counter() - started
    print(f'\n{held} of {total} measurements hold here ({len(claims)} claims, {took / 60:.1f} min).'
          + ('' if held == total else '  What differs is worth reporting with the --json file: it is how this project finds where it is wrong.'))
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(dict(here=here(), recorded_on=RECORDED_ON, held=held, total=total, claims=[
                dict(id=c.id, error=e, measured={k: v for k, v in m.items()},
                     recorded={q.name: q.recorded for q in c.quantities},
                     holds={q.name: (not e) and q.holds(m.get(q.name)) for q in c.quantities}) for c, m, e in results]), f, indent=1)
        print(f'Written to {args.json}.')
    return 0 if held == total else 1


if __name__ == '__main__':
    sys.exit(main())
