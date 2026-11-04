"""A powered roller conveyor carrying pallets to a stop plate (FR-007). Standard library only.

A belt is a surface that moves; MuJoCo models one from 3.11 on (`geom/surfacevel`), past the
pin (ADR 0027). Rollers turning on hinges work on any release, and are what light conveyors are
made of: a row of rollers, each held at one speed. What they carry must rest on three rollers at
any time (Interroll, "Conveyor rollers: planning"), so parts as short as the kit's cube or the
cell's 32 mm blocks ride on pallets, as on an assembly line: 160 mm pallets over 50 mm steel
rollers 55 mm apart. At the far end a stop plate holds the first pallet where a machine can pick
from it; the rollers turn on under it, and each pallet behind queues against the one in front.

Two things MuJoCo needs, measured (ADR 0067): a box laid across cylinders sinks into them - 3.10
has no box-on-cylinder collider of its own, and with multiccd off its general one gives a single
point - so the rollers are capsules, whose collider with a box is MuJoCo's own; and rollers as
light as a 20 mm aluminium one let a light pallet hop over them, where a steel tube's inertia
carries it steadily.

A `Line` is one conveyor laid out in a scene: the test field's (`FIELD`) or the factory cell's
feeder (ADR 0068), which carries the other way along x, on the cell's table.
"""
from dataclasses import dataclass
from math import cos, pi, sin

from little_world.core.command import Torque
from little_world.core.component import Body, Geometry, Hinge, Motor, Transform

ROLLER = (.025, .200)       # m: radius, length - 50 mm rollers, 200 mm between the side frames
TUBE = .185                 # kg: a 50 mm steel tube 1.5 mm thick, 200 mm long, and its ends
PITCH = .055                # m between roller axes: 5 mm gaps
ROLLERS = 9                 # 0.495 m of rollers
TOP = .12                   # m: the rollers' tops, the height of the Fetch table's top
SPEED = .10                 # m/s at the rollers' surface: 4 rad/s
DRIVE = (.2, 1.)            # each roller's velocity servo: N m per rad/s, and its torque limit, N m
# A friction roller's drive passes to its tube at most this share of the load on it: 4 to 6 % for a
# 50 mm roller with a friction element on one side (Interroll, "Conveyor rollers: planning basics").
# Its tube stops under a load the stop holds while its drive turns on (ADR 0068).
CONVEY = .05
G = 9.81
PALLET = (.16, .16, .015)   # m: an HDPE pallet, 0.37 kg
DENSITY = 950               # kg/m3: the pallets' HDPE (fields' 'pallet' material)
GUIDE = .006                # m: each side guide's clearance to a pallet
START = (.20, .75)          # m: x of the first roller's axis, y of the conveyor's centre line
CUBE = (.025, .025, .025)   # the kit's wooden cube, carried on each pallet
BED = .015                  # m from the rollers' undersides down to their bed's top
FRAME = .045                # m: the side frames' height, from 5 mm under the rollers' undersides


def _box(name, size, material, position):
    return Body(name, Geometry('box', size), material, transform=Transform(position))


