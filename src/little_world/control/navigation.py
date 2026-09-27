"""Driving a differential base to a point (ADR 0018).

`drive_to` is standard library: from the base's pose - where its drive axle's midpoint
is and which way it faces - to a forward speed and a turn rate, then to wheel speeds.
The pose is an ideal observation (exact simulator state), as every program sensor here
is; there is no odometry drift or localisation. `BasePose` reads it from MuJoCo.
"""
from math import atan2, cos, degrees, pi, radians, sin

TURN_FIRST = radians(35.)   # further off the bearing than this, turn on the spot first
SPEED = .22                 # m/s cruising: under the drive assist's 0.425 m/s, to stop well
CREEP = .03                 # m/s: never slower while still short, or friction wins
GAIN = 1.2                  # 1/s: speed falls off this fast with the distance left
TURN = 2.5                  # 1/s: turn rate per radian of heading error
TURN_MAX = 1.2              # rad/s


def wrap(angle):
    """Radians into (-pi, pi]."""
    return (angle + pi) % (2 * pi) - pi


TURN_MIN = .3               # rad/s: slower, a turn on the spot stalls against caster scrub
NEAR = .08                  # m: this close, no more turning on the spot - drive along the heading
CROSS = 3.                  # near the goal, a sideways error this many tolerances is accepted
RESUME = 4.                 # a reached goal is left again only past this many tolerances
BACK_UP = .5                # m: a goal behind and closer than this is reached in reverse


def approach(pose, goal, tolerance):
    """(forward, turn, reached) towards a point, turning on the spot when far off the
    bearing and backing up to a goal close behind rather than turning round - which
    also keeps an arm held out in front from sweeping into what it was just reaching."""
    x, y, yaw = pose
    dx, dy = goal[0] - x, goal[1] - y
    distance = (dx * dx + dy * dy) ** .5
    if distance <= tolerance:
        return 0., 0., True
    if distance < NEAR:
        # Close in, a differential base that keeps turning towards a point a few
        # centimetres to its side circles it. Drive along the heading instead, forward or
        # back, and accept a small sideways error: a non-holonomic base cannot close it
        # without backing away and coming in again.
        along = dx * cos(yaw) + dy * sin(yaw)
        cross = -dx * sin(yaw) + dy * cos(yaw)
        if abs(along) <= tolerance and abs(cross) <= CROSS * tolerance:
            return 0., 0., True
        speed = max(CREEP, min(SPEED, GAIN * abs(along)))
        steer = max(-.5, min(.5, TURN * wrap(atan2(dy, dx) - yaw))) if along > 0 else 0.
        return (speed if along > 0 else -speed), steer, False
    alpha = wrap(atan2(dy, dx) - yaw)
    reverse = distance < BACK_UP and abs(alpha) > pi / 2
    if reverse:
        alpha = wrap(alpha + pi)
    turn = max(-TURN_MAX, min(TURN_MAX, TURN * alpha))
    if abs(alpha) > TURN_FIRST:
        return 0., turn, False
    speed = max(CREEP, min(SPEED, GAIN * distance)) * cos(alpha)
    return (-speed if reverse else speed), turn, False


class GoTo:
    """Drive a base to a point, then turn it to a heading. Stateful so that the small
    drift of a turn on the spot does not send it back to chasing the point: once there,
    it only resumes the approach if it has drifted RESUME tolerances away."""

    def __init__(self, goal, heading=None, tolerance=.01, heading_tolerance=radians(2.)):
        self.goal, self.heading = tuple(goal), heading
        self.tolerance, self.heading_tolerance = tolerance, heading_tolerance
        self.aligning = False

    def step(self, pose):
        """(forward m/s, turn rad/s, arrived) for a base at (x, y, yaw radians)."""
        x, y, yaw = pose
        distance = ((self.goal[0] - x) ** 2 + (self.goal[1] - y) ** 2) ** .5
        if self.aligning and distance > RESUME * self.tolerance:
            self.aligning = False
        if not self.aligning:
            forward, turn, reached = approach(pose, self.goal, self.tolerance)
            if not reached:
                return forward, turn, False
            self.aligning = True
        if self.heading is None:
            return 0., 0., True
        error = wrap(self.heading - yaw)
        if abs(error) <= self.heading_tolerance:
            return 0., 0., True
        turn = max(-TURN_MAX, min(TURN_MAX, TURN * error))
        if abs(turn) < TURN_MIN:
            turn = TURN_MIN if turn > 0 else -TURN_MIN
        return 0., turn, False


def drive_to(pose, goal, heading=None, tolerance=.01, heading_tolerance=radians(2.)):
    """One stateless step of GoTo: (forward m/s, turn rad/s, arrived)."""
    return GoTo(goal, heading, tolerance, heading_tolerance).step(pose)


def wheel_targets(forward, turn, radius, track):
    """Left and right wheel speeds, rad/s, for a forward speed and a turn rate."""
    return (forward - turn * track / 2) / radius, (forward + turn * track / 2) / radius


class BasePose:
    """The drive axle's midpoint and heading of a machine with a differential drive,
    read from MuJoCo, and the wheel radius and track the drive commands need."""

    def __init__(self, backend, drive, blueprint, entity='machine'):
        import numpy as np
        self.np = np
        self.backend = backend
        model = backend.model
        channels = sorted(drive.channels, key=lambda c: c[4])   # side 0 (left) first
        if len(channels) < 2 or {c[4] for c in channels} != {0, 1}:
            raise ValueError('Driving to a point needs a left and a right drive wheel')
        body = lambda c: int(model.jnt_bodyid[model.dof_jntid[c[1]]])
        self.left = [body(c) for c in channels if c[4] == 0]
        self.right = [body(c) for c in channels if c[4] == 1]
        self.root = channels[0][5]
        self.radius = sum(c[3] for c in channels) / len(channels)
        lefts = [c[6] for c in channels if c[4] == 0]
        rights = [c[6] for c in channels if c[4] == 1]
        self.track = abs(sum(lefts) / len(lefts) - sum(rights) / len(rights))

    def pose(self):
        """(x, y, yaw radians) of the axle midpoint, in the field's frame. Forward is
        square to the line from the right wheel to the left one, as a differential drive
        defines it, whatever the chassis's own frame."""
        d = self.backend.data
        left = self.np.mean([d.xpos[b] for b in self.left], axis=0)
        right = self.np.mean([d.xpos[b] for b in self.right], axis=0)
        centre = (left + right) / 2
        lateral = left - right
        return float(centre[0]), float(centre[1]), float(atan2(-lateral[0], lateral[1]))

    def degrees(self):
        x, y, yaw = self.pose()
        return x, y, degrees(yaw)
