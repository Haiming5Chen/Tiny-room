"""A field run repeated over variations, and the spread of what it measured (ADR 0024).

Never touches the interactive world: every run compiles its own. A protocol says what the
machine does in the field: holds still (a static test, such as the tilt table); drives
straight ahead at its full configured speed, as the W key does (sprint, ramps, curbs, push);
or runs the field's program template - solved once for the machine as designed and set down
on its mark, then run unchanged on every variation, as a program written in a lab runs
however the machine was put down that day.

    python -m little_world.inventory.sweep tilt --design mobile_manipulator
"""
from dataclasses import dataclass
from statistics import median
import time

from little_world.fields import FIELDS
from little_world.fields.disturbance import DEFAULTS, Disturbing
from little_world.fields.variation import CameraError, Ranges, Variation, friction, payload_site, plan, varied
from little_world.inventory.confidence import CONFIDENCE, interval, lower_bound, mcnemar, runs_needed, upper_bound

# Field -> (protocol, seconds). Fields not listed have no protocol a machine can follow alone.
PROTOCOLS = {'tilt': ('hold', 33.), 'fetch': ('program', 60.), 'pick_place': ('program', 40.),
             'doorway': ('program', 45.), 'sprint': ('drive', 20.), 'ramps': ('drive', 12.),
             'curbs': ('drive', 13.), 'push': ('drive', 12.)}
AHEAD = (5., 5.)        # both sides full forward, as the W key asks
SETTLE = 300            # steps a machine stands before its program is solved or started
AFTER = 1.5             # s held still after a program ends, so resting goals can be judged
DESIGNS = ('mobile_platform', 'mobile_manipulator', 'two_wheel', 'arm_lab')


@dataclass(frozen=True)
class Run:
    """One variation's run: its goals' results, or why it could not run."""
    variation: Variation
    results: tuple = ()             # fields.goals.Result, one per goal
    tipped: float | None = None     # a static test's reading when the machine went over
    predicted: float | None = None  # what the design predicts for it, this variation
    program: str = ''               # the program's final state, '' when none ran
    error: str = ''
    seconds: float = 0.             # wall clock
    disturbed: str = ''             # what a disturbance did, '' when there was none (ADR 0030)
    pushed: float | None = None     # how far a push moved the machine's base, the way it pushed (m)
    went_back: int = 0              # times the program went back to a stop it was pushed off (ADR 0031)
    seen: tuple = ()                # each look's (object, where planned, where seen, where it was) (ADR 0032)
    regrasped: int = 0              # times the program looked again after a missed grasp (ADR 0033)
    message: str = ''               # the program's last word: why it stopped, when it failed
    event: float | None = None      # when the disturbance began, simulated seconds; None if it never did
    handled: tuple = ()             # how each handled part was treated (ADR 0040): handling.Handled, one a part

    def result(self, goal):
        return next((r for r in self.results if r.id == goal), None)


@dataclass(frozen=True)
class Sweep:
    field: str
    design: str
    protocol: str
    duration: float
    site: tuple | None
    ranges: Ranges
    runs: tuple
    camera: CameraError | None = None   # the field's camera off where it is believed to be (ADR 0039)


def design(name):
    """An example machine by name, or a saved design from a Blueprint JSON file."""
    from pathlib import Path
    from little_world.core.blueprint import Blueprint
    if name in DESIGNS:
        module = __import__(f'little_world.robots.{name}', fromlist=['_'])
        return getattr(module, f'{name}_blueprint')()
    path = Path(name)
    if not path.is_file():
        raise ValueError(f'no example design or file called {name!r}; examples: {", ".join(DESIGNS)}')
    return Blueprint.from_json(path.read_text(encoding='utf-8'))


def _root(bp):
    from little_world.core.component import Body
    return 'machine/' + next(b.id for b in bp.components if isinstance(b, Body) and b.parent is None)


def _rigs(backend, bp):
    from little_world.control.mujoco_drive import MujocoDrive
    from little_world.control.mujoco_keyboard import MujocoKeyboardControl
    from little_world.control.navigation import BasePose
    drive, control = MujocoDrive(backend, bp), MujocoKeyboardControl(backend, bp)
    try:
        base = BasePose(backend, drive, bp)
    except ValueError:
        base = None
    return drive, control, base


def _hold(world, drive, control, field, state):
    commands = dict(drive.step_commands((0., 0.), world.timestep, angular=True))
    commands.update(control.step_commands(world.timestep))
    commands.update(field.commands(state))
    return world.step(commands)


def solve(field_id, blueprint, look=True):
    """The field's program template, solved for the machine as designed on its mark; it
    looks with the field's camera, when the field has one, unless `look` is False."""
    from little_world import Entity, World
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.programming.program import Block, Program
    import little_world.fields as fields
    field = FIELDS[field_id]
    backend = MujocoBackend()
    with World(backend, field.scene(Entity('machine', blueprint))) as world:
        state = world.start()
        drive, control, base = _rigs(backend, blueprint)
        for _ in range(SETTLE):
            state = _hold(world, drive, control, field, state)
        if field_id == 'doorway':
            if base is None:
                raise ValueError('the Doorway program needs a left and a right drive wheel')
            (x0, y0), (x1, y1) = fields.BAY
            stops = ((fields.WALL_X - .7, fields.DOOR_Y, 0.), (fields.WALL_X + .6, fields.DOOR_Y, 0.),
                     ((x0 + x1) / 2, (y0 + y1) / 2, 0.))
            return Program(tuple(Block('goto', value=.02, duration=40., point=p) for p in stops))
        from little_world.control.tool_motion import ToolMotion, fetch, pick_and_place
        motion = ToolMotion(backend, blueprint, control)
        jaws = next((s.id for s in control.specs if s.actuators and set(s.actuators) <= set(motion.jaws)), None)
        if jaws is None:
            raise ValueError('the program needs the gripper bound to a keyboard action')
        model, data = backend.model, backend.data

        def top(body):
            b = model.body(body).id
            return float(data.xpos[b][2] + max(model.geom_size[g][2] for g in range(model.ngeom) if model.geom_bodyid[g] == b))
        if field_id == 'pick_place':
            tray = model.body('field/tray_base').id
            return pick_and_place(motion, jaws, (float(data.xpos[tray][0]), float(data.xpos[tray][1]), top('field/tray_base')))
        if base is None:
            raise ValueError('the Fetch program needs a left and a right drive wheel')
        place = (fields.BIN[0], fields.BIN[1], top('field/bin_base'))
        return fetch(motion, base, jaws, 'objects/fetch_cube', place, reach_in=fields.BIN_SIZE / 2 - .045,
                     look=look and bool(field.camera))


