"""A grasp bench: one gripper, five diagnostic objects, a grid of poses, one fixed protocol (FR-043).

Grasping was judged only inside whole tasks - the Fetch, the factory cell - so a weakness showed
where a task happened to meet it: a block lying across the jaws was lost on the way to the bin (OPEN
LW-034) and nothing asked which objects and poses a gripper holds. The bench asks it directly, as a
benchmark of MuJoCo grasps did across robots and objects (arXiv 2611.07651): each object set on a
bench at each pose of a grid, the arm sent through the same approach, close, lift, carry and hold, and
the outcome judged by the object - not by the program's own account of it.

- Objects: a 25 mm cube; the kit's 25 x 25 x 40 mm block standing and lying on its side; a cylinder
  25 mm across, standing; a 60 x 40 x 6 mm plate lying flat.
- Poses: 3 x 3 places 2 cm apart round the bench's middle, each at 4 turns about the vertical.
- Protocol: the arm lab's pick-and-place template (`tool_motion.pick_and_place`): jaws open; 6 cm
  above the object's top, down to its centre - or as low as the jaws keep 5 mm over the bench;
  close for 1 s and squeeze 0.6 deg more, then the grasp check (`tool_motion.take_hold`, ADR 0078);
  lift 10 cm; carry 20 cm to the side; hold 2 s. Known pose: the program is solved for where the
  object is. Or found by the camera (`--camera`): a depth camera beyond the bench, as the Fetch's at
  its table; the program is solved for the bench's middle, looks for the object there and reaches
  where it was seen, up to 2.8 cm away (ADR 0032, 0025) - so that what the camera misses is told
  apart from what the jaws drop. The
  program goes on as taught whatever its grasp check feels (the runner's 'ignore', FR-022), so the
  outcome is the grip's; what the check felt is reported beside it.
- Held: lifted 8 cm or more and carried 18 cm or more at the end, and slipped under 2 mm in the
  jaws over the run's last 2 s. A pose the arm cannot reach, or a run that cannot be set up, is
  not held: what is missing counts as a failure.
- The jaws' angle: where the object's x axis (the lying block's and the plate's length) lies from
  the line the jaws close along, 0 to 90 deg, as OPEN LW-034 measured it. An arm without a wrist
  that turns closes its jaws across the line from its base, so a turn of the object is a turn
  against the jaws.

The statistics are the standard library's; the runs come from `inventory.sweep` through MuJoCo.
"""
from dataclasses import dataclass
from math import cos, radians, sin
import re
from statistics import median

from little_world.inventory.confidence import interval

# name: (shape, full size): box (x, y, z) or cylinder (radius, length) - each at rest on the bench
OBJECTS = {
    'cube': ('box', (.025, .025, .025)),
    'block': ('box', (.025, .025, .040)),            # the kit cube of the arm lab and the Fetch, standing
    'block lying': ('box', (.040, .025, .025)),      # the same block on its side, its length along its turn
    'cylinder': ('cylinder', (.0125, .040)),         # standing on its end
    'plate': ('box', (.060, .040, .006)),            # flat on the bench
}
CENTRE = (.36, -.10)        # m: the grid's middle, in the arm lab's reach with the carry
SHIFTS = (-.02, 0., .02)    # m: the grid's places either way of it, in x and in y
TURNS = (0., 30., 60., 90.)  # deg about the vertical
TOP = .187                  # m: the bench's top, the arm lab's pickup stand's height
BENCH = (.16, .16)          # m: the bench's top, wide enough for the grid and the plate
LIFT, CARRY, HOLD = .10, .20, 2.   # m up, m to the side, s held there
VIEW = ((.36, .05, .26), .75, -125., -18.)   # the window's camera: the bench and the carry beside it
CAMERA_AT = (CENTRE[0] + .45, CENTRE[1], TOP + .78)   # m: a depth camera beyond the bench, looking down at
                                                      # it as the Fetch's looks at its table (ADR 0032)
SEARCH = .06                # m round the plan the camera looks: the grid's places and a little more
SLIP = .002                 # m: the most an object may move in the jaws over the last HOLD seconds
AIR = .02                   # m over where it stood: an object this high is in the air, held by the jaws alone


