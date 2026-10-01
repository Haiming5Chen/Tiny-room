"""Test fields: scenes with goals for any machine built in the workshop (ADR 0013).

Every field is authored in the machine's start frame - the machine stays at the origin
facing +X - so choosing a field never moves the design. Props are ordinary Blueprint
bodies with sourced surfaces (ADR 0010); nothing here is simulated specially.
Standard library only.
"""
from dataclasses import dataclass
from math import atan2, cos, degrees, radians, sin, tan
from little_world.components import Transform, box
from little_world.construction.structure import outline
from little_world.core.blueprint import Blueprint
from little_world.core.command import Torque
from little_world.core.component import Body, Geometry, Hinge, Motor
from little_world.core.entity import Entity
from little_world.core.material import Material
from little_world.core.scene import Scene
from .goals import Line, TiltHold, Undisturbed, Upright, Zone


@dataclass(frozen=True)
class Field:
    id: str
    title: str
    summary: str
    build: object                  # () -> tuple of Entities; everything but the machine
    goals: tuple = ()
    markings: tuple = ()           # extra floor lines ((x0, y0), (x1, y1)): lane edges
    backdrop: str | None = 'sky'
    home: tuple = ((2.8, 0., .2), 6.5, -30., -28.)   # look-at, distance, azimuth, elevation
    # A field that moves (ADR 0020): State -> {actuator: torque command} for its own
    # motors, applied each step beside the machine's; None for a still field.
    actuate: object = None
    # A field fitted to the machine (ADR 0020): `build` takes the machine's Blueprint, as
    # a tilt table's trip rail is set against the wheels of whatever stands on it.
    fitted: bool = False
    # A static test (ADR 0020): State -> degrees the field has reached, read on a gauge
    # instead of the drive telemetry; `side` is the tipping side of the machine it tests,
    # compared with the stance's prediction; `ground` are field bodies the machine stands on.
    reading: object = None
    gauge_top: float = 90.
    side: str | None = None
    ground: tuple = ()

    def scene(self, machine):
        parts = self.build(machine.blueprint) if self.fitted else self.build()
        return Scene((*parts, machine), backdrop=self.backdrop)

    def commands(self, state):
        return {} if self.actuate is None or state is None else self.actuate(state)


# -- materials: surfaces name the real thing, so contact friction is sourced ---------------

PALETTE = (
    Material('slab', 2400, .6, (.80, .80, .78, 1), 'concrete', .85, 'concrete'),
    Material('barrier', 950, .3, (.93, .72, .18, 1), 'matte_plastic', .7, 'hdpe'),
    Material('plywood', 600, .4, (.86, .74, .55, 1), 'matte_plastic', .85, 'wood'),
    Material('bollard', 950, .3, (.96, .42, .12, 1), 'matte_plastic', .6, 'hdpe'),
    Material('curb', 2400, .6, (.62, .62, .60, 1), 'concrete', .9, 'concrete'),
    # A 4 kg crate: hollow, so its density is the crate's mass over its outer volume.
    Material('crate', 130, .4, (.86, .66, .40, 1), 'wood_grain', .8, 'wood'),
    Material('stand', 2700, .5, (.12, .17, .19, 1), surface='aluminium'),
    Material('cube', 650, .6, (.91, .84, .65, 1), surface='wood'),
    Material('tray', 950, .3, (.25, .55, .75, 1), 'matte_plastic', .6, 'hdpe'),
)
SLAB = (14., 8.)       # metres; x from -3 to 11, y from -4 to 4
X0 = -3.


def fixed(name, size, material, position, quaternion=(1., 0., 0., 0.)):
    return box(name, size, material, transform=Transform(position, quaternion))


def loose(name, size, material, position):
    return box(name, size, material, dynamic=True, transform=Transform(position))