def ranges_for(field_id):
    """The variation ranges a field's sweep uses: a field that sets the machine square
    before it starts (the tilt table, ADR 0029) leaves turning out - it would be undone."""
    return Ranges(turn=0.) if FIELDS[field_id].squared else Ranges()


def run(field_id, blueprint, variation=Variation(), program=None, site=None, disturbance=None, corrections=None,
        retries=None, ideal=False, regrasps=None, trace=None, checks=None, camera_error=None, timestep=None):
    """One run of a field under one variation, and a disturbance partway through if one is
    given (ADR 0030). A program field's program, when not given, is solved for `blueprint`
    as designed; `corrections` caps an aimed pose's corrections (ADR 0025), `retries` how
    often the program may go back to a stop it was pushed off (ADR 0031) and `regrasps` how
    often it may look again after a missed grasp (ADR 0033); None: the runner's own.
    A program that looks does so with the field's camera, its sensor's noise drawn for this
    set-up, or without noise if `ideal` (ADR 0032); `checks` False takes every picture as new
    and lit (ADR 0038; None: the runner's own). `camera_error` sets the field's camera off the
    pose the program believes it at (ADR 0039); `timestep`, seconds a step (None: the world's
    own, 2 ms). The parts the field's goals carry are watched for how they are handled (ADR
    0040). `trace`, a list, gets each step's time and
    a digest of every body's position and speed: what makes a set-up's undisturbed and
    disturbed runs one run until the event (ADR 0036)."""
    from little_world import Entity, World
    from little_world.fields.goals import GoalTracker
    from little_world.physics.mujoco_backend import MujocoBackend
    started = time.monotonic()
    field = FIELDS[field_id]
    protocol, duration = PROTOCOLS[field_id]
    if protocol == 'program' and program is None:
        program = solve(field_id, blueprint)
    try:
        bp = varied(blueprint, variation, site)
    except ValueError as error:
        return Run(variation, error=str(error))
    if field.squared:               # predicted for the machine as the field will stand it (ADR 0029)
        from little_world.fields import squared
        bp = squared(bp)
    predicted = None
    if field.reading is not None and field.side is not None:
        from little_world.construction.structure import standing
        from little_world.fields import railed
        stance = standing(bp)
        tip = stance.tip(field.side) if stance is not None else None
        if tip is not None:
            predicted = railed(tip, stance.height) if field.fitted else tip
    backend = MujocoBackend()
    scene = field.scene(Entity('machine', bp))
    from little_world.inventory.handling import Watching
    with World(backend, scene, **({'timestep': timestep} if timestep else {})) as world:
        state = world.start()
        table = friction(variation)
        if table:
            backend.vary_pair_friction(table)
        drive, control, base = _rigs(backend, bp)
        steps = round(duration / world.timestep)
        runner = None
        kick = Disturbing(disturbance, _root(bp)) if disturbance is not None else None
        watching = tuple(Watching(part) for part in handled_parts(field))

        def watch(state):
            tracker.update(state)
            for w in watching:
                w.update(backend, state, world.timestep)
            if kick is not None:
                kick.tick(backend, state, state.time - tracker.start, tracker.met)
            if trace is not None:
                trace.append((state.time, _digest(backend)))
        if protocol == 'program':
            from little_world.programming.execution import apply, base_targets, joint_angles, needs_grasp
            from little_world.programming.observations import Observations
            from little_world.programming.program import Runner
            from little_world.control.tool_motion import ToolMotion
            for _ in range(round(SETTLE * .002 / world.timestep)):
                state = _hold(world, drive, control, field, state)
            tracker = GoalTracker(field.goals, _root(bp))
            obs = Observations(backend.model, backend.data)
            try:
                aim = ToolMotion(backend, bp, control).aim     # aimed poses checked (ADR 0025)
            except ValueError:
                aim = None
            caps = {k: v for k, v in (('corrections', corrections), ('retries', retries), ('regrasps', regrasps),
                                      ('checks', checks))
                    if v is not None}
            runner = Runner(**caps)
            runner.start(program)
            try:
                believed = None
                if camera_error is not None and not camera_error.nominal and field.camera:
                    name = f'field/{field.camera[0]}'
                    believed = backend.camera_pose(name)        # as calibrated
                    backend.move_camera(name, camera_error.shift, camera_error.turn)
                see = (eye(backend, field, scene, variation, ideal, believed)
                       if any(b.kind == 'look' for b in program.blocks) else None)
                if kick is not None:
                    kick.camera = see       # what a camera fault fails (ADR 0038)
            except ValueError as error:
                return Run(variation, error=str(error))
            actual = []         # where each looked-for object really was: measured, not seen
            for _ in range(steps):
                contacts, distances = obs.program_inputs(program)
                held = obs.grasped() if needs_grasp(program) else frozenset()
                out = runner.tick(world.timestep, joint_angles(control), contacts, distances, held,
                                  base.pose() if base else None, aim, see)
                if len(runner.seen) > len(actual):
                    body = backend.model.body(runner.seen[-1][0]).id
                    actual.append(tuple(float(v) for v in backend.data.xpos[body]))
                control.held = apply(out, control)
                ahead = base_targets(out, base) if out['base'] else out['drive']
                commands = dict(drive.step_commands(ahead, world.timestep, angular=True))
                commands.update(control.step_commands(world.timestep))
                commands.update(field.commands(state))
                state = world.step(commands)
                watch(state)
                if runner.state != 'running':
                    break
            control.held = set()
            for _ in range(round(AFTER / world.timestep)):
                state = _hold(world, drive, control, field, state)
                watch(state)
        else:
            tracker = GoalTracker(field.goals, _root(bp))
            tracker.update(state)
            for _ in range(steps):
                if protocol == 'drive':
                    commands = dict(drive.step_commands(AHEAD, world.timestep))
                    commands.update(control.step_commands(world.timestep))
                    commands.update(field.commands(state))
                    state = world.step(commands)
                else:
                    state = _hold(world, drive, control, field, state)
                watch(state)
        return Run(variation, tracker.results(finished=True), tracker.tipped_at, predicted,
                   runner.state if runner else '', '', time.monotonic() - started,
                   kick.note() if kick is not None else '', kick.moved if kick is not None else None,
                   runner.retries if runner else 0,
                   tuple((*look, at) for look, at in zip(runner.seen, actual)) if runner else (),
                   runner.regrasps if runner else 0, runner.message if runner else '',
                   kick.began + tracker.start if kick is not None and kick.began is not None else None,
                   tuple(w.result() for w in watching))