@dataclass(frozen=True)
class Line:
    """A conveyor laid out: its first roller's axis at x `start[0]`, its centre line at y `start[1]`,
    carrying towards +x (`heading` 1) or -x (-1), its rollers' tops at height `top`; its parts are
    named in the entity `entity` of the scene it is in."""
    start: tuple = START
    top: float = TOP
    heading: int = 1
    entity: str = 'field'
    drive: tuple = DRIVE        # each roller's velocity servo: N m per rad/s, and its torque limit, N m
    friction: bool = True       # friction rollers (ADR 0068): the drive passes CONVEY of a pallet's load
    load: float = .0102         # kg a pallet carries: the kit's cube

    def __post_init__(self):
        if self.heading not in (1, -1):
            raise ValueError('a conveyor carries along +x (heading 1) or -x (-1)')

    def roller_x(self, i):
        return self.start[0] + self.heading * i * PITCH

    def stop_x(self):
        """Where the stop plate's face is: half a pitch past the last roller's axis."""
        return self.roller_x(ROLLERS - 1) + self.heading * PITCH / 2

    def bed_x(self):
        return (self.roller_x(0) + self.roller_x(ROLLERS - 1)) / 2

    def at_stop(self, k=1):
        """Where pallet `k` comes to rest, the ones before it queued ahead of it: its centre's x."""
        return self.stop_x() - self.heading * (PALLET[0] / 2 + (k - 1) * PALLET[0])

    def entry(self):
        """Where a pallet set on at the line's start has its centre: its back edge over the first
        roller's outer side."""
        return self.roller_x(0) - self.heading * ROLLER[0] + self.heading * PALLET[0] / 2

    def pallet_z(self):
        """A pallet's centre's height, resting on the rollers."""
        return self.top + PALLET[2] / 2

    def footprint(self):
        """(x low, y low, x high, y high): what the conveyor covers from above - rollers, frames
        and stop plate."""
        r, length = ROLLER
        xs = (self.roller_x(0) - self.heading * r, self.stop_x() + self.heading * .006)
        half = length / 2 + r + .009
        return min(xs), self.start[1] - half, max(xs), self.start[1] + half

    def bed_bottom(self):
        """The height of its bed's underside: what it stands on."""
        return self.top - 2 * ROLLER[0] - BED - .010

    def parts(self, stand='stand', roller='roller'):
        """The conveyor's parts: a bed, its rollers on hinges with their motors, two side guides,
        the stop plate and the side frames."""
        r, length = ROLLER
        y0, axis_z = self.start[1], self.top - r
        # The bed is the rollers' parent. MuJoCo does not filter contacts between a child and a
        # parent welded to the world (ADR 0020): it lies BED under them, out of their reach.
        bed_z = axis_z - r - .020                           # BED, and half the bed's thickness
        span = (ROLLERS - 1) * PITCH + 2 * r
        parts = [_box('conveyor_bed', (span, length + 2 * r, .010), stand, (self.bed_x(), y0, bed_z))]
        along_y = (cos(-pi / 4), sin(-pi / 4), 0., 0.)     # a capsule's own axis (z) turned to lie along y
        for i in range(ROLLERS):
            name = f'roller_{i}'
            # Positions are in the bed's frame: the rollers are its children.
            parts.append(Body(name, Geometry('capsule', (r, length)), roller,
                              transform=Transform((self.roller_x(i) - self.bed_x(), 0., axis_z - bed_z), along_y),
                              parent='conveyor_bed'))
            parts.append(Hinge(f'{name}_hinge', name, (0., 0., 1.), .0001))
            parts.append(Motor(f'{name}_motor', f'{name}_hinge', DRIVE[1]))
        # The side guides and the stop stand 2 mm clear of the rollers' tops: welded to the world,
        # they would grind against rollers that reached them.
        half = PALLET[1] / 2 + GUIDE
        for i, side in enumerate((1, -1)):
            parts.append(_box(f'conveyor_guide_{i}', (span, .006, .030), stand,
                              (self.bed_x(), y0 + side * (half + .003), self.top + .017)))
        parts.append(_box('conveyor_stop', (.006, length, .030), stand,
                          (self.stop_x() + self.heading * .003, y0, self.top + .017)))
        # The side frames a conveyor's rollers turn between, 3 mm clear of the capsules' round ends,
        # their tops 10 mm under the rollers': a hand lowering a part beside the line clears them
        # (ADR 0068).
        for i, side in enumerate((1, -1)):
            parts.append(_box(f'conveyor_frame_{i}', (span, .006, FRAME), stand,
                              (self.bed_x(), y0 + side * (length / 2 + r + .006), self.top - .010 - FRAME / 2)))
        return parts

    def actuate(self, state, speed=SPEED):
        """Each roller held at the conveyor's speed by its own velocity servo, whose damping the
        solver integrates (ADR 0014): its top moving along the heading at `speed`."""
        return self.torques(self.spins(state), speed)

    def spins(self, state):
        """Each roller's spin now, rad/s about +y (positive: its top moving +x)."""
        return [state.bodies[f'{self.entity}/roller_{i}'].angular_velocity[1] for i in range(ROLLERS)]

    def clutch(self):
        """The most torque a roller's drive passes to its tube, N m: a friction roller's CONVEY of
        the load a pallet and what it carries put on each roller under it (ADR 0068), else the
        servo's own limit."""
        if not self.friction:
            return self.drive[1]
        pallet = PALLET[0] * PALLET[1] * PALLET[2] * DENSITY
        return min(self.drive[1], CONVEY * (pallet + self.load) * G * PITCH / PALLET[0] * ROLLER[0])

    def torques(self, spins, speed=SPEED):
        """The rollers' motors' commands for their spins now (rad/s about +y)."""
        kv, most = self.drive[0], self.clutch()
        target = self.heading * speed / ROLLER[0]
        out = {}
        for i, spin in enumerate(spins):
            torque = kv * (target - spin)
            out[f'{self.entity}/roller_{i}_motor'] = Torque(torque, -kv) if abs(torque) < most else (most if torque > 0 else -most)
        return out

    def surface_speed(self, state):
        """The rollers' mean surface speed now along the heading, m/s."""
        return self.heading * sum(self.spins(state)) * ROLLER[0] / ROLLERS