# What the bench measured for an example as designed (ADR 0077, 0078): held of the 9 places at each
# turn, the report that says so, and what to read in it - the Inventory's Grasp bench tab shows it.
RECORDED = {
    'arm_lab': ({'cube': (9, 9, 9, 9), 'block': (9, 9, 9, 9), 'block lying': (8, 8, 9, 0),
                 'cylinder': (0, 0, 0, 0), 'plate': (0, 0, 0, 0)},
                'docs/sweeps/2026-11-22-grasp-bench-squeeze-first.md',
                "The arm lab's jaws, which no wrist turns, close 74, 44, 14 and 16 deg from the object's length at "
                "the four turns: the lying block falls when they take it by its ends. The cylinder slips out by one "
                "contact a pad (OPEN LW-057); the plate is out of the pads' reach. The grasp check felt all 97 held."),
}
LINE = re.compile(r'\s*\d+/\d+ (.+) \((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\): (.+)$')


def poses():
    """The grid: (dx, dy, turn), 36 of them, places first."""
    return tuple((dx, dy, turn) for dx in SHIFTS for dy in SHIFTS for turn in TURNS)


def height(name):
    """How tall an object stands at rest."""
    shape, size = OBJECTS[name]
    return size[2] if shape == 'box' else size[1]


@dataclass(frozen=True)
class Outcome:
    """One object at one pose: how far it rose and travelled, how much it slipped, and why it stopped."""
    name: str
    pose: tuple                 # (dx, dy, turn)
    lifted: float = 0.          # m its centre rose above where it stood, at the end
    carried: float = 0.         # m in plan from where the program planned to pick it up, at the end
    slip: float | None = None   # m it moved in the jaws over the last HOLD seconds
    message: str = ''           # the program's last word, or why the run could not be set up
    felt: bool | None = None    # what the program's grasp check felt from the jaws' servos (ADR 0048)
    between: bool | None = None  # whether the contacts then said the object was held by the pads
    skew: float | None = None   # deg: a box's x axis from the line the jaws close along, 0 to 90
    grip: float | None = None   # the most of its grip's friction in use while it was in the air (FR-036), 0 to 1

    @property
    def held(self):
        return (self.lifted >= LIFT - .02 and self.carried >= CARRY - .02 and self.slip is not None
                and self.slip < SLIP)

    @property
    def reason(self):
        """Why it was not held, in a few words; '' when it was."""
        if self.held:
            return ''
        if self.felt is None and self.message and self.message != 'Completed':
            return self.message         # it never came to its grasp: why
        if self.lifted < .02:
            return 'not lifted' + (f': {self.message}' if self.message and self.message != 'Completed' else '')
        if self.slip is not None and self.slip >= SLIP:
            return 'slipped in the jaws'
        if self.lifted < LIFT - .02:
            return 'slid down in the jaws'
        if self.carried < CARRY - .02:
            return 'not carried'
        return 'not held'


def table(outcomes):
    """{object: {turn: (held, tried)}} and {object: (held, tried)}."""
    by_turn, total = {}, {}
    for o in outcomes:
        h, t = by_turn.setdefault(o.name, {}).get(o.pose[2], (0, 0))
        by_turn[o.name][o.pose[2]] = (h + o.held, t + 1)
        h, t = total.get(o.name, (0, 0))
        total[o.name] = (h + o.held, t + 1)
    return by_turn, total


