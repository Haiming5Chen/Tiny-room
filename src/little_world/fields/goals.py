"""Goals a test field sets, judged from body poses and velocities alone (ADR 0013).

Standard library only. A goal reads the core `State` - the same snapshot every backend
returns - so the judging does not depend on MuJoCo or on the UI. Coordinates are the
field's, which is the machine's start frame: the machine starts at the origin facing +X.
"""
from dataclasses import dataclass
from math import acos, degrees, dist

MACHINE = 'machine/'


def tilt(quaternion):
    """Degrees between a body's +Z axis and the world's."""
    w, x, y, z = quaternion
    return degrees(acos(max(-1., min(1., 1. - 2. * (x * x + y * y)))))


def up(quaternion):
    """A body's +Z axis in the world."""
    w, x, y, z = quaternion
    return (2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y))


def between(a, b):
    """Degrees between two bodies' +Z axes."""
    u, v = up(a), up(b)
    return degrees(acos(max(-1., min(1., sum(p * q for p, q in zip(u, v))))))


@dataclass(frozen=True)
class Line:
    """Met when the machine gets past a segment: any body of it (the nose), or all of it
    (`whole`, a curb cleared). Past means on the side the segment's right-hand normal
    points to - for a segment drawn from right to left across the lane, forward."""
    id: str
    label: str
    a: tuple
    b: tuple
    after: str | None = None    # a goal that must be met first: gates in order
    since: str | None = None    # report the time since this goal was met: a split
    whole: bool = False

    def past(self, point):
        (ax, ay), (bx, by) = self.a, self.b
        dx, dy = bx - ax, by - ay
        px, py = point[0] - ax, point[1] - ay
        along = (px * dx + py * dy) / (dx * dx + dy * dy)
        return 0. <= along <= 1. and px * dy - py * dx > 0.

    def check(self, machine, state):
        points = [state.bodies[name].pose.position for name in machine]
        if not points:
            return False
        if self.whole:
            (ax, ay), (bx, by) = self.a, self.b
            dx, dy = bx - ax, by - ay
            return all((p[0] - ax) * dy - (p[1] - ay) * dx > 0. for p in points) and \
                any(self.past(p) for p in points)
        return any(self.past(p) for p in points)


@dataclass(frozen=True)
class Zone:
    """Met when the target is inside an axis-aligned box: the machine (any of its bodies)
    or a named body; `rest` also asks that it has stopped moving."""
    id: str
    label: str
    lo: tuple
    hi: tuple
    target: str | None = None
    rest: bool = False
    after: str | None = None
    since: str | None = None

    def inside(self, point):
        return all(l <= v <= h for l, v, h in zip(self.lo, point, self.hi))

    def check(self, machine, state):
        if self.target is None:
            return any(self.inside(state.bodies[name].pose.position) for name in machine)
        body = state.bodies[self.target]
        still = sum(v * v for v in body.linear_velocity) ** .5 < .02
        return self.inside(body.pose.position) and (still or not self.rest)


@dataclass(frozen=True)
class Upright:
    """Kept while the machine's base stays within `max_tilt` of upright."""
    id: str
    label: str
    max_tilt: float = 45.


@dataclass(frozen=True)
class Undisturbed:
    """Kept while none of the named bodies has been moved or knocked over."""
    id: str
    label: str
    bodies: tuple
    shift: float = .05          # metres over the floor
    lean: float = 25.           # degrees from upright


@dataclass(frozen=True)
class TiltHold:
    """Met when a tilting table (a body of the field) passes `angle` degrees with the
    machine still standing on it - its base within `lean` degrees of the table's own
    up. Missed, with the angle it went over at, once the machine has tipped past
    `tipped` degrees relative to the table (ADR 0020)."""
    id: str
    label: str
    table: str
    angle: float
    lean: float = 10.
    tipped: float = 25.


@dataclass(frozen=True)
class Result:
    id: str
    label: str
    status: str                 # 'met', 'missed', 'kept', 'failed', or 'open' while running
    time: float | None = None   # seconds from the start of the run
    detail: str = ''


class GoalTracker:
    """Follows a run's goals from one State to the next."""

    def __init__(self, goals, root):
        self.goals = tuple(goals)
        self.root = root                            # the machine's base body, e.g. 'machine/root'
        self.start = None
        self.met = {}                               # goal id -> time
        self.failed = {}
        self.disturbed = {}                         # goal id -> names moved so far
        self.origins = {}
        self.tipped_at = None                       # table angle when the machine went over

    def update(self, state):
        if self.start is None:
            self.start = state.time
            for goal in self.goals:
                if isinstance(goal, Undisturbed):
                    self.origins[goal.id] = {n: state.bodies[n].pose for n in goal.bodies}
                    self.disturbed[goal.id] = set()
        now = state.time - self.start
        machine = [n for n in state.bodies if n.startswith(MACHINE)]
        for goal in self.goals:
            if goal.id in self.met or goal.id in self.failed:
                continue
            if isinstance(goal, Upright):
                if tilt(state.bodies[self.root].pose.quaternion) > goal.max_tilt:
                    self.failed[goal.id] = now
            elif isinstance(goal, Undisturbed):
                for name, pose in self.origins[goal.id].items():
                    body = state.bodies[name].pose
                    if dist(body.position[:2], pose.position[:2]) > goal.shift or \
                            tilt(body.quaternion) > goal.lean:
                        self.disturbed[goal.id].add(name)
            elif isinstance(goal, TiltHold):
                table = state.bodies[goal.table].pose.quaternion
                angle = tilt(table)
                lean = between(state.bodies[self.root].pose.quaternion, table)
                if lean > goal.tipped:
                    self.failed[goal.id] = now
                    self.tipped_at = self.tipped_at or angle
                elif angle >= goal.angle and lean <= goal.lean:
                    self.met[goal.id] = now
            elif (goal.after is None or goal.after in self.met) and goal.check(machine, state):
                self.met[goal.id] = now

    def results(self, finished=False):
        out = []
        for goal in self.goals:
            if isinstance(goal, Upright):
                if goal.id in self.failed:
                    out.append(Result(goal.id, goal.label, 'failed', self.failed[goal.id],
                                      f'tipped past {goal.max_tilt:g} deg'))
                else:
                    out.append(Result(goal.id, goal.label, 'kept'))
            elif isinstance(goal, Undisturbed):
                moved = len(self.disturbed.get(goal.id, ()))
                total = len(goal.bodies)
                out.append(Result(goal.id, goal.label, 'failed' if moved else 'kept', None,
                                  f'{moved} of {total} moved'))
            elif isinstance(goal, TiltHold) and goal.id in self.failed:
                out.append(Result(goal.id, goal.label, 'missed', self.failed[goal.id],
                                  f'tipped over at {self.tipped_at:.0f} deg'))
            elif goal.id in self.met:
                time = self.met[goal.id]
                detail = ''
                since = getattr(goal, 'since', None)
                if since is not None and since in self.met:
                    detail = f'{time - self.met[since]:.1f} s after {self._label(since).lower()}'
                out.append(Result(goal.id, goal.label, 'met', time, detail))
            else:
                out.append(Result(goal.id, goal.label, 'missed' if finished else 'open'))
        return tuple(out)

    def _label(self, goal_id):
        return next(g.label for g in self.goals if g.id == goal_id)