def slab():
    """A concrete floor with a low barrier round it, so nothing leaves the field."""
    length, width = SLAB
    cx = X0 + length / 2
    parts = [fixed('floor', (length, width, .08), 'slab', (cx, 0., -.04))]
    for i, y in enumerate((width / 2 + .05, -width / 2 - .05)):
        parts.append(fixed(f'barrier_{i}', (length + .2, .1, .25), 'barrier', (cx, y, .125)))
    for i, x in enumerate((X0 - .05, X0 + length + .05)):
        parts.append(fixed(f'barrier_{i + 2}', (.1, width + .2, .25), 'barrier', (x, 0., .125)))
    return parts


def field_entities(parts, props=()):
    entities = [Entity('field', Blueprint(tuple(parts), PALETTE))]
    if props:
        entities.append(Entity('objects', Blueprint(tuple(props), PALETTE)))
    return tuple(entities)


# -- the fields ------------------------------------------------------------------------

def workshop_field():
    from little_world.scenes.workshop import workshop_entities
    return workshop_entities()


WORKSHOP = Field('workshop', 'Workshop room',
                 'The furnished room: free driving and the arm pickup stand. No goals.',
                 workshop_field, backdrop=None, home=((.1, .45, .3), 5.4, 125., -32.))


LANE = .7
SPRINT = Field(
    'sprint', 'Sprint lane',
    'Five metres on concrete between a start and a finish line. Times the run.',
    lambda: field_entities(slab()),
    goals=(Line('start', 'Start line', (.6, -LANE), (.6, LANE)),
           Line('finish', '5 m finish', (5.6, -LANE), (5.6, LANE), after='start', since='start'),
           Upright('upright', 'Stayed upright')),
    markings=(((.6, -LANE), (5.6, -LANE)), ((.6, LANE), (5.6, LANE))))


GATES = ((1.6, .45), (3.0, -.45), (4.4, .45), (5.8, -.45))


def slalom_entities():
    props = []
    for i, (x, y) in enumerate(GATES):
        for j, side in enumerate((-.4, .4)):
            props.append(Body(f'bollard_{i}_{j}', Geometry('cylinder', (.035, .30)), 'bollard',
                              dynamic=True, transform=Transform((x, y + side, .15))))
    return field_entities(slab(), props)


def slalom_goals():
    goals = [Line('start', 'Start line', (.8, -1.), (.8, 1.))]
    previous = 'start'
    for i, (x, y) in enumerate(GATES):
        goals.append(Line(f'gate_{i + 1}', f'Gate {i + 1}', (x, y - .36), (x, y + .36), after=previous))
        previous = f'gate_{i + 1}'
    goals.append(Line('finish', 'Finish', (7.2, -1.), (7.2, 1.), after=previous, since='start'))
    goals.append(Undisturbed('bollards', 'Bollards left standing',
                             tuple(f'objects/bollard_{i}_{j}' for i in range(len(GATES)) for j in range(2))))
    goals.append(Upright('upright', 'Stayed upright'))
    return tuple(goals)


SLALOM = Field('slalom', 'Slalom',
               'Four bollard gates, left and right, then a finish line. Knocked bollards count.',
               slalom_entities, goals=slalom_goals())


RAMP_START, RAMP_HEIGHT, RAMP_WIDTH, TOP_LENGTH, BOARD = 1.0, .20, .9, 1.4, .03
RAMP_LANES = ((8., 1.3), (14., 0.), (20., -1.3))   # slope in degrees, lane centre y


def ramp_top(angle):
    """Where the slope meets the platform, along X."""
    return RAMP_START + RAMP_HEIGHT / sin(radians(angle)) * cos(radians(angle))