def markdown(outcomes, design, title='', look=False):
    """The bench's report: held of tried by object and turn, each object's rate with its exact 95 %
    interval, and why the rest were not held; `look`, the runs found the object with the bench's camera."""
    by_turn, total = table(outcomes)
    names = [n for n in OBJECTS if n in total]
    found = 'found by the bench\'s depth camera' if look else 'known pose'
    lines = [f'# {title or "Grasp bench"}: {design}' + (', found by the camera' if look else ''), '',
             f'Each object at {len(SHIFTS) ** 2} places x {len(TURNS)} turns on a bench {100 * TOP:.1f} cm up; '
             f'approach, close, lift {100 * LIFT:g} cm, carry {100 * CARRY:g} cm, hold {HOLD:g} s; {found}. '
             f'Held: lifted and carried, and under {1000 * SLIP:g} mm of slip in the jaws over the last {HOLD:g} s.', '']
    angles = jaw_angles(outcomes)
    if angles:
        lines += ['At the ' + ', '.join(f'{t:g}' for t in angles) + ' deg turns the object\'s x axis lay '
                  + ', '.join(f'{a:.0f}' for a in angles.values())
                  + ' deg from the line the jaws close along (0: along it; the median over the places).', '']
    lines += [
             '| Object | ' + ' | '.join(f'{t:g} deg' for t in TURNS) + ' | Held | 95 % interval |',
             '| --- | ' + ' | '.join('---' for _ in TURNS) + ' | --- | --- |']
    for n in names:
        h, t = total[n]
        lo, hi = interval(h, t)
        cells = ' | '.join('{} of {}'.format(*by_turn[n].get(turn, (0, 0))) for turn in TURNS)
        lines.append(f'| {n} | {cells} | {h} of {t} | {100 * lo:.0f} to {100 * hi:.0f} % |')
    lines += ['', '## Why the rest were not held', '']
    for n in names:
        reasons = {}
        for o in outcomes:
            if o.name == n and not o.held:
                reasons[o.reason] = reasons.get(o.reason, 0) + 1
        if reasons:
            lines.append(f'- {n}: ' + '; '.join(f'{r} ({k})' for r, k in sorted(reasons.items(), key=lambda x: -x[1])))
    slips = [o.slip for o in outcomes if o.held]
    if slips:
        lines += ['', f'Held runs slipped {1000 * min(slips):.2f} to {1000 * max(slips):.2f} mm in their last {HOLD:g} s.']
    near = grips(outcomes)
    if near:
        lines += ['', '## How close to slipping', '',
                  'The most of its grip\'s friction in use while the object was in the air, held by the jaws alone '
                  '(FR-036): 100 % is a grip at the edge of its friction cones, sliding.', '',
                  '| Object | held runs: median | most | not held, in the air |', '| --- | --- | --- | --- |']
        for n in names:
            if n in near:
                held, lost = near[n]
                lines.append(f'| {n} | ' + (f'{100 * median(held):.0f} % | {100 * max(held):.0f} %' if held else '- | -')
                             + ' | ' + (', '.join(f'{100 * u:.0f} %' for u in sorted(lost)) if lost else '-') + ' |')
    (felt_held, held), (felt_lost, lost) = check(outcomes)
    if held or lost:
        from little_world.assets import robot_library
        from little_world.assets.robot_models import MODELS
        reads = ('its jaws\' contacts with the object: a library robot\'s gripper servo is not read as the kit\'s are'
                 if design in MODELS or robot_library.is_user(design) else 'the jaws\' servos (ADR 0048), not the object')
        lines += ['', '## What the grasp check felt', '',
                  f'The program went on as taught whatever its grasp check felt; the check reads {reads}.', '',
                  '| Object | held, felt held | held, felt nothing | not held, felt held | not held, felt nothing |',
                  '| --- | --- | --- | --- | --- |']
        for n in names:
            mine = [o for o in outcomes if o.name == n and o.felt is not None]
            cell = lambda h, f: sum(1 for o in mine if o.held == h and o.felt == f)
            lines.append(f'| {n} | {cell(True, True)} | {cell(True, False)} | {cell(False, True)} | {cell(False, False)} |')
        lines += ['', f'It felt {felt_held} of the {held} held runs held, and {felt_lost} of the {lost} others.']
    return '\n'.join(lines) + '\n'


def grips(outcomes):
    """{object: (the held runs' most friction in use, the others')} over the runs that lifted it."""
    out = {}
    for o in outcomes:
        if o.grip is not None:
            out.setdefault(o.name, ([], []))[0 if o.held else 1].append(o.grip)
    return out


def jaw_angles(outcomes):
    """{turn: the median jaws' angle (deg) over the runs at that turn}, for the runs that reached."""
    by = {}
    for o in outcomes:
        if o.skew is not None:
            by.setdefault(o.pose[2], []).append(o.skew)
    return {turn: median(by[turn]) for turn in TURNS if turn in by}


