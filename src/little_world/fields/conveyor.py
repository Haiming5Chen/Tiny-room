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
"""
from math import cos, pi, sin, sqrt

from little_world.core.command import Torque
from little_world.core.component import Body, Geometry, Hinge, Motor, Transform

ROLLER = (.025, .200)       # m: radius, length - 50 mm rollers, 200 mm between the side frames
TUBE = .185                 # kg: a 50 mm steel tube 1.5 mm thick, 200 mm long, and its ends
PITCH = .055                # m between roller axes: 5 mm gaps
ROLLERS = 9                 # 0.495 m of rollers
TOP = .12                   # m: the rollers' tops, the height of the Fetch table's top
SPEED = .10                 # m/s at the rollers' surface: 4 rad/s
DRIVE = (.2, 1.)            # each roller's velocity servo: N m per rad/s, and its torque limit, N m
PALLET = (.16, .16, .015)   # m: an HDPE pallet, 0.37 kg
GUIDE = .006                # m: each side guide's clearance to a pallet
START = (.20, .75)          # m: x of the first roller's axis, y of the conveyor's centre line
CUBE = (.025, .025, .025)   # the kit's wooden cube, carried on each pallet


def roller_x(i):
    return START[0] + i * PITCH


def stop_x():
    """Where the stop plate's face is: half a pitch past the last roller's axis."""
    return roller_x(ROLLERS - 1) + PITCH / 2


def bed_x():
    return (roller_x(0) + roller_x(ROLLERS - 1)) / 2


def at_stop(k=1):
    """Where pallet `k` comes to rest, the ones before it queued ahead of it: its centre's x."""
    return stop_x() - PALLET[0] / 2 - (k - 1) * PALLET[0]


def tube_density():
    """A solid roller as heavy as the steel tube, kg/m3: its own inertia, MuJoCo's from its shape."""
    r, length = ROLLER
    return TUBE / (pi * r * r * length + 4 / 3 * pi * r ** 3)


def entities(pallets=2, load=True):
    """The conveyor's parts - a bed, its rollers on hinges with their motors, two side guides
    and the stop plate - and `pallets` pallets at its start, each with the kit's cube on it when
    `load`: (field parts, props)."""
    from . import fixed, loose
    r, length = ROLLER
    y0, axis_z = START[1], TOP - r
    # The bed is the rollers' parent. MuJoCo does not filter contacts between a child and a
    # parent welded to the world (ADR 0020): it lies 15 mm under them, out of their reach.
    bed_z = axis_z - r - .020
    span = (ROLLERS - 1) * PITCH + 2 * r
    parts = [fixed('conveyor_bed', (span, length + 2 * r, .010), 'stand', (bed_x(), y0, bed_z))]
    along_y = (cos(-pi / 4), sin(-pi / 4), 0., 0.)     # a capsule's own axis (z) turned to lie along y
    for i in range(ROLLERS):
        name = f'roller_{i}'
        # Positions are in the bed's frame: the rollers are its children.
        parts.append(Body(name, Geometry('capsule', (r, length)), 'roller',
                          transform=Transform((roller_x(i) - bed_x(), 0., axis_z - bed_z), along_y), parent='conveyor_bed'))
        parts.append(Hinge(f'{name}_hinge', name, (0., 0., 1.), .0001))
        parts.append(Motor(f'{name}_motor', f'{name}_hinge', DRIVE[1]))
    # The side guides and the stop stand 2 mm clear of the rollers' tops: welded to the world,
    # they would grind against rollers that reached them.
    half = PALLET[1] / 2 + GUIDE
    for i, side in enumerate((1, -1)):
        parts.append(fixed(f'conveyor_guide_{i}', (span, .006, .030), 'stand', (bed_x(), y0 + side * (half + .003), TOP + .017)))
    parts.append(fixed('conveyor_stop', (.006, length, .030), 'stand', (stop_x() + .003, y0, TOP + .017)))
    # The side frames a conveyor's rollers turn between, 3 mm clear of the capsules' round ends.
    for i, side in enumerate((1, -1)):
        parts.append(fixed(f'conveyor_frame_{i}', (span, .006, 2 * r + .01), 'stand',
                           (bed_x(), y0 + side * (length / 2 + r + .006), axis_z)))
    props = []
    for k in range(pallets):
        # Pallet 1 nearest the stop, each next 20 mm behind the one before.
        x = roller_x(0) - r + PALLET[0] / 2 + (pallets - 1 - k) * (PALLET[0] + .02)
        props.append(loose(f'pallet_{k + 1}', PALLET, 'pallet', (x, y0, TOP + PALLET[2] / 2 + .0005)))
        if load:
            props.append(loose(f'cube_{k + 1}', CUBE, 'cube', (x, y0, TOP + PALLET[2] + CUBE[2] / 2 + .001)))
    return parts, props


def actuate(state, speed=SPEED):
    """Each roller held at the conveyor's speed by its own velocity servo, whose damping the
    solver integrates (ADR 0014): its top moving +x at `speed`."""
    kv, most = DRIVE
    target = speed / ROLLER[0]
    out = {}
    for i in range(ROLLERS):
        spin = state.bodies[f'field/roller_{i}'].angular_velocity[1]     # about +y: the top moves +x
        torque = kv * (target - spin)
        out[f'field/roller_{i}_motor'] = Torque(torque, -kv) if abs(torque) < most else (most if torque > 0 else -most)
    return out


def surface_speed(state):
    """The rollers' mean surface speed now, m/s."""
    return sum(state.bodies[f'field/roller_{i}'].angular_velocity[1] for i in range(ROLLERS)) * ROLLER[0] / ROLLERS


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