def ramps_entities(lanes=RAMP_LANES):
    parts = slab()
    for angle, y in lanes:
        a = radians(angle)
        length = RAMP_HEIGHT / sin(a)
        centre = (RAMP_START + length / 2 * cos(a) + BOARD / 2 * sin(a), y,
                  length / 2 * sin(a) - BOARD / 2 * cos(a))
        tag = f'{angle:g}'
        parts.append(fixed(f'ramp_{tag}', (length, RAMP_WIDTH, BOARD), 'plywood', centre,
                           (cos(a / 2), 0., -sin(a / 2), 0.)))
        top = ramp_top(angle)
        parts.append(fixed(f'platform_{tag}', (TOP_LENGTH, RAMP_WIDTH, RAMP_HEIGHT), 'plywood',
                           (top + TOP_LENGTH / 2, y, RAMP_HEIGHT / 2)))
        parts.append(fixed(f'stop_{tag}', (.06, RAMP_WIDTH, .08), 'plywood',
                           (top + TOP_LENGTH - .03, y, RAMP_HEIGHT + .04)))
    return field_entities(parts)


def ramps_goals(lanes=RAMP_LANES):
    goals = []
    for angle, y in lanes:
        top = ramp_top(angle)
        goals.append(Zone(f'climb_{angle:g}', f'Climbed {angle:g} deg',
                          (top + .15, y - RAMP_WIDTH / 2, RAMP_HEIGHT - .02),
                          (top + TOP_LENGTH, y + RAMP_WIDTH / 2, RAMP_HEIGHT + 1.)))
    goals.append(Upright('upright', 'Stayed upright'))
    return tuple(goals)


RAMPS = Field('ramps', 'Ramps',
              'Plywood ramps of 8, 14 and 20 degrees up to a 20 cm deck: left, ahead, right.',
              ramps_entities, goals=ramps_goals(), home=((2.0, 0., .3), 5.5, -35., -25.))


CURB_HEIGHTS = (.010, .020, .035)                  # m, in the order met
CURB_FIRST, CURB_STEP = 1.2, 1.4                   # m along X to the first curb's centre, between curbs
CURB_DEPTH, CURB_WIDTH = .2, 1.8


def curbs_entities(heights=CURB_HEIGHTS):
    parts = slab()
    for i, h in enumerate(heights):
        parts.append(fixed(f'curb_{round(h * 1000)}mm', (CURB_DEPTH, CURB_WIDTH, h), 'curb',
                           (CURB_FIRST + i * CURB_STEP, 0., h / 2)))
    return field_entities(parts)


def curbs_goals(heights=CURB_HEIGHTS):
    goals = []
    for i, h in enumerate(heights):
        line = CURB_FIRST + i * CURB_STEP + CURB_DEPTH / 2 + .02
        goals.append(Line(f'curb_{round(h * 1000)}', f'Cleared {round(h * 1000)} mm curb',
                          (line, -CURB_WIDTH / 2), (line, CURB_WIDTH / 2), whole=True))
    goals.append(Upright('upright', 'Stayed upright'))
    return tuple(goals)


def curb_run(heights=CURB_HEIGHTS):
    """The Curb run with curbs of other heights, for a check that needs them (ADR 0013)."""
    words = ', '.join(f'{round(h * 1000)}' for h in heights[:-1]) + f' and {round(heights[-1] * 1000)}'
    return Field('curbs', 'Curb run',
                 f'Concrete curbs {words} mm high across the lane. Cleared means all of the machine is over.',
                 lambda: curbs_entities(heights), goals=curbs_goals(heights))


CURB_RUN = curb_run()


def push_entities():
    return field_entities(slab(), (loose('crate', (.35, .35, .25), 'crate', (1.2, 0., .125)),))


PUSH = Field('push', 'Push the crate',
             'A 4 kg wooden crate on concrete (friction 0.40): push it past the 3 m line.',
             push_entities,
             goals=(Zone('delivered', 'Crate past 3 m', (3.0, -3.9, -.1), (10.9, 3.9, 1.), target='objects/crate'),
                    Upright('upright', 'Stayed upright')),
             markings=(((3.0, -1.), (3.0, 1.)),))