def handled_parts(field):
    """The parts a field's goals carry somewhere - the Fetch cube - whose handling is watched."""
    return tuple(sorted({g.target for g in field.goals if getattr(g, 'target', '')}))


def _digest(backend):
    """A short digest of every joint's position and speed, bit for bit."""
    from hashlib import blake2b
    d = backend.data
    return blake2b(d.qpos.tobytes() + d.qvel.tobytes(), digest_size=8).hexdigest()


def eye(backend, field, scene, variation=Variation(), ideal=False, believed=None):
    """The field's depth camera for a program's looks (ADR 0032), its noise drawn from a
    seed of the set-up's own, so a set-up sees the same noise however it is disturbed."""
    from zlib import crc32
    from little_world.perception.eye import Eye, sizes_in
    from little_world.perception.sensors import SENSORS
    if not field.camera:
        raise ValueError(f'the {field.id} field has no camera to look with')
    camera, sensor = field.camera
    return Eye(backend, f'field/{camera}', SENSORS[sensor], sizes_in(scene), crc32(variation.label.encode()), ideal,
               believed)


def _one(args):
    return run(*args)


def sweep(field_id, blueprint, variations=None, name='design', site=None, jobs=1, progress=None,
          ranges=Ranges(), corrections=None, retries=None, blind=False, regrasps=None, camera_error=None):
    """Every variation's run of a field (by default the plan for `ranges`);
    `progress(done, total, run)` after each. `corrections` caps aimed poses' corrections;
    `blind` runs the program without its looks (ADR 0032); `camera_error` sets the field's
    camera off where the program believes it, in every run (ADR 0039)."""
    if field_id not in PROTOCOLS:
        raise ValueError(f'the {field_id} field has no protocol a machine can follow alone; '
                         f'fields that do: {", ".join(sorted(PROTOCOLS))}')
    variations = tuple(variations if variations is not None else plan(ranges))
    if any(v.payload for v in variations) and site is None:
        try:
            site = payload_site(blueprint, max(v.payload for v in variations))
        except ValueError:
            site = None     # each loaded run then reports why it could not be loaded
    protocol, duration = PROTOCOLS[field_id]
    program = solve(field_id, blueprint, look=not blind) if protocol == 'program' else None
    work = [(field_id, blueprint, v, program, site, None, corrections, retries, False, regrasps, None, None, camera_error)
            for v in variations]
    runs = []
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(jobs) as pool:
            for r in pool.map(_one, work):
                runs.append(r)
                if progress:
                    progress(len(runs), len(work), r)
    else:
        for w in work:
            runs.append(_one(w))
            if progress:
                progress(len(runs), len(work), runs[-1])
    return Sweep(field_id, name, protocol, duration, site, ranges, tuple(runs),
                 camera_error if camera_error is not None and not camera_error.nominal else None)


@dataclass(frozen=True)
class Disturbed:
    """The same set-ups run undisturbed and under each disturbance (ADR 0030)."""
    field: str
    design: str
    protocol: str
    duration: float
    site: tuple | None
    ranges: Ranges
    corrections: int | None         # an aimed pose's corrections, capped; None: the runner's own
    groups: tuple                   # ((label, description, runs), ...), undisturbed first
    retries: int | None = None      # going back to a stop, capped (ADR 0031); None: the runner's own
    blind: bool = False             # the program ran without its looks (ADR 0032)
    regrasps: int | None = None     # looking again after a missed grasp, capped (ADR 0033); None: the runner's own
    checks: bool | None = None      # False: every picture taken as new and lit (ADR 0038); None: the runner's own


def setups(ranges=Ranges(), samples=8, seed=1):
    """What a disturbance is tried on: the design as designed and the set-ups drawn at random
    by the same plan a sweep uses, so that the two can be read side by side."""
    return tuple(v for v in plan(ranges, samples, seed) if v.nominal or v.label.startswith('repeat'))


def disturb(field_id, blueprint, disturbances=None, name='design', samples=8, seed=1, jobs=1, progress=None,
            corrections=None, retries=None, blind=False, regrasps=None, checks=None):
    """Every set-up run undisturbed and then under each disturbance (by default the field's
    own, `fields.disturbance.DEFAULTS`); `progress(done, total, run)` after each."""
    if field_id not in PROTOCOLS:
        raise ValueError(f'the {field_id} field has no protocol a machine can follow alone; '
                         f'fields that do: {", ".join(sorted(PROTOCOLS))}')
    disturbances = tuple(disturbances if disturbances is not None else DEFAULTS.get(field_id, ()))
    if not disturbances:
        raise ValueError(f'nothing is defined to disturb the {field_id} field; fields that have it: '
                         f'{", ".join(sorted(DEFAULTS))}')
    ranges = ranges_for(field_id)
    variations = setups(ranges, samples, seed)
    site = None
    if any(v.payload for v in variations):
        try:
            site = payload_site(blueprint, max(v.payload for v in variations))
        except ValueError:
            site = None
    protocol, duration = PROTOCOLS[field_id]
    program = solve(field_id, blueprint, look=not blind) if protocol == 'program' else None
    tried = (None, *disturbances)
    work = [(field_id, blueprint, v, program, site, d, corrections, retries, False, regrasps, None, checks)
            for d in tried for v in variations]
    runs = []
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(jobs) as pool:
            for r in pool.map(_one, work):
                runs.append(r)
                if progress:
                    progress(len(runs), len(work), r)
    else:
        for w in work:
            runs.append(_one(w))
            if progress:
                progress(len(runs), len(work), runs[-1])
    n = len(variations)
    groups = tuple(('none' if d is None else d.label, '' if d is None else d.describe(), tuple(runs[i * n:(i + 1) * n]))
                   for i, d in enumerate(tried))
    return Disturbed(field_id, name, protocol, duration, site, ranges, corrections, groups, retries, blind, regrasps,
                     checks)