def check(outcomes):
    """What the grasp check felt: ((felt held, held runs), (felt held, other runs)), over the runs it
    checked."""
    checked = [o for o in outcomes if o.felt is not None]
    held = [o for o in checked if o.held]
    lost = [o for o in checked if not o.held]
    return (sum(o.felt for o in held), len(held)), (sum(o.felt for o in lost), len(lost))


def skew(closing, turn):
    """Degrees, 0 to 90, between an object's x axis turned `turn` deg about the vertical and the
    plan direction `closing` (x, y) the jaws close along."""
    from math import atan2, degrees
    angle = abs(degrees(atan2(closing[1], closing[0])) - turn) % 180.
    return min(angle, 180. - angle)


# -- the runs ---------------------------------------------------------------------------------------

def bench_field(name, pose, camera=False):
    """The bench with one object on it at `pose` (dx, dy, turn) from the grid's middle: the arm lab's
    pickup stand widened, the object a loose wooden part, its goal to be lifted; with `camera`, a depth
    camera beyond it, a RealSense D435's, for a program that finds the object by looking. The window
    finds it by its id, the last one made (`fields.VARIANTS`)."""
    from little_world.core.component import Body, Camera, Geometry, Transform
    from little_world.fields import VARIANTS, Field, Zone, field_entities, fixed, looking, slab
    if name not in OBJECTS:
        raise ValueError(f'no bench object called {name!r}; objects: {", ".join(OBJECTS)}')
    shape, size = OBJECTS[name]
    dx, dy, turn = pose
    h = height(name)
    part = Body('part', Geometry(shape, size), 'cube',
                Transform((CENTRE[0] + dx, CENTRE[1] + dy, TOP + h / 2 + .0005),
                          (cos(radians(turn) / 2), 0., 0., sin(radians(turn) / 2))), dynamic=True)

    def entities():
        parts = slab()
        parts.append(fixed('bench', (*BENCH, TOP), 'stand', (CENTRE[0], CENTRE[1], TOP / 2)))
        if camera:      # held out on a bracket from a post behind it, out of its picture, as the Fetch's
            cx, cy, cz = CAMERA_AT
            parts.append(fixed('camera_post', (.03, .03, cz + .015), 'stand', (cx + .07, cy, (cz + .015) / 2)))
            parts.append(fixed('camera_bracket', (.07, .02, .01), 'stand', (cx + .045, cy, cz + .02)))
            parts.append(fixed('camera_head', (.09, .025, .025), 'stand', CAMERA_AT,
                               looking(CAMERA_AT, (CENTRE[0], CENTRE[1], TOP))))
            parts.append(Camera('bench_camera', 'camera_head', Transform((0., 0., -.0125)), fovy=58.))
        return field_entities(parts, (part,))
    lifted = Zone('lifted', f'Lifted {100 * LIFT:g} cm', (-2., -2., TOP + h / 2 + LIFT - .01), (2., 2., 3.),
                  target='objects/part')
    made = Field('grasp_bench_camera' if camera else 'grasp_bench', 'Grasp bench',
                 f'The {name} on a bench, to be lifted, carried and held.', entities, goals=(lifted,), home=VIEW,
                 camera=('bench_camera', 'realsense_d435') if camera else ())
    VARIANTS[made.id] = made
    return made


