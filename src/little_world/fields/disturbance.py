"""Things that happen to a run partway through: a shove, a part moved (ADR 0030).

ADR 0024 varies the conditions a run starts in. A lab also does things to a robot while it
works: someone bumps the cart, a part is moved after the robot looked. A disturbance says
what happens and when - so many seconds after a goal is met, or after the start - and a
`Disturbing` applies it to a running world through the adapter (`push`, `shift`) and notes
what it did. Standard library only.
"""
from dataclasses import dataclass
from math import atan2, cos, radians, sin

KINDS = ('push', 'move')
SETTLED = 1.0   # s after a push ends, when how far it moved the machine is read
STILL = .01     # m/s: below this the machine's base counts as standing still


@dataclass(frozen=True)
class Disturbance:
    """One thing that happens to a run. A push acts on the machine's base: `impulse`
    newton-seconds, horizontal, spread over `seconds`, toward `toward` degrees from the
    machine's heading (anticlockwise: 90 pushes it to its left). A move shifts a loose
    field part, such as the Fetch cube, by `offset` metres in plan."""
    label: str
    kind: str
    after: str = ''                # the goal whose being met starts the clock; '' the run's start
    still: float = 0.              # and then the machine has stood still this long (s)
    delay: float = 0.              # seconds after that
    impulse: float = 0.
    toward: float = 90.
    seconds: float = .1
    part: str = ''
    offset: tuple = (0., 0.)

    def __post_init__(self):
        object.__setattr__(self, 'offset', tuple(float(v) for v in self.offset))
        if self.kind not in KINDS:
            raise ValueError(f'a disturbance is one of {KINDS}, not {self.kind!r}')
        if self.delay < 0 or self.still < 0 or self.seconds <= 0 or self.impulse < 0 or len(self.offset) != 2:
            raise ValueError('a disturbance waits a while, lasts a while and pushes forwards')
        if self.kind == 'push' and not self.impulse:
            raise ValueError('a push needs an impulse')
        if self.kind == 'move' and not (self.part and any(self.offset)):
            raise ValueError('a move needs a part and an offset')

    def describe(self):
        when = [f'after "{self.after}"' if self.after else 'from the start']
        if self.still:
            when.append(f'once still for {self.still:g} s')
        if self.delay:
            when.append(f'{self.delay:g} s later')
        if self.kind == 'push':
            return (f'{self.impulse:g} N s over {self.seconds:g} s, {self.toward:g} deg left of its heading, '
                    + ', '.join(when))
        return (f'{self.part.split("/")[-1]} moved {100 * self.offset[0]:+.1f} cm, {100 * self.offset[1]:+.1f} cm, '
                + ', '.join(when))


def _yaw(quaternion):
    w, x, y, z = quaternion
    return atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


class Disturbing:
    """Applies one disturbance during a run: call `tick` after every step with the time since
    the goals' clock started and the goals met so far (`GoalTracker.met`). `note` says what
    happened, and for a push how far it moved the machine's base."""

    def __init__(self, disturbance, root):
        self.disturbance = disturbance
        self.root = root            # the machine's base body, e.g. 'machine/root'
        self.began = None           # time on the goals' clock when it happened
        self.ended = None
        self.start = None           # where the base was when the push began (x, y)
        self.way = None             # the push's direction in plan (unit x, y)
        self.moved = None           # metres the base had gone the way it was pushed, SETTLED s after
        self.since = None           # when the base last started standing still
        self.ready = None           # when the clock's conditions were all met
        self.done = False

    def tick(self, backend, state, elapsed, met):
        d = self.disturbance
        if self.done:
            return
        if self.began is None:
            if d.after and d.after not in met:
                return
            if elapsed < (met[d.after] if d.after else 0.):
                return
            if self.ready is None:
                if d.still:
                    speed = state.bodies[self.root].linear_velocity
                    if (speed[0] ** 2 + speed[1] ** 2) ** .5 > STILL:
                        self.since = None
                        return
                    self.since = elapsed if self.since is None else self.since
                    if elapsed - self.since < d.still:
                        return
                self.ready = elapsed
            if elapsed < self.ready + d.delay:
                return
            self.began = elapsed
            if d.kind == 'move':
                backend.shift(d.part, d.offset)
                self.done = True
                return
            pose = state.bodies[self.root].pose
            self.start = pose.position[:2]
            angle = _yaw(pose.quaternion) + radians(d.toward)
            self.way = (cos(angle), sin(angle))
            force = d.impulse / d.seconds
            backend.push(self.root, (force * self.way[0], force * self.way[1], 0.))
            return
        if self.ended is None:
            if elapsed >= self.began + d.seconds:
                backend.push(self.root, (0., 0., 0.))
                self.ended = elapsed
            return
        if elapsed >= self.ended + SETTLED:
            # Along the push only: a machine driving on carries on across it.
            x, y = state.bodies[self.root].pose.position[:2]
            self.moved = (x - self.start[0]) * self.way[0] + (y - self.start[1]) * self.way[1]
            self.done = True

    def note(self):
        d = self.disturbance
        if self.began is None:
            return f'{d.label}: never happened' + (f' ({d.after} not met)' if d.after else '')
        text = f'{d.label} at {self.began:.1f} s'
        if self.moved is not None:
            text += f', the base went {100 * self.moved:.1f} cm the way it was pushed'
        return text


def _push(label, after, impulse, **more):
    return Disturbance(label, 'push', after=after, impulse=impulse, toward=90., seconds=.1, **more)


# What each field can have done to it, measured in ADR 0030. Fetch: once the cart has stopped
# at the table (stood still 0.2 s) a shove to its left, or the cube moved sideways (+Y, the
# cart's left as it faces the table). Sprint: a shove to its left a second past the start line.
DEFAULTS = {
    'fetch': (_push('shoved 4 N s at the table', 'reached', 4., still=.2, delay=.1),
              _push('shoved 6 N s at the table', 'reached', 6., still=.2, delay=.1),
              Disturbance('cube moved 3 cm sideways', 'move', after='reached', still=.2, delay=.1,
                          part='objects/fetch_cube', offset=(0., .03)),
              Disturbance('cube moved 5 cm sideways', 'move', after='reached', still=.2, delay=.1,
                          part='objects/fetch_cube', offset=(0., .05))),
    'sprint': (_push('shoved 4 N s after the start', 'start', 4., delay=1.),
               _push('shoved 8 N s after the start', 'start', 8., delay=1.)),
}