def _last(run):
    """When the run met its last goal, or None if it missed one."""
    if run.error or not all(_succeeded(x) for x in run.results):
        return None
    times = [x.time for x in run.results if x.time is not None]
    return max(times) if times else None


@dataclass(frozen=True)
class Group:
    """What one disturbance did over the set-ups."""
    label: str
    met: int                # set-ups that met every goal
    runs: int
    drawn_met: int          # of the set-ups drawn at random
    drawn: int
    change: float | None    # median change in when the last goal was met, s; None undisturbed or unknown
    pushes: tuple           # how far each push moved the base, m, sorted
    went_back: int          # set-ups whose program went back to its stop
    missed: tuple           # the set-ups that missed a goal
    seen: tuple = ()        # how far from its plan each set-up's last look saw its object, m, sorted
    again: int = 0          # set-ups whose program looked again after a missed grasp (ADR 0033)
    # Each drawn set-up is a pair: its undisturbed run and this one, one run until the event
    # (ADR 0036). Of the drawn set-ups that met every goal undisturbed (`held`), how many the
    # event broke; of those that missed undisturbed, how many met every goal with it.
    held: int = 0
    broke: int = 0
    rescued: int = 0
    why: str = ''           # what the program said when it stopped, in most of the set-ups that missed

    @property
    def low(self):
        return lower_bound(self.drawn_met, self.drawn) if self.drawn else 0.

    @property
    def p(self):
        """The exact McNemar test on the drawn pairs whose outcomes differ."""
        return mcnemar(self.broke, self.rescued)

    @property
    def breaks_at_most(self):
        """The share of undisturbed successes the event breaks is at most this (95 %)."""
        return upper_bound(self.broke, self.held) if self.held else 1.

    def breaks(self):
        """The share of undisturbed successes the event breaks, as sure as the pairs make it:
        at most, when it broke none; at least, when it broke all; else the 95 % interval."""
        if not self.held:
            return '-'
        if self.broke == 0:
            return f'0 of {self.held}, at most {100 * self.breaks_at_most:.0f} %'
        if self.broke == self.held:
            return f'{self.broke} of {self.held}, at least {100 * lower_bound(self.broke, self.held):.0f} %'
        lo, hi = interval(self.broke, self.held)
        return f'{self.broke} of {self.held}, {100 * lo:.0f} to {100 * hi:.0f} %'


def summaries(result):
    """One Group per disturbance, undisturbed first, each set-up compared with itself."""
    undisturbed = result.groups[0][2]
    out = []
    for i, (label, _, runs) in enumerate(result.groups):
        sample = [r for r in runs if not r.error and r.variation.label.startswith('repeat')]
        changes = [_last(r) - _last(u) for r, u in zip(runs, undisturbed)
                   if _last(r) is not None and _last(u) is not None]
        pairs = [(_last(u) is not None, _last(r) is not None) for r, u in zip(runs, undisturbed)
                 if r.variation.label.startswith('repeat') and not r.error and not u.error]
        out.append(Group(label, sum(1 for r in runs if _last(r) is not None), len(runs),
                         sum(1 for r in sample if _last(r) is not None), len(sample),
                         median(changes) if i and changes else None,
                         tuple(sorted(r.pushed for r in runs if r.pushed is not None)),
                         sum(1 for r in runs if r.went_back),
                         tuple(r.variation.label for r in runs if _last(r) is None),
                         tuple(sorted(off(r.seen[-1]) for r in runs if r.seen)),
                         sum(1 for r in runs if r.regrasped),
                         sum(1 for was, _ in pairs if was), sum(1 for was, now in pairs if was and not now),
                         sum(1 for was, now in pairs if now and not was),
                         _why(r for r in runs if _last(r) is None)))
    return out


def _handled_by_disturbance(result):
    """The disturbance report's lines on how the handled part was treated under each (ADR 0040)."""
    from little_world.inventory.handling import WINDOW
    parts = sorted({h.part for _, _, runs in result.groups for r in runs for h in r.handled})
    if not parts:
        return []
    part = parts[0]
    lines = ['', f'How {part.split("/")[-1]} was handled (ADR 0040), the median over the set-ups and, in brackets, '
             f'the most: the force on it from the machine and from anything else, averaged over {1000 * WINDOW:.0f} ms; '
             'how far it leaned; how far it fell when the machine let go.', '',
             '| Disturbance | From the machine | From anything else | Leaned | Fell when let go |',
             '| --- | --- | --- | --- | --- |']
    for label, _, runs in result.groups:
        hs = [h for r in runs for h in r.handled if h.part == part]
        if not hs:
            continue
        machine = [h.of('steady', 'machine') for h in hs]
        other = [max((v for k, v in h.steady if k != 'machine'), default=0.) for h in hs]
        tilt = [h.tilt for h in hs]
        fell = [h.dropped for h in hs if h.dropped is not None]
        lines.append(f'| {label} | {median(machine):.2f} N ({max(machine):.2f}) | {median(other):.2f} N ({max(other):.2f}) | '
                     f'{median(tilt):.0f} deg ({max(tilt):.0f}) | ' + (f'{100 * median(fell):.1f} cm |' if fell else '- |'))
    return lines


def _handling(runs):
    """A report's lines on how each handled part was treated over these runs (ADR 0040)."""
    from little_world.inventory.handling import WINDOW, summary, table
    parts = sorted({h.part for r in runs for h in r.handled})
    lines = []
    for part in parts:
        rows = summary([next((h for h in r.handled if h.part == part), None) for r in runs])
        if rows:
            lines += ['', f'How {part.split("/")[-1]} was handled, over {len(runs)} runs (ADR 0040): the force on it '
                      f'from each thing that touched it, largest in any one step and averaged over {1000 * WINDOW:.0f} '
                      'ms; how far it leaned; how far it fell when the machine let go.', '', *table(rows)]
    return lines


