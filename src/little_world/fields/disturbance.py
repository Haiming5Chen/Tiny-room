"""Things that happen to a run partway through: a shove, a part moved, a camera that fails, a
motor that weakens (ADR 0030, 0038, 0058).

ADR 0024 varies the conditions a run starts in. A lab also does things to a robot while it
works: someone bumps the cart, a part is moved after the robot looked, a camera's stream
stops or goes dark. A disturbance says what happens and when - so many seconds after a goal
is met, or after the start - and a `Disturbing` applies it to a running world through the
adapter (`push`, `shift`, `weaken`) or to the field's camera (`fail`) and notes what it did.
Standard library only.
"""
from dataclasses import dataclass
from math import atan2, cos, radians, sin

KINDS = ('push', 'move', 'camera', 'motor')
FAULTS = ('freeze', 'dark')   # a camera that keeps sending its last picture; one whose pictures have no depth
SETTLED = 1.0   # s after a push ends, when how far it moved the machine is read
STILL = .01     # m/s: below this the machine's base counts as standing still
# A motor run hot (ADR 0058): its winding's resistance rises with its temperature, so at the same
# voltage it draws less current at stall and makes less torque, at the same free speed.
COPPER = .00393     # 1/K: annealed copper's temperature coefficient of resistance at 20 C
HOT = 50.           # K a drive motor's winding is taken to have warmed: assumed, Pololu gives none
LEFT = 'gearmotor_37_1_output_shaft_motor'   # the kit cart's left drive motor (+y of its heading)


def hot(kelvin=HOT):
    """The share of its stall torque a motor keeps with its winding `kelvin` above 20 C."""
    return 1 / (1 + COPPER * kelvin)


@dataclass(frozen=True)
class Disturbance:
    """One thing that happens to a run. A push acts on the machine's base: `impulse`
    newton-seconds, horizontal, spread over `seconds`, toward `toward` degrees from the
    machine's heading (anticlockwise: 90 pushes it to its left). A move shifts a loose
    field part, such as the Fetch cube, by `offset` metres in plan and turns it `turn`
    degrees about the vertical. `camera` fails the field's camera at the same moment -
    'freeze' or 'dark' (ADR 0038) - and a 'camera' disturbance does only that."""
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
    turn: float = 0.
    camera: str = ''                 # '', or one of FAULTS: the field's camera fails as it happens
    motor: str = ''                  # a 'motor' disturbance: the machine's motor it weakens
    torque: float = 1.               # the share of its stall torque it keeps
    speed: float = 1.                # the share of its free speed it keeps

    def __post_init__(self):
        object.__setattr__(self, 'offset', tuple(float(v) for v in self.offset))
        if self.kind not in KINDS:
            raise ValueError(f'a disturbance is one of {KINDS}, not {self.kind!r}')
        if self.delay < 0 or self.still < 0 or self.seconds <= 0 or self.impulse < 0 or len(self.offset) != 2:
            raise ValueError('a disturbance waits a while, lasts a while and pushes forwards')
        if self.kind == 'push' and not self.impulse:
            raise ValueError('a push needs an impulse')
        if self.kind == 'move' and not (self.part and (any(self.offset) or self.turn)):
            raise ValueError('a move needs a part and an offset or a turn')
        if self.camera and self.camera not in FAULTS:
            raise ValueError(f'a camera fails in one of {FAULTS}, not {self.camera!r}')
        if self.kind == 'camera' and not self.camera:
            raise ValueError('a camera disturbance needs a fault')
        if not (0 < self.torque <= 1 and 0 < self.speed <= 1):
            raise ValueError('a weakened motor keeps 0 to 1 of its torque and speed')
        if self.kind == 'motor' and not (self.motor and (self.torque < 1 or self.speed < 1)):
            raise ValueError('a motor disturbance needs a motor and less torque or speed')

    def describe(self):
        when = [f'after "{self.after}"' if self.after else 'from the start']
        if self.still:
            when.append(f'once still for {self.still:g} s')
        if self.delay:
            when.append(f'{self.delay:g} s later')
        fault = {'freeze': 'the camera frozen on its last picture', 'dark': 'the camera dark'}.get(self.camera, '')
        if self.kind == 'push':
            return (f'{self.impulse:g} N s over {self.seconds:g} s, {self.toward:g} deg left of its heading, '
                    + ', '.join(when) + (f'; {fault}' if fault else ''))
        if self.kind == 'camera':
            return fault + ', ' + ', '.join(when)
        if self.kind == 'motor':
            name = 'the left drive motor' if self.motor == LEFT else self.motor
            kept = [f'{100 * self.torque:.0f} % of its torque'] + ([f'{100 * self.speed:.0f} % of its speed'] if self.speed < 1 else [])
            return f'{name} at ' + ' and '.join(kept) + ', ' + ', '.join(when)
        return (f'{self.part.split("/")[-1]} moved {100 * self.offset[0]:+.1f} cm, {100 * self.offset[1]:+.1f} cm'
                + (f', turned {self.turn:+g} deg' if self.turn else '') + ', ' + ', '.join(when)
                + (f'; {fault} just before' if fault else ''))