def program(field, blueprint, top=0., clearance=.06, speed=40., look=False):
    """The protocol as a program, solved for this arm and the object where it stands (known pose):
    open, `clearance` above its top (`top` over its centre), down to its centre - or as low as the
    jaws keep JAWS_CLEAR over the bench - close and squeeze, grasp check, lift, carry, hold. Returns
    (the program, the jaws' angle to a box's x axis there, deg, or None for a round object). With
    `look`, the program first looks for the object with the field's camera and its poses are aimed at
    their points, so the arm reaches where the camera saw it (ADR 0032, 0025). ValueError if a point is
    out of reach."""
    from math import atan2, degrees
    import mujoco as mj
    import numpy as np
    from little_world import Entity, World
    from little_world.control.tool_motion import LOOKING, REACHED, WATCH, ToolMotion, take_hold
    from little_world.inventory import sweep
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.programming.program import Block, Program
    backend = MujocoBackend()
    with World(backend, field.scene(Entity('machine', blueprint))) as world:
        state = world.start()
        drive, control, _ = sweep._rigs(backend, blueprint)
        for _ in range(sweep.SETTLE):
            state = sweep._hold(world, drive, control, field, state)
        motion = ToolMotion(backend, blueprint, control)
        spec = next((s for s in control.specs if s.actuators and set(s.actuators) <= set(motion.jaws)), None)
        if spec is None:
            raise ValueError('the bench needs the gripper bound to a keyboard action')
        jaws = spec.id
        # The kit's jaws close for the template's 1 s (ADR 0042); a gripper driven by how closed it is,
        # all the way, at its key's speed, its own controller squeezing what stops it.
        units = getattr(control, 'units', {})
        close = 100. / spec.speed + .25 if all(units.get(a) == '%' for a in spec.actuators) else 1.
        start = motion.targets()
        _, pointing = motion.tool(angles=start)
        m, d = backend.model, backend.data
        part = m.body('objects/part').id
        grasp, length = d.xpos[part].copy(), d.xmat[part].reshape(3, 3)[:, 0]
        _, _, up = motion.frame()
        hold = float(pointing[2])
        poses_, seed, angles_, points = {}, start, {}, {}
        planned = tuple(float(v) for v in grasp)
        fingers = [m.body(motion.prefix + b).id for b in _fingers(blueprint)]

        def reach(label, point):
            nonlocal seed
            short = float('inf')
            for angle in (hold, None):
                angles, short = motion.solve(point, seed, angle)
                if short <= REACHED and not motion.self_collision(angles):
                    poses_[label], seed, angles_[label] = motion.pose(angles), angles, angles
                    points[label] = tuple(float(v) for v in point)
                    return
            raise ValueError(f'the arm cannot reach the {label} point: {100 * short:.1f} cm short')
        grasp = lowest(motion, grasp, float(grasp[2]) - top, top, hold, start)
        reach('above', grasp + (top + clearance) * up)
        reach('at', grasp)
        reach('lifted', grasp + LIFT * up)
        reach('carried', grasp + LIFT * up + np.array((0., CARRY, 0.)))
        closing = np.zeros(3)
        if len(fingers) == 2:
            at = motion._pose(angles_['at'])
            closing = at.xpos[fingers[1]] - at.xpos[fingers[0]]
        round_ = any(m.geom_type[g] != mj.mjtGeom.mjGEOM_BOX for g in range(m.ngeom) if m.geom_bodyid[g] == part)
        jaws_angle = (skew(closing[:2], degrees(atan2(length[1], length[0])))
                      if closing[:2].any() and not round_ else None)

    def pose(label, pace):
        return Block('pose', value=pace, duration=2., angles=poses_[label], point=points[label] if look else ())
    found = (Block('look', 'objects/part', value=WATCH, duration=LOOKING, secondary=SEARCH, point=planned),) if look else ()
    return Program((Block('action', jaws, -1, .6), *found, pose('above', speed), pose('at', speed / 2),
                    *take_hold(jaws, 'objects/part', close),
                    pose('lifted', speed / 2), pose('carried', speed / 2), Block('wait', duration=HOLD))), jaws_angle


def _low(motion, angles):
    """The lowest point of the tool's visible parts with the arm at `angles` (m): a mesh by its own
    vertices, other shapes as `tool_motion._jaws_low` bounds them - by the box round its bounding
    sphere, the Panda's hand reaches 3.6 cm lower over the cube than its mesh does."""
    import mujoco as mj
    import numpy as np
    from little_world.control.tool_motion import _below, _corners
    m = motion.model
    d = motion._pose(angles)
    low = np.inf
    for g in range(m.ngeom):
        if not (_below(m, int(m.geom_bodyid[g]), motion.body) and m.geom_rgba[g][3] > 0):
            continue
        if m.geom_type[g] == mj.mjtGeom.mjGEOM_MESH:
            mesh = m.geom_dataid[g]
            v = m.mesh_vert[m.mesh_vertadr[mesh]:m.mesh_vertadr[mesh] + m.mesh_vertnum[mesh]]
            low = min(low, float(np.min(d.geom_xpos[g][2] + v @ d.geom_xmat[g].reshape(3, 3)[2])))
        else:
            low = min(low, float(np.min(_corners(m, d, g)[:, 2])))
    return low