def _p(p):
    """An exact p as a report prints it: four places, or below the smallest of them."""
    return '< 0.0001' if p < 1e-4 else f'= {p:.4f}'


def _why(missed):
    """What the program said last in most of these runs, if it said why it stopped."""
    from collections import Counter
    said = Counter(r.message for r in missed if r.message and r.message not in ('Completed', 'Running'))
    return said.most_common(1)[0][0] if said else ''


def off(look):
    """How far, in plan, a look saw its object from where it was planned (m)."""
    _, planned, seen, *_ = look
    return ((seen[0] - planned[0]) ** 2 + (seen[1] - planned[1]) ** 2) ** .5


def missed_by(look):
    """How far a look's sighting was from where its object really was (m), or None."""
    if len(look) < 4:
        return None
    return sum((a - b) ** 2 for a, b in zip(look[2], look[3])) ** .5


def disturbed_from_json(text):
    """A disturbance sweep written with `to_json`, read back."""
    import json
    d = json.loads(text)
    groups = tuple((label, description, tuple(_run(r) for r in runs)) for label, description, runs in d['groups'])
    site = tuple(d['site']) if d['site'] is not None else None
    return Disturbed(d['field'], d['design'], d['protocol'], d['duration'], site, Ranges(**d['ranges']),
                     d['corrections'], groups, d.get('retries'), d.get('blind', False), d.get('regrasps'),
                     d.get('checks'))


def disturbed_markdown(result):
    """A disturbance sweep as a short report: one row per disturbance."""
    field = FIELDS[result.field]
    undisturbed = result.groups[0][2]
    n = len(undisturbed)
    drawn_count = sum(1 for r in undisturbed if r.variation.label.startswith('repeat'))
    what = {'hold': f'held still for {result.duration:g} s',
            'drive': f'driven straight ahead at full speed for {result.duration:g} s',
            'program': "running the field's program, solved once for the design on its mark"}[result.protocol]
    capped = ('' if result.corrections is None else
              f' Aimed poses were corrected at most {result.corrections} times (ADR 0025; the runner allows 2).') + \
        ('' if result.retries is None else
         f' A program went back to a stop it was pushed off at most {result.retries} times (ADR 0031; the runner allows 1).') + \
        (' The program ran without its looks (`--blind`, ADR 0032).' if result.blind else '') + \
        ('' if result.regrasps is None else
         f' A program looked again after a missed grasp at most {result.regrasps} times (ADR 0033; the runner allows 1).') + \
        (' The program took every picture as new and lit (`--unchecked-camera`, ADR 0038).' if result.checks is False else '')
    groups = summaries(result)
    looked = any(g.seen for g in groups)
    worst = max((missed_by(r.seen[-1]) or 0. for _, _, runs in result.groups for r in runs if r.seen), default=0.)
    lines = [f'# {field.title}, disturbed: {result.design}', '',
             f'Each disturbance tried on the same {n} set-ups - the design as designed and {drawn_count} drawn at '
             f'random within the ranges of ADR 0024 - {what}.{capped}', '',
             '| Disturbance | Every goal met | Drawn at random | Broken by it | Last goal, median change | Pushed |'
             ' Went back |' + (' Looked again | Camera saw it moved |' if looked else '') + ' Missed in |',
             '| --- | --- | --- | --- | --- | --- | --- |' + (' --- | --- |' if looked else '') + ' --- |']
    for i, g in enumerate(groups):
        sure = f'{g.drawn_met} of {g.drawn}, at least {100 * g.low:.0f} %' if g.drawn else '-'
        broken = '-' if not i or not g.held else \
            g.breaks() + (f'; rescued {g.rescued}' if g.rescued else '') + (f'; p {_p(g.p)}' if g.broke or g.rescued else '')
        change = '-' if g.change is None else f'{g.change:+.1f} s'
        pushed = '-' if not g.pushes else \
            f'{100 * median(g.pushes):.1f} cm ({100 * g.pushes[0]:.1f} to {100 * g.pushes[-1]:.1f})'
        lost = '-' if not g.missed else 'every set-up' if len(g.missed) == g.runs else ', '.join(g.missed)
        if g.why:
            lost += f': "{g.why}"'
        seen = ('' if not looked else f' {g.again or "-"} |' + (' - |' if not g.seen else
                f' {100 * median(g.seen):.1f} cm ({100 * g.seen[0]:.1f} to {100 * g.seen[-1]:.1f}) |'))
        lines.append(f'| {g.label} | {g.met} of {g.runs} | {sure} | {broken} | {change} | {pushed} | {g.went_back or "-"} |{seen} {lost} |')
    lines += _handled_by_disturbance(result)
    lines += ['', 'What each disturbance does:', '']
    lines += [f'- **{label}**: {description}.' for label, description, _ in result.groups[1:]]
    first = [x.label.lower() for x in undisturbed[0].results] if undisturbed and undisturbed[0].results else []
    lines += ['', 'A run counts when it meets every goal' + (f' ({", ".join(first)})' if first else '') +
              '. "Last goal, median change" compares each set-up with itself undisturbed. "Pushed" is how '
              'far the machine\'s base went the way it was pushed, a second after the push; "Went back", in how '
              'many set-ups the program drove back to a stop it had been pushed off (ADR 0031). '
              + '"Broken by it" pairs each drawn set-up with itself undisturbed - the two are one run until '
              'the event, step for step (ADR 0036) - and counts those that met every goal undisturbed and '
              'missed one with it, with the share of successes it breaks (95 % confidence); "rescued" counts the '
              'set-ups it turned the other way, and p is the exact McNemar test on the set-ups whose outcomes '
              'differ. '
              + ('"Looked again", in how many the program, its grasp missed, opened its jaws, looked and reached '
                 'again (ADR 0033). "Camera saw it moved" is how far from where it was planned the table camera '
                 f'last saw the cube (ADR 0032); every sighting was within {1000 * worst:.1f} mm of where the cube '
                 'really was. ' if looked else '') +
              'The rate is over the set-ups drawn at random (ADR 0028); the design as designed is a chosen run.', '']
    return '\n'.join(lines)