def _yaw(quaternion):
    w, x, y, z = quaternion
    return atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


class Disturbing:
    """Applies one disturbance during a run: call `tick` after every step with the time since
    the goals' clock started and the goals met so far (`GoalTracker.met`). `note` says what
    happened, and for a push how far it moved the machine's base."""

    def __init__(self, disturbance, root, camera=None):
        self.disturbance = disturbance
        self.root = root            # the machine's base body, e.g. 'machine/root'
        self.camera = camera        # the field's camera, something with `fail(fault)`, for a camera fault
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
            if d.camera:
                # The camera fails first: its last picture is of the world before anything else
                # happens now (ADR 0038). No camera to fail: nothing happens to one.
                if self.camera is not None:
                    self.camera.fail(d.camera)
                if d.kind == 'camera':
                    self.done = True
                    return
            if d.kind == 'move':
                backend.shift(d.part, d.offset, d.turn)
                self.done = True
                return
            if d.kind == 'motor':
                backend.weaken(self.root.split('/')[0] + '/' + d.motor, d.torque, d.speed)
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
        if d.camera and self.camera is None:
            text += ', with no camera to fail'
        if self.moved is not None:
            text += f', the base went {100 * self.moved:.1f} cm the way it was pushed'
        return text


def _push(label, after, impulse, **more):
    return Disturbance(label, 'push', after=after, impulse=impulse, toward=90., seconds=.1, **more)


# What each field can have done to it, measured in ADR 0030. Fetch: once the cart has stopped
# at the table (stood still 0.2 s) a shove to its left, or the cube moved sideways (+Y, the
# cart's left as it faces the table) - then, or 2 s later, when a cart that looks has looked
# and is bringing its jaws over the cube (ADR 0032); or, then, the table's camera frozen as the
# cube is moved, or dark (ADR 0038). Sprint: a shove to its left a second past the start line.
DEFAULTS = {
    'fetch': (_push('shoved 4 N s at the table', 'reached', 4., still=.2, delay=.1),
              _push('shoved 6 N s at the table', 'reached', 6., still=.2, delay=.1),
              Disturbance('cube moved 3 cm sideways', 'move', after='reached', still=.2, delay=.1,
                          part='objects/fetch_cube', offset=(0., .03)),
              Disturbance('cube moved 5 cm sideways', 'move', after='reached', still=.2, delay=.1,
                          part='objects/fetch_cube', offset=(0., .05)),
              Disturbance('cube moved 5 cm sideways, 2 s later', 'move', after='reached', still=.2, delay=2.1,
                          part='objects/fetch_cube', offset=(0., .05)),
              Disturbance('camera frozen as the cube is moved 5 cm', 'move', after='reached', still=.2, delay=.1,
                          part='objects/fetch_cube', offset=(0., .05), camera='freeze'),
              Disturbance('camera dark at the table', 'camera', after='reached', still=.2, delay=.1, camera='dark')),
    'sprint': (_push('shoved 4 N s after the start', 'start', 4., delay=1.),
               _push('shoved 8 N s after the start', 'start', 8., delay=1.)),
}
# A motor run hot from the start (ADR 0058), apart from each field's disturbances above, which come
# once a goal is met: the kit cart's left drive motor, its winding 50 K over 20 C.
WEAK = {field: (Disturbance('left motor 50 K hot', 'motor', motor=LEFT, torque=hot()),) for field in ('sprint', 'fetch')}