# Tray centre; the stand and cube are where the workshop has them. At (.30, .30) - 0.42 m
# from the arm's axis - a level tool 2 cm above the tray's floor was beyond the standard arm's
# reach (ADR 0016); 0.36 m leaves the arm room to lower the cube level, and the tray
# stays clear of the largest test machine (the six-wheel rover is 0.43 m wide).
TRAY = (.20, .30)


def pick_place_entities():
    tx, ty = TRAY
    parts = slab()
    parts.append(fixed('pickup_stand', (.065, .085, .187), 'stand', (.460, 0., .0935)))
    parts.append(fixed('tray_base', (.14, .14, .006), 'tray', (tx, ty, .003)))
    for i, (dx, dy, sx, sy) in enumerate(((.067, 0, .006, .14), (-.067, 0, .006, .14),
                                          (0, .067, .14, .006), (0, -.067, .14, .006))):
        parts.append(fixed(f'tray_wall_{i}', (sx, sy, .03), 'tray', (tx + dx, ty + dy, .015)))
    props = (loose('grasp_cube', (.025, .025, .040), 'cube', (.460, 0., .208)),)
    return field_entities(parts, props)


PICK_PLACE = Field(
    'pick_place', 'Pick and place',
    'The pickup stand and cube, and a tray beside the arm: lift the cube, then set it in the tray.',
    pick_place_entities,
    # Resting in the tray means on its floor (the cube's centre 26 mm up standing, 18.5 mm
    # on its side): held still a centimetre above it by a closed gripper does not count.
    goals=(Zone('lifted', 'Cube lifted 5 cm', (-2., -2., .258), (2., 2., 3.), target='objects/grasp_cube'),
           Zone('placed', 'Cube resting in the tray', (TRAY[0] - .064, TRAY[1] - .064, 0.), (TRAY[0] + .064, TRAY[1] + .064, .032),
                target='objects/grasp_cube', rest=True, after='lifted')),
    home=((.3, .1, .2), 1.5, 150., -32.))


TABLE = (2.0, 0., .40, .50, .12)    # centre x, y; depth, width, height (m)
FETCH_CUBE = (1.84, 0.)             # 4 cm behind the table's front edge
BIN, BIN_SIZE, BIN_WALL = (.5, .8), .20, .04   # a bin on the floor, left of the start


def fetch_entities():
    x, y, depth, width, height = TABLE
    parts = slab()
    parts.append(fixed('table', (depth, width, height), 'plywood', (x, y, height / 2)))
    bx, by = BIN
    half = BIN_SIZE / 2
    parts.append(fixed('bin_base', (BIN_SIZE, BIN_SIZE, .006), 'tray', (bx, by, .003)))
    for i, (dx, dy, sx, sy) in enumerate(((half - .003, 0, .006, BIN_SIZE), (-half + .003, 0, .006, BIN_SIZE),
                                          (0, half - .003, BIN_SIZE, .006), (0, -half + .003, BIN_SIZE, .006))):
        parts.append(fixed(f'bin_wall_{i}', (sx, sy, BIN_WALL), 'tray', (bx + dx, by + dy, BIN_WALL / 2)))
    props = (loose('fetch_cube', (.025, .025, .040), 'cube', (FETCH_CUBE[0], FETCH_CUBE[1], height + .020)),)
    return field_entities(parts, props)


def fetch_goals():
    x, y, depth, width, height = TABLE
    front = x - depth / 2
    bx, by = BIN
    inside = BIN_SIZE / 2 - .006
    return (Zone('reached', 'Reached the table', (front - .2, y - width / 2, -1.), (front, y + width / 2, 2.)),
            Zone('lifted', 'Cube lifted 5 cm', (-10., -10., height + .02 + .05), (20., 20., 3.), target='objects/fetch_cube'),
            # On the bin's floor, as in the pick-and-place field: held above it does not count.
            Zone('delivered', 'Cube resting in the bin', (bx - inside, by - inside, 0.), (bx + inside, by + inside, .032),
                 target='objects/fetch_cube', rest=True, after='lifted'),
            Upright('upright', 'Stayed upright'))