def to_json(result):
    """A sweep as JSON, for the app to read back from a sweep run in another process."""
    import json
    from dataclasses import asdict
    return json.dumps(asdict(result))


def _run(r):
    from little_world.fields.goals import Result
    return Run(Variation(**{**r['variation'], 'at': tuple(r['variation']['at'])}),
               tuple(Result(**x) for x in r['results']), r['tipped'], r['predicted'], r['program'], r['error'],
               r['seconds'], r.get('disturbed', ''), r.get('pushed'), r.get('went_back', 0),
               tuple((look[0], *(tuple(v) for v in look[1:])) for look in r.get('seen', ())),
               r.get('regrasped', 0), r.get('message', ''), r.get('event'),
               tuple(_handled(h) for h in r.get('handled', ())))


def _handled(h):
    from little_world.inventory.handling import Handled
    return Handled(h['part'], tuple(tuple(x) for x in h['peak']), tuple(tuple(x) for x in h['steady']), h['tilt'],
                   h['dropped'])


def from_json(text):
    import json
    d = json.loads(text)
    runs = tuple(_run(r) for r in d['runs'])
    site = tuple(d['site']) if d['site'] is not None else None
    camera = d.get('camera')
    return Sweep(d['field'], d['design'], d['protocol'], d['duration'], site, Ranges(**d['ranges']), runs,
                 CameraError(**camera) if camera else None)


# -- reading a sweep ---------------------------------------------------------------------------

def spread(sweep):
    """Per goal: (label, met, ran, times of the runs that met it, labels of the runs that did not)."""
    ran = [r for r in sweep.runs if not r.error]
    if not ran:
        return []
    out = []
    for first in ran[0].results:
        got = [(r, r.result(first.id)) for r in ran]
        good = [x for r, x in got if x and x.status in ('met', 'kept')]
        times = sorted(x.time for x in good if x.time is not None)
        bad = [r.variation.label for r, x in got if not x or x.status not in ('met', 'kept')]
        out.append((first.label, len(good), len(ran), times, bad))
    return out


def drawn(sweep):
    """The runs whose conditions were drawn at random within the ranges: the sample. The
    others were chosen - the design as designed, each variation alone at either end of its
    range - and check corners; they do not measure how often anything happens (ADR 0028)."""
    return [r for r in sweep.runs if not r.error and r.variation.label.startswith('repeat')]


def _succeeded(x):
    return x is not None and x.status in ('met', 'kept')


@dataclass(frozen=True)
class Rate:
    """How many drawn runs met a goal (or every goal), and the share of runs drawn the same
    way that would, at least, with CONFIDENCE (one-sided, Clopper-Pearson)."""
    label: str
    met: int
    runs: int

    @property
    def low(self):
        return lower_bound(self.met, self.runs) if self.runs else 0.


def rates(sweep):
    """[every goal, then each goal] over the drawn runs; [] when none was drawn."""
    sample = drawn(sweep)
    if not sample:
        return []
    out = [Rate('every goal', sum(1 for r in sample if all(_succeeded(x) for x in r.results)), len(sample))]
    for first in sample[0].results:
        out.append(Rate(first.label, sum(1 for r in sample if _succeeded(r.result(first.id))), len(sample)))
    return out


def assurance(sweep):
    """Two short lines for the panel: what the drawn runs show and how sure it makes us."""
    sample = drawn(sweep)
    if not sample:
        return ()
    n = len(sample)
    tipped = [r.tipped for r in sample if r.tipped is not None]
    if tipped and len(tipped) == n:
        return (f'{n} random set-ups tipped at {min(tipped):.1f}-{max(tipped):.1f} deg;',
                f'a new one lands in that span {n - 1} times in {n + 1}')
    whole = rates(sweep)[0]
    return (f'{whole.met} of {n} random set-ups met every goal,',
            f'so at least {100 * whole.low:.0f}% would ({100 * CONFIDENCE:.0f}% confidence)')


def _time(t):
    return '-' if t is None else f'{t:.1f} s'