FIELD = Line()


def roller_x(i):
    return FIELD.roller_x(i)


def stop_x():
    """Where the field's stop plate's face is: half a pitch past the last roller's axis."""
    return FIELD.stop_x()


def bed_x():
    return FIELD.bed_x()


def at_stop(k=1):
    """Where the field's pallet `k` comes to rest, the ones before it queued ahead of it: its centre's x."""
    return FIELD.at_stop(k)


def tube_density():
    """A solid roller as heavy as the steel tube, kg/m3: its own inertia, MuJoCo's from its shape."""
    r, length = ROLLER
    return TUBE / (pi * r * r * length + 4 / 3 * pi * r ** 3)


def entities(pallets=2, load=True):
    """The field's conveyor - `Line.parts` - and `pallets` pallets at its start, each with the kit's
    cube on it when `load`: (field parts, props)."""
    from . import loose
    r = ROLLER[0]
    y0 = START[1]
    props = []
    for k in range(pallets):
        # Pallet 1 nearest the stop, each next 20 mm behind the one before.
        x = roller_x(0) - r + PALLET[0] / 2 + (pallets - 1 - k) * (PALLET[0] + .02)
        props.append(loose(f'pallet_{k + 1}', PALLET, 'pallet', (x, y0, TOP + PALLET[2] / 2 + .0005)))
        if load:
            props.append(loose(f'cube_{k + 1}', CUBE, 'cube', (x, y0, TOP + PALLET[2] + CUBE[2] / 2 + .001)))
    return FIELD.parts(), props


def actuate(state, speed=SPEED):
    """The field's rollers held at the conveyor's speed (`Line.actuate`)."""
    return FIELD.actuate(state, speed)


def surface_speed(state):
    """The field's rollers' mean surface speed now, m/s."""
    return FIELD.surface_speed(state)


def goals():
    """Each pallet at rest where the stop and the pallets ahead hold it - within 5 mm along the
    conveyor, 10 mm across it, flat on the rollers, not climbing - and the first one's cube still
    on it."""
    from .goals import Zone
    z = TOP + PALLET[2] / 2
    y0 = START[1]
    out = []
    for k, label in ((1, 'Pallet 1 at the stop'), (2, 'Pallet 2 queued behind it')):
        x = at_stop(k)
        out.append(Zone(f'pallet_{k}', label, (x - .005, y0 - .01, z - .002), (x + .002, y0 + .01, z + .002),
                        target=f'objects/pallet_{k}', rest=True))
    cz = TOP + PALLET[2] + CUBE[2] / 2
    out.append(Zone('cube_1', 'Its cube still on it', (at_stop(1) - .03, y0 - .03, cz - .003), (at_stop(1) + .03, y0 + .03, cz + .003),
                    target='objects/cube_1', rest=True, after='pallet_1'))
    return tuple(out)