FETCH = Field(
    'fetch', 'Fetch',
    'A cube on a table 1.8 m ahead: drive there, pick it up, bring it back and set it in the bin left of the start.',
    fetch_entities, goals=fetch_goals(), home=((1.0, .35, .15), 3.6, -70., -32.))


WALL_X, DOOR_Y, DOOR_WIDTH = 2.0, .5, .50   # a wall across the field, its door off to the left
BAY = ((2.7, .15), (3.5, .85))               # where to park beyond it


def doorway_entities():
    parts = slab()
    half = DOOR_WIDTH / 2
    post = .04
    # Fixed wall either side of the door; the door's frame is two light posts that fall if
    # hit, standing 5 mm clear of the wall so that only a machine can move them.
    left_edge, right_edge = DOOR_Y + half + post + .005, DOOR_Y - half - post - .005
    parts.append(fixed('wall_left', (.10, 3.9 - left_edge, .60), 'barrier', (WALL_X, (3.9 + left_edge) / 2, .30)))
    parts.append(fixed('wall_right', (.10, right_edge + 3.9, .60), 'barrier', (WALL_X, (right_edge - 3.9) / 2, .30)))
    props = tuple(Body(f'door_post_{i}', Geometry('box', (post, post, .60)), 'bollard', dynamic=True,
                       transform=Transform((WALL_X, DOOR_Y + side * (half + post / 2), .30)))
                  for i, side in enumerate((-1, 1)))
    return field_entities(parts, props)


def doorway_goals():
    (x0, y0), (x1, y1) = BAY
    beyond = WALL_X + .10
    return (Line('through', 'Through the doorway', (beyond, DOOR_Y - DOOR_WIDTH / 2), (beyond, DOOR_Y + DOOR_WIDTH / 2), whole=True),
            Zone('parked', 'Reached the bay', (x0, y0, -.1), (x1, y1, 1.), after='through'),
            Undisturbed('frame', 'Door frame untouched', ('objects/door_post_0', 'objects/door_post_1'), shift=.01, lean=5.),
            Upright('upright', 'Stayed upright'))


DOORWAY = Field(
    'doorway', 'Doorway',
    f'A wall 2 m ahead with a {DOOR_WIDTH * 100:.0f} cm door, off to the left: steer through without touching '
    'its frame and park in the bay beyond.',
    doorway_entities, goals=doorway_goals(), markings=((BAY[0], (BAY[1][0], BAY[0][1])), ((BAY[0][0], BAY[1][1]), BAY[1])),
    home=((1.8, .4, .2), 4.2, -60., -35.))


TILT_START, TILT_RATE, TILT_MAX = 1., 2., 60.   # s before it moves, degrees per second, top
TILT_TABLE = (1.4, 1.0, .04)                     # plywood, turning about its centre line (X)
TILT_GAINS, TILT_TORQUE = (3000., 300.), 600.    # N m/rad, N m s/rad; N m
RAIL, RAIL_GAP = .005, .002                      # m: the trip rail's height; its clearance


def trip_rail(blueprint):
    """Where the trip rail's inner face goes, y in the machine's start frame: 2 mm outside
    the lowest parts on its right-hand side, so that it stops a slide before it starts.
    It is low because a machine pressed against it tips about the rail's top edge rather
    than its wheels' own, which raises the tipping angle (see `railed`)."""
    half = TILT_TABLE[1] / 2 - RAIL
    points, _ = outline(blueprint) if blueprint is not None else ((), ())
    if not points:
        return -half
    floor = min(p[2] for p in points)
    low = [p[1] for p in points if p[2] <= floor + .02]
    return max(-half, min(low) - RAIL_GAP)


def railed(tip, height):
    """A tipping angle, degrees, predicted about the wheels' own edge, moved up to the top
    edge of the trip rail they rest against: atan(reach / (height - rail)). For the mobile
    manipulator, 54.3 degrees becomes 55.8."""
    return degrees(atan2(height * tan(radians(tip)), height - RAIL))