def markdown(sweep):
    """The sweep as a short report: results first, then each variation."""
    field = FIELDS[sweep.field]
    ran = [r for r in sweep.runs if not r.error]
    skipped = [r for r in sweep.runs if r.error]
    what = {'hold': f'held still for {sweep.duration:g} s',
            'drive': f'driven straight ahead at full speed for {sweep.duration:g} s',
            'program': "running the field's program, solved once for the design on its mark"}[sweep.protocol]
    lines = [f'# {field.title}, varied: {sweep.design}', '',
             f'{len(ran)} runs, {what}' + (f'; {len(skipped)} could not run' if skipped else '') + '.']
    if sweep.site is not None:
        lines.append(f'Payload site: ({sweep.site[0]:.3f}, {sweep.site[1]:.3f}) m in plan, a steel block of the payload\'s mass.')
    if sweep.camera is not None:
        lines.append(f'The field\'s camera stood off where the program believed it: {sweep.camera.describe()} (ADR 0039).')
    by_goal = {rate.label: rate for rate in rates(sweep)[1:]}
    lines += ['', '| Goal | Met | Drawn at random | Times (fastest / median / slowest) | Not met in |',
              '| --- | --- | --- | --- | --- |']
    for label, good, total, times, bad in spread(sweep):
        span = ' / '.join(_time(t) for t in (times[0], median(times), times[-1])) if times else '-'
        missed = 'every run' if bad and not good else ', '.join(bad) if bad else '-'
        rate = by_goal.get(label)
        sure = f'{rate.met} of {rate.runs}, at least {100 * rate.low:.0f} %' if rate else '-'
        lines.append(f'| {label} | {good} of {total} | {sure} | {span} | {missed} |')
    tipped = [r for r in ran if r.tipped is not None]
    if tipped:
        lo, hi = min(tipped, key=lambda r: r.tipped), max(tipped, key=lambda r: r.tipped)
        lines += ['', f'Tipped over between {lo.tipped:.1f} deg ({lo.variation.label}) and '
                  f'{hi.tipped:.1f} deg ({hi.variation.label}).']
        errors = [r.tipped - r.predicted for r in tipped if r.predicted is not None]
        if errors:
            worst = max((r for r in tipped if r.predicted is not None), key=lambda r: abs(r.tipped - r.predicted))
            lines.append(f'Against the design\'s prediction for each variation: {min(errors):+.1f} to '
                         f'{max(errors):+.1f} deg, the furthest {worst.variation.label}.')
    looks = sorted(off(r.seen[-1]) for r in ran if r.seen)
    if looks:
        worst = max((missed_by(r.seen[-1]) or 0. for r in ran if r.seen), default=0.)
        lines += ['', f'The program looked for its object with the field\'s camera (ADR 0032) in {len(looks)} runs and '
                  f'saw it {1000 * median(looks):.1f} mm from where it was planned (median; {1000 * looks[0]:.1f} to '
                  f'{1000 * looks[-1]:.1f} mm), each time within {1000 * worst:.1f} mm of where it really was.']
    lines += ['', _how_sure(sweep)]
    lines += _handling(ran)
    nominal = next((r for r in ran if r.variation.nominal), None)
    lines += ['', '## Each run', '', '| Variation | ' + ('Tipped at | Predicted | ' if tipped else '') + 'Goals | Changed from as designed |',
              '| --- | ' + ('--- | --- | ' if tipped else '') + '--- | --- |']
    for r in sweep.runs:
        v = r.variation
        name = f'{v.label}: {v.describe()}' if v.label.startswith('repeat') else v.label
        if r.error:
            lines.append(f'| {name} | ' + ('- | - | ' if tipped else '') + f'not run: {r.error} | |')
            continue
        good = sum(1 for x in r.results if x.status in ('met', 'kept'))
        cells = [name]
        if tipped:
            cells += ['-' if r.tipped is None else f'{r.tipped:.1f}', '-' if r.predicted is None else f'{r.predicted:.1f}']
        cells += [f'{good} of {len(r.results)}', _changes(r, nominal)]
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines += ['', 'Variations: ' + _ranges(sweep), '']
    return '\n'.join(lines)


def _how_sure(sweep):
    """The paragraph that says what the counts can and cannot show."""
    sample = drawn(sweep)
    chosen = len([r for r in sweep.runs if not r.error]) - len(sample)
    level = f'{100 * CONFIDENCE:.0f} %'
    corners = (f'The other {chosen} runs were chosen, not drawn - the design as designed and each variation '
               'alone at either end of its range: they check the corners and measure no rate.') if chosen else ''
    if not sample:
        return f'How sure: no run was drawn at random, so no rate can be given. {corners}'.strip()
    n = len(sample)
    tipped = [r.tipped for r in sample if r.tipped is not None]
    if tipped and len(tipped) == n:
        return (f'How sure: the {n} runs drawn at random within the ranges tipped over between '
                f'{min(tipped):.1f} and {max(tipped):.1f} deg. Another run drawn the same way lands between '
                f'the lowest and highest of {n} with probability {n - 1}/{n + 1}, whatever the spread\'s shape '
                f'(order statistics). {corners}').strip()
    whole = rates(sweep)[0]
    claim = runs_needed(.05)
    return (f'How sure: the {n} runs drawn at random within the ranges are the sample. Every goal was met in '
            f'{whole.met} of them, so at least {100 * whole.low:.0f} % of runs set up at random within these ranges '
            f'would meet every goal ({level} confidence, one-sided, Clopper-Pearson). {corners} '
            f'To show failures below 5 % at {level} takes {claim} drawn runs without one (`--samples {claim}`).')


def headline(sweep):
    """The sweep in one line, and whether that is good news: ('Tipped over at 51 to 58 deg
    in 20 runs', None) or ('All goals met in 19 of 20 runs', 'warn')."""
    ran = [r for r in sweep.runs if not r.error]
    if not ran:
        return 'No run could be made', 'warn'
    tipped = [r.tipped for r in ran if r.tipped is not None]
    if tipped:
        lo, hi = min(tipped), max(tipped)
        span = f'{lo:.0f} deg' if round(lo) == round(hi) else f'{lo:.0f} to {hi:.0f} deg'
        runs = f'all {len(ran)} runs' if len(tipped) == len(ran) else f'{len(tipped)} of {len(ran)} runs'
        return f'Tipped over at {span} in {runs}', None
    whole = sum(1 for r in ran if all(x.status in ('met', 'kept') for x in r.results))
    if whole == len(ran):
        return f'Every goal met in all {len(ran)} runs', 'ok'
    return f'Every goal met in {whole} of {len(ran)} runs', 'warn'


@dataclass(frozen=True)
class Strip:
    """One quantity over a sweep's runs, for drawing as ticks on a line: a static test's
    angle at tipping, or else the goal whose time spread most."""
    label: str
    values: tuple           # one per run that has it
    nominal: float | None   # the run as designed
    predicted: float | None = None
    unit: str = 'deg'


def strip(sweep):
    """What to draw of a sweep's spread, or None when no run gives a number."""
    ran = [r for r in sweep.runs if not r.error]
    nominal = next((r for r in ran if r.variation.nominal), None)
    tipped = [r.tipped for r in ran if r.tipped is not None]
    if tipped:
        return Strip('tipped over at', tuple(tipped), nominal.tipped if nominal else None,
                     nominal.predicted if nominal else None)
    best = None
    for label, _, _, times, _ in spread(sweep):
        if len(times) >= 2 and (best is None or times[-1] - times[0] > best[1][-1] - best[1][0]):
            best = (label, times)
    if best is None:
        return None
    label, times = best
    at = next((x.time for x in nominal.results if x.label == label), None) if nominal else None
    return Strip(label.lower(), tuple(times), at, None, 's')


