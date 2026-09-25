"""Test fields: scenes with goals for any machine built in the workshop (ADR 0013).

Every field is authored in the machine's start frame - the machine stays at the origin
facing +X - so choosing a field never moves the design. Props are ordinary Blueprint
bodies with sourced surfaces (ADR 0010); nothing here is simulated specially.
Standard library only.
"""
from dataclasses import dataclass
from math import cos, radians, sin
from little_world.components import Transform, box
from little_world.core.blueprint import Blueprint
from little_world.core.component import Body, Geometry
from little_world.core.entity import Entity
from little_world.core.material import Material
from little_world.core.scene import Scene
from .goals import Line, Undisturbed, Upright, Zone


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

    def scene(self, machine):
        return Scene((*self.build(), machine), backdrop=self.backdrop)


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


CURBS = ((1.2, .010), (2.6, .020), (4.0, .035))   # centre along X, height
CURB_DEPTH, CURB_WIDTH = .2, 1.8


def curbs_entities():
    parts = slab()
    for x, h in CURBS:
        parts.append(fixed(f'curb_{round(h * 1000)}mm', (CURB_DEPTH, CURB_WIDTH, h), 'curb', (x, 0., h / 2)))
    return field_entities(parts)


def curbs_goals():
    goals = []
    for x, h in CURBS:
        line = x + CURB_DEPTH / 2 + .02
        goals.append(Line(f'curb_{round(h * 1000)}', f'Cleared {round(h * 1000)} mm curb',
                          (line, -CURB_WIDTH / 2), (line, CURB_WIDTH / 2), whole=True))
    goals.append(Upright('upright', 'Stayed upright'))
    return tuple(goals)


CURB_RUN = Field('curbs', 'Curb run',
                 'Concrete curbs 10, 20 and 35 mm high across the lane. Cleared means all of the machine is over.',
                 curbs_entities, goals=curbs_goals())


def push_entities():
    return field_entities(slab(), (loose('crate', (.35, .35, .25), 'crate', (1.2, 0., .125)),))


PUSH = Field('push', 'Push the crate',
             'A 4 kg wooden crate on concrete (friction 0.40): push it past the 3 m line.',
             push_entities,
             goals=(Zone('delivered', 'Crate past 3 m', (3.0, -3.9, -.1), (10.9, 3.9, 1.), target='objects/crate'),
                    Upright('upright', 'Stayed upright')),
             markings=(((3.0, -1.), (3.0, 1.)),))


TRAY = (.30, .30)    # tray centre; the stand and cube are where the workshop has them


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
    goals=(Zone('lifted', 'Cube lifted 5 cm', (-2., -2., .258), (2., 2., 3.), target='objects/grasp_cube'),
           Zone('placed', 'Cube resting in the tray', (TRAY[0] - .064, TRAY[1] - .064, 0.), (TRAY[0] + .064, TRAY[1] + .064, .06),
                target='objects/grasp_cube', rest=True, after='lifted')),
    home=((.3, .1, .2), 1.5, 150., -32.))


FIELDS = {f.id: f for f in (WORKSHOP, SPRINT, SLALOM, RAMPS, CURB_RUN, PUSH, PICK_PLACE)}


def field_scene(field_id, machine):
    if field_id not in FIELDS:
        raise ValueError(f'Unknown test field: {field_id}')
    return FIELDS[field_id].scene(machine)