def tilt_entities(machine=None):
    """A tilt table: the machine starts on a plywood table that turns about its long
    centre line, left side up. A 5 mm trip rail stands against its right-hand wheels, as
    on a vehicle tilt table, so it cannot slide: what is measured is where it tips. The
    floor is 0.6 m below."""
    length, width, thick = TILT_TABLE
    rail = trip_rail(machine)
    post = length / 2 - .06
    parts = [fixed('floor', (6., 6., .08), 'slab', (1., 0., -.64)),
             # Two posts carry the hinge line, a beam joins them on the floor. They stop 12 cm
             # under the table: MuJoCo does not filter a child against a parent welded to the
             # world, so the turning table must not reach them (to 65 deg).
             Body('tilt_stand', Geometry('box', (.08, .08, .44)), 'stand', transform=Transform((-post, 0., -.38))),
             fixed('tilt_post', (.08, .08, .44), 'stand', (post, 0., -.38)),
             fixed('tilt_beam', (length, .08, .06), 'stand', (0., 0., -.57)),
             Body('tilt_table', Geometry('box', TILT_TABLE), 'plywood', transform=Transform((post, 0., .36)),
                  parent='tilt_stand'),
             Body('tilt_rail', Geometry('box', (length, RAIL, RAIL)), 'plywood',
                  transform=Transform((0., rail - RAIL / 2, (thick + RAIL) / 2)), parent='tilt_table'),
             # A screw-driven table is not back-driven: heavy damping holds it still unpowered.
             Hinge('tilt_hinge', 'tilt_table', (1., 0., 0.), 50., (0., 0., 0.), (-5., TILT_MAX + 5.)),
             Motor('tilt_motor', 'tilt_hinge', TILT_TORQUE)]
    return field_entities(parts)


def tilt_target(time):
    """The table's angle, degrees, at a time into the run."""
    return max(0., min(TILT_MAX, (time - TILT_START) * TILT_RATE))


def table_angle(state):
    """The tilt table's roll about its hinge line, degrees, left side up positive."""
    w, x, y, z = state.bodies['field/tilt_table'].pose.quaternion
    return degrees(atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)))


def tilt_actuate(state):
    """Hold the table on its schedule: a stiff servo whose damping the solver integrates."""
    kp, kd = TILT_GAINS
    rate = state.bodies['field/tilt_table'].angular_velocity[0]
    torque = kp * radians(tilt_target(state.time) - table_angle(state)) - kd * rate
    if abs(torque) >= TILT_TORQUE:
        return {'field/tilt_motor': TILT_TORQUE if torque > 0 else -TILT_TORQUE}
    return {'field/tilt_motor': Torque(torque, -kd)}


def tilt_goals():
    return tuple(TiltHold(f'held_{a}', f'Held at {a} deg', 'field/tilt_table', float(a)) for a in (20, 30, 40, 50)) + \
        (TiltHold('held_60', 'Held at 60 deg', 'field/tilt_table', TILT_MAX - .5),)


TILT = Field(
    'tilt', 'Tilt table',
    f'The machine stands on a table that tilts, left side up, {TILT_RATE:g} deg/s to {TILT_MAX:g} deg, a 5 mm trip '
    'rail against its right-hand wheels. Where it tips over is its static stability.',
    tilt_entities, goals=tilt_goals(), actuate=tilt_actuate, home=((0., 0., .1), 2.6, 90., -12.), fitted=True,
    reading=table_angle, gauge_top=TILT_MAX, side='right', ground=('field/tilt_table',))


FIELDS = {f.id: f for f in (WORKSHOP, SPRINT, SLALOM, RAMPS, CURB_RUN, PUSH, PICK_PLACE, FETCH, DOORWAY, TILT)}


def field_scene(field_id, machine):
    if field_id not in FIELDS:
        raise ValueError(f'Unknown test field: {field_id}')
    return FIELDS[field_id].scene(machine)