def moved_most(sweep, count=3):
    """The one-at-a-time variations that changed the result most, with what they changed:
    a goal lost or won first, then the size of the change in the tipping angle or in time."""
    ran = [r for r in sweep.runs if not r.error]
    nominal = next((r for r in ran if r.variation.nominal), None)
    if nominal is None:
        return []
    scored = []
    for r in ran:
        if r is nominal or r.variation.label.startswith('repeat'):
            continue
        lost = sum(1 for x in r.results if (nominal.result(x.id) or x).status != x.status)
        size = abs(r.tipped - nominal.tipped) if r.tipped is not None and nominal.tipped is not None else \
            sum(abs(x.time - y.time) for x in r.results for y in [nominal.result(x.id)]
                if y is not None and x.status == y.status == 'met' and x.time is not None and y.time is not None)
        words = _changes(r, nominal)
        if words:
            scored.append((lost, size, r.variation.label, words))
    scored.sort(key=lambda s: (-s[0], -s[1]))
    return [(label, words) for _, _, label, words in scored[:count]]


def _changes(run, nominal):
    if nominal is None or run is nominal:
        return ''
    out = []
    for x in run.results:
        y = nominal.result(x.id)
        if y is None:
            continue
        if x.status != y.status:
            out.append(f'{x.label.lower()}: {x.status}')
        elif x.status == 'met' and x.time is not None and y.time is not None and abs(x.time - y.time) >= .5:
            out.append(f'{x.label.lower()} {x.time - y.time:+.1f} s')
    if run.tipped is not None and nominal.tipped is not None and abs(run.tipped - nominal.tipped) >= .1:
        out.append(f'tipped {run.tipped - nominal.tipped:+.1f} deg')
    return '; '.join(out)


def _ranges(sweep):
    r = sweep.ranges
    placed = (f'set down up to {100 * r.place:g} cm and {r.turn:g} deg off its mark' if r.turn else
              f'set down up to {100 * r.place:g} cm off its mark, then squared to the field')
    return (f'{placed}; up to {r.payload:g} kg carried, '
            f'up to {100 * r.shift:g} cm either side of its site; friction across each surface pair\'s published '
            'range (contact_pairs.SPREADS; a factor of two where a source gives none). The placement and '
            'payload ranges are assumptions, stated; the friction ranges are the sources\'.')


def main(argv=None):
    import argparse
    import os
    parser = argparse.ArgumentParser(prog='python -m little_world.inventory.sweep',
                                     description='Run a test field over variations and report the spread.')
    parser.add_argument('field', choices=sorted(PROTOCOLS))
    parser.add_argument('--design', default='mobile_platform',
                        help=f'an example ({", ".join(DESIGNS)}) or a saved Blueprint JSON file')
    parser.add_argument('--samples', type=int, default=8, help='random repeats after the one-at-a-time runs')
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--jobs', type=int, default=max(1, min(4, (os.cpu_count() or 2) - 1)))
    parser.add_argument('--out', help='write the report here as well as printing it')
    parser.add_argument('--json', help='write the sweep here as JSON')
    parser.add_argument('--name', help='what to call the design in the report (default: --design)')
    parser.add_argument('--disturb', action='store_true',
                        help="instead: the design and the drawn set-ups, undisturbed and under the field's disturbances")
    parser.add_argument('--only', action='append', default=None, metavar='LABEL',
                        help="with --disturb: only this one of the field's disturbances, by its label (repeatable)")
    parser.add_argument('--corrections', type=int, default=None,
                        help='cap an aimed pose\'s corrections (0: run poses as taught; default: the runner\'s own)')
    parser.add_argument('--retries', type=int, default=None,
                        help='cap how often a program goes back to a stop it was pushed off (0: never; default: the runner\'s own)')
    parser.add_argument('--camera-error', metavar='X,Y,Z[,PAN,TILT,ROLL]',
                        help="the field's camera off where the program believes it: millimetres along the "
                             'field\'s axes, then degrees about its own (ADR 0039)')
    parser.add_argument('--unchecked-camera', action='store_true',
                        help='take every picture as new and lit, as before ADR 0038 (to measure what the checks change)')
    parser.add_argument('--regrasps', type=int, default=None,
                        help='cap how often a program that looked looks again after a missed grasp (0: never; default: the runner\'s own)')
    parser.add_argument('--blind', action='store_true',
                        help="run the field's program without looking with the field's camera (ADR 0032)")
    args = parser.parse_args(argv)
    if args.unchecked_camera and not args.disturb:
        parser.error('--unchecked-camera is for --disturb: only a disturbance makes the camera fail')
    camera_error = None
    if args.camera_error:
        if args.disturb:
            parser.error('--camera-error is for a varied sweep, not --disturb')
        try:
            values = [float(v) for v in args.camera_error.split(',')]
            if len(values) not in (3, 6):
                raise ValueError
            camera_error = CameraError(tuple(v / 1000 for v in values[:3]), tuple(values[3:]) or (0., 0., 0.))
        except ValueError:
            parser.error(f'--camera-error takes three millimetres and optionally three degrees, not {args.camera_error!r}')
    bp = design(args.design)
    ranges = ranges_for(args.field)
    variations = plan(ranges, samples=args.samples, seed=args.seed)

    def progress(done, total, r):
        print(f'  {done}/{total} {r.variation.label}: ' + (f'not run ({r.error})' if r.error else f'{r.seconds:.0f} s'), flush=True)
    if args.disturb:
        chosen = None
        if args.only:
            known = {d.label: d for d in DEFAULTS.get(args.field, ())}
            unknown = [label for label in args.only if label not in known]
            if unknown:
                parser.error(f'no disturbance called {unknown[0]!r} for {args.field}; there are: '
                             + '; '.join(known))
            chosen = tuple(known[label] for label in args.only)
        result = disturb(args.field, bp, chosen, args.name or args.design, args.samples, args.seed, args.jobs,
                         progress, args.corrections, args.retries, args.blind, args.regrasps,
                         False if args.unchecked_camera else None)
        text = disturbed_markdown(result)
    else:
        result = sweep(args.field, bp, variations, args.name or args.design, jobs=args.jobs, progress=progress,
                       ranges=ranges, corrections=args.corrections, retries=args.retries, blind=args.blind,
                       regrasps=args.regrasps, camera_error=camera_error)
        text = markdown(result)
    print(text)
    from pathlib import Path
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    if args.json:
        Path(args.json).write_text(to_json(result), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