def _fingers(blueprint):
    """The bodies the jaws close with, as the machine names them: the kit gripper's two fingers, or a
    library robot's - its hand's (`robot_models.CONTROLLERS`) or the jaws its file was found to have."""
    fingers = [b.id for b in blueprint.components if b.id.endswith(('_finger_left', '_finger_right'))]
    robot = next((b for b in blueprint.components if getattr(b, 'robot_asset', None)), None)
    if not fingers and robot is not None:
        from little_world.assets.robot_models import CONTROLLERS, jaws
        hand = CONTROLLERS.get(robot.robot_asset, {}).get('hand')
        fingers = [f'{robot.id}__robot_{n}' for n in (hand[2] if hand else jaws(robot.robot_asset))]
    return fingers


def machine(name):
    """A machine by name: an example design, a saved design's file (`sweep.design`), or a robot from the
    library - a Menagerie arm or one brought in from its file - standing on the floor."""
    from little_world.assets import robot_library
    from little_world.assets.robot_models import MODELS, blueprint
    from little_world.inventory import sweep
    return blueprint(name) if name in MODELS or robot_library.is_user(name) else sweep.design(name)


def lowest(motion, centre, bench, top, hold, seed):
    """Where the tool point grasps an object whose centre is at `centre`, `top` under its top, on
    a surface at height `bench`: its centre, or as little over it as keeps the jaws JAWS_CLEAR over
    the surface - with the tool at the angle `hold` if the arm can, else at any. The point rises no
    further than the object's top. ValueError if no such point is reached without the arm in its
    own machine."""
    from little_world.control.tool_motion import JAWS_CLEAR, REACHED
    for angle in (hold, None):
        point = centre.copy()
        for _ in range(4):
            angles, short = motion.solve(point, seed, angle)
            if short > REACHED:
                break
            under = bench + JAWS_CLEAR - _low(motion, angles)
            if under <= 1e-4:
                if not motion.self_collision(angles):
                    return point
                break
            point = point.copy()
            point[2] += under
            if point[2] > centre[2] + top + 1e-9:
                break
    raise ValueError('the arm cannot close its jaws on it without striking the bench')


def run(design, name, pose, look=False):
    """One object at one pose, through the protocol: its Outcome. Known pose, the program is solved for
    where the object is; with `look`, for the bench's middle at the object's turn, and the camera finds
    where in the grid it is."""
    import numpy as np
    from little_world.inventory import sweep
    blueprint = machine(design)
    if look and OBJECTS[name][0] != 'box':
        return Outcome(name, tuple(pose), message='not looked for: the camera finds boxes (ADR 0032)')
    field = bench_field(name, pose, camera=look)
    try:
        planned = bench_field(name, (0., 0., pose[2]), camera=True) if look else field
        solved, jaws_angle = program(planned, blueprint, top=height(name) / 2, look=look)
    except ValueError as error:
        return Outcome(name, tuple(pose), message=str(error))
    bench_field(name, pose, camera=look)           # the field the window finds by its id is the one run
    fingers = _fingers(blueprint)
    track = []

    uses = []

    def probe(state, backend):
        from little_world.inventory.handling import grip_use
        m, d = backend.model, backend.data
        part = d.xpos[m.body('objects/part').id].copy()
        middle = sum(d.xpos[m.body('machine/' + f).id] for f in fingers) / len(fingers) if fingers else part
        track.append((part, part - middle))
        if part[2] > track[0][0][2] + AIR:      # in the air: what share of its grip's friction holds it
            use = grip_use(backend, 'objects/part')
            if use is not None:
                uses.append(use)
    result = sweep.run('pick_place', blueprint, program=solved, field=field, probe=probe, recovery='ignore')
    if result.error or not track:
        return Outcome(name, tuple(pose), message=result.error or 'did not run')
    steps = max(1, round(HOLD / .002))
    first, last = track[0][0], track[-1][0]
    # Carried from where the program planned to pick it up - with the camera, the bench's middle:
    # it carries the object to a place 20 cm from there, wherever in the grid the camera found it.
    origin = first[:2] - (np.array(pose[:2]) if look else 0.)
    slip = float(np.linalg.norm(track[-1][1] - track[-min(steps, len(track))][1])) if fingers else None
    felt, between = (bool(result.felt[-1][1]), bool(result.felt[-1][2])) if result.felt else (None, None)
    return Outcome(name, tuple(pose), lifted=float(last[2] - first[2]), carried=float(np.linalg.norm(last[:2] - origin)),
                   slip=slip, message=result.message, felt=felt, between=between, skew=jaws_angle,
                   grip=max(uses) if uses else None)


def recorded(blueprint):
    """(the example's name, {object: {turn: (held, tried)}}, its report, what to read in it) when
    `blueprint` is an example the bench measured, as designed; None for any other design."""
    from little_world.inventory.sweep import design
    for name, (held, report, note) in RECORDED.items():
        if blueprint == design(name):
            return (name, {n: {t: (h, len(SHIFTS) ** 2) for t, h in zip(TURNS, row)} for n, row in held.items()},
                    report, note)
    return None


def summary(outcomes):
    """A run's two lines under its table: the jaws' angle at each turn, and what the grasp check felt."""
    angles = jaw_angles(outcomes)
    (felt, held), _ = check(outcomes)
    lines = []
    if angles:
        lines.append('The jaws close ' + ', '.join(f'{a:.0f}' for a in angles.values()) + ' deg from the object\'s length '
                     'at the ' + ', '.join(f'{t:g}' for t in angles) + ' deg turns (the median over the places).')
    if held:
        lines.append(f'The grasp check felt {felt} of the {held} held runs held.')
    return lines


def progress(line):
    """(object, pose, held) from one of the bench's progress lines ('12/180 cube (0.0, 0.0, 30.0): held'),
    None for any other line."""
    found = LINE.match(line)
    if not found or found[1] not in OBJECTS:
        return None
    return found[1], (float(found[2]), float(found[3]), float(found[4])), found[5] == 'held'


def counts(found):
    """{object: {turn: (held, tried)}} from (object, pose, held) triples - the table as runs come in."""
    out = {}
    for name, pose, held in found:
        h, t = out.setdefault(name, {}).get(pose[2], (0, 0))
        out[name][pose[2]] = (h + held, t + 1)
    return out


def from_json(text):
    """The Outcomes the command line wrote beside its report (`--out`)."""
    import json
    return tuple(Outcome(name, tuple(pose), *rest) for name, pose, *rest in json.loads(text))


def _one(job):
    return run(*job)


def bench(design, names=tuple(OBJECTS), jobs=1, progress=None, look=False):
    """Every object at every pose of the grid for `design` - with `look`, each found by the bench's
    camera: the Outcomes, objects in order."""
    work = [(design, name, pose, look) for name in names for pose in poses()]
    found = []
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(jobs) as pool:
            for i, o in enumerate(pool.map(_one, work)):
                found.append(o)
                if progress:
                    progress(i + 1, len(work), o)
    else:
        for i, job in enumerate(work):
            found.append(_one(job))
            if progress:
                progress(i + 1, len(work), found[-1])
    return tuple(found)


def main(argv=None):
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(prog='python -m little_world.inventory.graspbench',
                                     description='Every diagnostic object at every pose of the grid, through one protocol (FR-043).')
    parser.add_argument('--design', default='arm_lab')
    parser.add_argument('--objects', nargs='*', default=list(OBJECTS), choices=list(OBJECTS), metavar='OBJECT')
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--camera', action='store_true', help='find each object with the bench\'s depth camera, '
                        'not from where it is known to be')
    parser.add_argument('--out', help='write the report here, and its outcomes beside it as .json')
    args = parser.parse_args(argv)
    found = bench(args.design, tuple(args.objects), args.jobs,
                  lambda i, n, o: print(f'{i}/{n} {o.name} {o.pose}: {"held" if o.held else o.reason}', flush=True),
                  look=args.camera)
    text = markdown(found, args.design, look=args.camera)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
        Path(args.out).with_suffix('.json').write_text(json.dumps(
            [[o.name, list(o.pose), o.lifted, o.carried, o.slip, o.message, o.felt, o.between, o.skew, o.grip]
             for o in found]), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
