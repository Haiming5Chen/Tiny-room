"""Moving an arm's tool rather than its joints (ADR 0016, 0045).

MuJoCo-bound, like the keyboard binding it drives: the Jacobian comes from the model.
A move is solved on a scratch copy of the state by damped least squares over the arm's
own joints - those between the machine and its tool - and handed to the position
controller as joint targets. The servos then move the arm, so torque limits, contact
and gravity still decide what actually happens; the solution is only where the joints
are asked to go.
"""
from math import degrees, radians
import mujoco as mj
import numpy as np
from little_world.construction.structure import modules
from little_world.programming.program import Block, Program, smoothstep

REACHED = .002      # m: a solution this close to the goal reaches it
SPEED = .05         # m/s: how fast a tool move travels its straight line (ADR 0045)
WAYPOINT = .002     # m: a move's line is solved this often along it, each point from the last
AIMED = .005        # m: an aimed pose whose tool settles further than this off its point is solved again
LEVEL = .15         # m of position error that one unit of tool-direction error weighs as
DAMPING = .01       # damped least squares: keeps steps finite near a stretched-out arm


class ToolMotion:
    """The tool point of a kit arm, and joint targets that put it somewhere else."""

    def __init__(self, backend, blueprint, control, entity='machine'):
        from little_world.core.component import Body
        self.backend, self.control = backend, control
        self.model, self.data = m, d = backend.model, backend.data
        self.prefix = entity + '/'
        found = modules(blueprint)
        tool = next((x for x in found if x.role == 'tool'), None)
        robot = next((b for b in blueprint.components if isinstance(b, Body) and b.robot_asset), None)
        servos = getattr(control, 'servos', {})
        units = getattr(control, 'units', {})

        def gripper(name):
            return units.get(name, '%' if servos[name][1] == 7 else 'deg') == '%'
        if tool is not None:
            self.tool_module = tool
            self.body = m.body(self.prefix + tool.root).id
            self.jaws = tuple(tool.actuators)
        elif robot is not None:
            # A registered robot model: its tool point is given, its jaws are its gripper servo.
            from little_world.assets.robot_models import metadata, tool as tool_of
            native = self.prefix + robot.id + '__robot_'
            meta = metadata(robot.robot_asset)
            name, _ = tool_of(robot.robot_asset)
            if name is None:
                last = meta.get('servo_joints', meta['joints'])[min(6, len(meta['joints']) - 1)]
                self.body = int(m.jnt_bodyid[m.joint(native + last).id])
            else:
                self.body = m.body(native + name).id
            self.tool_module = next(x for x in found if x.root == robot.id)
            self.jaws = tuple(n for n in servos if gripper(n))
        else:
            raise ValueError('Tool moves need an arm with a tool module, such as a gripper')
        chain, body = set(), self.body
        while body > 0:
            chain.add(body)
            body = int(m.body_parentid[body])
        # The arm's joints: every position-controlled actuator whose joint moves the tool
        # (a registered model's gripper servo drives its fingers, not the tool point).
        self.joints = []   # (action id, actuator, qpos address, dof address, lower, upper)
        joint_ids = []
        for spec in control.specs:
            for name in spec.actuators:
                if name not in control.channels:
                    continue
                if name in servos:
                    if gripper(name):
                        continue
                    joint = m.joint(backend.servo_joint_names[self.prefix + name]).id
                else:
                    joint = int(m.actuator(self.prefix + name).trnid[0])
                if int(m.jnt_bodyid[joint]) in chain:
                    low, high = (m.jnt_range[joint] if m.jnt_limited[joint] else (-np.pi, np.pi))
                    self.joints.append((spec.id, name, int(m.jnt_qposadr[joint]), int(m.jnt_dofadr[joint]),
                                        float(low), float(high)))
                    joint_ids.append(joint)
        if not self.joints:
            raise ValueError('No keyboard-bound joint moves the tool: bind the arm first')
        self.qpos = np.array([j[2] for j in self.joints])
        self.dofs = np.array([j[3] for j in self.joints])
        self.lower = np.array([j[4] for j in self.joints]) + 1e-3
        self.upper = np.array([j[5] for j in self.joints]) - 1e-3
        self.actions = tuple(dict.fromkeys(j[0] for j in self.joints))
        rotation = d.xmat[self.body].reshape(3, 3)
        if tool is not None:
            # The tool point: midway between a gripper's pads, fixed in the tool's own frame.
            pads = [m.body(self.prefix + b).id for b in tool.bodies if b.endswith('_pad')]
            centre = np.mean([d.xpos[p] for p in pads], axis=0) if pads else d.xpos[self.body]
            self.offset = rotation.T @ (centre - d.xpos[self.body])
            arm = next((x for x in found if x.role == 'arm' and x.root in set(blueprint_ancestors(found, tool))), None)
            base = arm.root if arm else found[0].root
        else:
            from little_world.assets.robot_models import tool as tool_of
            self.offset = np.array(tool_of(robot.robot_asset)[1])
            base = robot.id
        length = np.linalg.norm(self.offset)
        self.pointing = self.offset / length if length > 1e-3 else np.array((0., 0., 1.))
        # The arm's own base frame gives forward and left; up is always up.
        self.base = m.body(self.prefix + base).id
        self.scratch = mj.MjData(m)
        self.jp = np.zeros((3, m.nv))
        self.jr = np.zeros((3, m.nv))
        # The moving part of the arm: everything below its first joint's body.
        first = int(m.jnt_bodyid[joint_ids[0]])
        self.first_joint = joint_ids[0]
        self.moving = {b for b in range(m.nbody) if _below(m, b, first)}
        self.machine = {b for b in range(m.nbody) if m.body(b).name.startswith(self.prefix)}
        self.gliding = None     # a Glide under way (ADR 0045)
        self._drive = None      # where a held key has carried the tool's target, and its angle

    # -- reading the tool --------------------------------------------------------------

    def targets(self):
        """The arm's joint targets now, radians (the joint's angle where none is set)."""
        return np.array([self.control.targets.get(name, float(self.data.qpos[q]))
                         for _, name, q, *_ in self.joints])

    def tool(self, data=None, angles=None):
        """(tool point, pointing direction) in the world; at `angles` if given."""
        d = self._pose(angles) if angles is not None else self.data if data is None else data
        rotation = d.xmat[self.body].reshape(3, 3)
        return d.xpos[self.body] + rotation @ self.offset, rotation @ self.pointing

    def frame(self):
        """Forward, left and up for jogging: the arm base's axes laid flat, and vertical."""
        rotation = self.data.xmat[self.base].reshape(3, 3)
        forward = rotation[:, 0] * (1, 1, 0)
        if np.linalg.norm(forward) < 1e-6:
            forward = np.array((1., 0., 0.))
        forward = forward / np.linalg.norm(forward)
        return forward, np.cross((0., 0., 1.), forward), np.array((0., 0., 1.))

    def _pose(self, angles):
        d = self.scratch
        d.qpos[:] = self.data.qpos
        if angles is not None:
            d.qpos[self.qpos] = angles
        mj.mj_kinematics(self.model, d)
        mj.mj_comPos(self.model, d)
        return d

    # -- solving -----------------------------------------------------------------------

    def _residual(self, q, goal, hold):
        """(residual vector, Jacobian) at joint angles q: position, then tool direction."""
        d = self._pose(q)
        point, pointing = self.tool(d)
        mj.mj_jac(self.model, d, self.jp, self.jr, point, self.body)
        rows, residual = [self.jp[:, self.dofs]], [goal - point]
        if hold is not None:
            # d(pointing_z)/dq = (joint axis x pointing)_z for each joint
            rows.append(LEVEL * np.cross(self.jr[:, self.dofs].T, pointing)[:, 2][None, :])
            residual.append([LEVEL * (hold - pointing[2])])
        return np.concatenate(residual), np.vstack(rows)

    def _descend(self, goal, q, hold, iterations=150):
        """Levenberg-Marquardt within the joint limits: damped least squares whose damping
        grows when a step makes things worse, and shrinks when it helps."""
        q = np.clip(q, self.lower, self.upper)
        residual, jacobian = self._residual(q, goal, hold)
        cost, damping = residual @ residual, DAMPING
        for _ in range(iterations):
            if cost < 1e-10:
                break
            a, b = jacobian, residual
            step = a.T @ np.linalg.solve(a @ a.T + damping ** 2 * np.eye(len(b)), b)
            largest = np.max(np.abs(step))
            if largest > .3:
                step *= .3 / largest
            trial = np.clip(q + step, self.lower, self.upper)
            r, j = self._residual(trial, goal, hold)
            if r @ r < cost:
                q, residual, jacobian, cost = trial, r, j, r @ r
                damping = max(DAMPING / 10, damping / 2)
            else:
                damping *= 4
                if damping > 10:
                    break
        return q, cost

    def _seeds(self, goal, seed):
        """Where to start: the given angles; the same with a vertical first joint turned to
        face the goal; and each with the other joints bent, because a stretched-out arm is
        singular and a solver started there cannot find which way to fold."""
        first = [seed]
        d = self._pose(seed)
        joint = self.first_joint
        axis = d.xaxis[joint]
        if abs(axis[2]) > .99:
            point, _ = self.tool(d)
            anchor = d.xanchor[joint]
            turn = (np.arctan2(goal[1] - anchor[1], goal[0] - anchor[0]) -
                    np.arctan2(point[1] - anchor[1], point[0] - anchor[0])) * np.sign(axis[2])
            turned = seed.copy()
            turned[0] += (turn + np.pi) % (2 * np.pi) - np.pi
            first.append(turned)
        out = []
        for s in first:
            out.append(s)
            for bend in (.6, -.6):
                bent = s.copy()
                bent[1:] += bend * np.array([(-1) ** i for i in range(len(bent) - 1)])
                out.append(bent)
        return out

    def solve(self, goal, seed=None, hold=None):
        """Joint angles (radians) putting the tool point at `goal`, holding the vertical
        component of the tool's pointing direction at `hold` if given, within the joint
        limits. Returns (angles, distance left to the goal in metres); an angle that could
        not be held counts as distance too, weighted by LEVEL."""
        goal = np.asarray(goal, dtype=float)
        seed = self.targets() if seed is None else np.array(seed, dtype=float)
        best, best_cost = seed, float('inf')
        for start in self._seeds(goal, np.clip(seed, self.lower, self.upper)):
            q, cost = self._descend(goal, start, hold)
            if cost < best_cost - 1e-12:
                best, best_cost = q, cost
            if best_cost < 1e-10:
                break
        return best, float(np.sqrt(best_cost))

    def self_collision(self, angles, depth=.001):
        """True when the arm at these joint angles would sink more than `depth` into the
        rest of its own machine - a forearm resting on the chassis it is mounted on.
        The solver does not see collisions; waypoints are checked with this after."""
        d = self._pose(angles)
        mj.mj_collision(self.model, d)
        bodies = self.model.geom_bodyid
        for i in range(d.ncon):
            c = d.contact[i]
            if c.dist > -depth:
                continue
            a, b = int(bodies[c.geom1]), int(bodies[c.geom2])
            if a in self.machine and b in self.machine and (a in self.moving) != (b in self.moving):
                return True
        return False

    def pose(self, angles):
        """Joint angles as a program pose: ((action id, (degrees, ...)), ...)."""
        by_action = {}
        for (action, *_), value in zip(self.joints, angles):
            by_action.setdefault(action, []).append(round(degrees(float(value)), 3))
        return tuple((action, tuple(values)) for action, values in by_action.items())

    def angles(self, pose):
        """A program pose as this arm's joint angles, radians; joints it leaves out keep
        their targets."""
        given = {action: list(values) for action, values in pose}
        out, seen = self.targets(), {}
        for i, (action, *_) in enumerate(self.joints):
            k = seen.get(action, 0)
            if k < len(given.get(action, ())):
                out[i] = radians(given[action][k])
            seen[action] = k + 1
        return out

    def aim(self, point, pose, tolerance=AIMED):
        """For a pose aimed at a world point (ADR 0025): None when the tool is within
        `tolerance` of it, else the pose that puts it there from where the machine stands now
        - its base may have rocked onto another caster, or stopped off its mark, since the
        pose was solved - keeping the tool pointed as the pose points it. False when the
        point is out of reach from here: the pose stands, and a runner that moved the point
        to where a camera saw its object can say so (ADR 0035)."""
        now, _ = self.tool()
        if np.linalg.norm(np.asarray(point, dtype=float) - now) <= tolerance:
            return None
        planned = self.angles(pose)
        _, pointing = self.tool(angles=planned)
        angles, short = self.solve(point, planned, float(pointing[2]))
        return self.pose(angles) if short <= tolerance / 2 else False

    # -- moving ------------------------------------------------------------------------

    def jog(self, forward=0., left=0., up=0., hold_angle=True):
        """Move the tool's target by metres along the arm's forward, left and up.
        Returns the distance it falls short by; the targets change only if it reaches."""
        self.stop()
        start = self.targets()
        point, pointing = self.tool(angles=start)
        f, l, u = self.frame()
        goal = point + forward * f + left * l + up * u
        angles, short = self.solve(goal, start, pointing[2] if hold_angle else None)
        if short <= REACHED:
            for (_, name, *_), value in zip(self.joints, angles):
                self.control.targets[name] = float(value)
        return short

    def teach(self):
        """The arm's current joint targets as a pose - where a move under way is going."""
        return self.pose(self.destination())

    # -- moving along the line (ADR 0045) ----------------------------------------------

    def line(self, start, goal, angles, hold):
        """Joint angles for points every WAYPOINT from `start` to `goal`, each solved from the
        one before, so the arm keeps one way of bending all along. A point the last cannot
        reach - leaving a stretched-out, singular arm - is solved from the joint angles that
        far between the start and the end's own solution. (angles, short): `short` is how far
        the worst point stays from the line; a line that leaves the reach, or crosses a pose
        the arm cannot hold the tool's angle through, is not taken."""
        start, goal = np.asarray(start, dtype=float), np.asarray(goal, dtype=float)
        steps = max(1, int(np.ceil(np.linalg.norm(goal - start) / WAYPOINT)))
        first = np.array(angles, dtype=float)
        end = None
        out, q, worst = [first], first, 0.
        for k in range(1, steps + 1):
            point = start + (goal - start) * k / steps
            trial, cost = self._descend(point, q, hold)
            if cost > REACHED ** 2:
                if end is None:
                    end, _ = self.solve(goal, first, hold)
                blend, blended = self._descend(point, first + (end - first) * k / steps, hold)
                if blended < cost:
                    trial, cost = blend, blended
            q = trial
            worst = max(worst, float(np.sqrt(cost)))
            out.append(q)
        return out, worst

    def glide(self, forward=0., left=0., up=0., hold_angle=True, speed=SPEED):
        """Move the tool's target by metres along the arm's forward, left and up, travelling
        the straight line at `speed` from rest to rest (`advance` hands it out step by step).
        Returns how far the line falls short; nothing moves unless all of it is reached."""
        start = self.targets()
        point, pointing = self.tool(angles=start)
        f, l, u = self.frame()
        goal = point + forward * f + left * l + up * u
        angles, short = self.line(point, goal, start, pointing[2] if hold_angle else None)
        if short <= REACHED:
            self.gliding = Glide(angles, float(np.linalg.norm(goal - point)) / speed)
            self._drive = None
        return short

    def drive(self, direction, dt, hold_angle=True, speed=SPEED):
        """While a key is held: carry the tool's target along `direction` (forward, left, up;
        any length, 0 to stop) at `speed`, solving each step from the last. Returns how far
        the step fell short - the arm at the edge of its reach, or unable to hold the tool's
        angle, stops there."""
        direction = np.asarray(direction, dtype=float)
        if not np.any(direction):
            self._drive = None
            return 0.
        self.gliding = None
        start = self.targets()
        if self._drive is None:
            point, pointing = self.tool(angles=start)
            self._drive = (point, pointing[2] if hold_angle else None)
        point, hold = self._drive
        f, l, u = self.frame()
        heading = direction[0] * f + direction[1] * l + direction[2] * u
        goal = point + heading / np.linalg.norm(heading) * speed * dt
        q, cost = self._descend(goal, start, hold)
        if np.sqrt(cost) > REACHED:
            return float(np.sqrt(cost))
        self._drive = (goal, hold)
        self._set(q)
        return 0.

    def advance(self, dt):
        """One step of a gliding move: the joint targets where the tool should be by now.
        False once there is nothing to move."""
        if self.gliding is None:
            return False
        self._set(self.gliding.at(dt))
        if self.gliding.done:
            self.gliding = None
        return True

    def destination(self):
        """The joint angles a move under way ends at; the targets when nothing moves."""
        return self.gliding.angles[-1].copy() if self.gliding is not None else self.targets()

    def stop(self):
        """Forget a move under way; the joints keep the targets they have."""
        self.gliding, self._drive = None, None

    def _set(self, angles):
        for (_, name, *_), value in zip(self.joints, angles):
            self.control.targets[name] = float(value)


class Glide:
    """The joint angles along a tool move's line, handed out as the tool travels it in
    `duration` seconds, smoothly from rest to rest."""

    def __init__(self, angles, duration):
        self.angles, self.duration, self.elapsed, self.done = angles, max(duration, 1e-9), 0., False

    def at(self, dt):
        self.elapsed += dt
        s = smoothstep(min(1., self.elapsed / self.duration)) * (len(self.angles) - 1)
        k = min(int(s), len(self.angles) - 2) if len(self.angles) > 1 else 0
        self.done = self.elapsed >= self.duration
        if len(self.angles) == 1:
            return self.angles[0]
        return self.angles[k] + (self.angles[k + 1] - self.angles[k]) * (s - k)


def _below(model, body, top):
    """Whether `body` is `top` or hangs below it in the model's tree."""
    while body > 0:
        if body == top:
            return True
        body = int(model.body_parentid[body])
    return False


def blueprint_ancestors(found, module):
    """Root bodies of a module and the modules it is mounted on."""
    by_root = {m.root: m for m in found}
    out, current = [], module
    while current is not None:
        out.append(current.root)
        current = by_root.get(current.parent)
    return out


def nearest_object(backend, point, prefix='machine/'):
    """The loose body, not part of the machine, closest to a point: what the tool is at."""
    m, d = backend.model, backend.data
    best, name = float('inf'), None
    for i in range(1, m.nbody):
        body = m.body(i).name
        if body.startswith(prefix) or m.body_weldid[i] == 0 or m.body_parentid[i] != 0:
            continue
        distance = float(np.linalg.norm(d.xpos[i] - point))
        if distance < best:
            best, name = distance, body
    return name


AT_OBJECT = .015    # m: an object this close to the tool point is already between the jaws


def pick_and_place(motion, jaws, place, target=None, clearance=.06, speed=40.):
    """A program that picks up the object at (or nearest) the tool and sets it down at
    `place` (x, y, height of the surface under it), each waypoint solved for this arm.
    `jaws` is the gripper's keyboard action: its positive key closes.

    The tool keeps the angle it has now wherever the arm can manage that; where it
    cannot (lifting straight up from a stretched-out reach), the lift also draws back
    towards the arm, and only then does the tool tilt."""
    backend = motion.backend
    start = motion.targets()
    tool, pointing = motion.tool(angles=start)
    target = target or nearest_object(backend, tool)
    if target is None:
        raise ValueError('Nothing to pick up near the tool')
    body = backend.model.body(target).id
    held = backend.data.xpos[body].copy()
    # The object keeps the offset from the tool point it has in the grip.
    at = held - tool if np.linalg.norm(held - tool) <= AT_OBJECT else np.zeros(3)
    grasp = held - at
    half = float(held[2] - _bottom(backend, body))
    down = np.array((place[0], place[1], place[2] + half + .01)) - at
    hold = float(pointing[2])
    _, _, up = motion.frame()
    radial = lambda point: (point - backend.data.xpos[motion.base]) * (1, 1, 0) / max(
        1e-9, np.linalg.norm((point - backend.data.xpos[motion.base])[:2]))
    poses, seed = {}, start

    def reach(label, candidates):
        nonlocal seed
        for angle in (hold, None):
            for point in candidates:
                angles, short = motion.solve(point, seed, angle)
                if short <= REACHED and not motion.self_collision(angles):
                    poses[label], seed = motion.pose(angles), angles
                    return
        raise ValueError(f'The arm cannot reach the {label} point: {100 * short:.1f} cm short')
    steps = []
    if np.linalg.norm(held - tool) > AT_OBJECT:
        reach('above', [grasp + clearance * up])
        reach('at', [grasp])
        steps += ['above', 'at']
    lift = clearance + .02
    reach('lift', [grasp + lift * up - back * radial(grasp) for back in (0., .02, .04, .06, .08)])
    reach('over', [down + lift * up])
    reach('down', [down])
    reach('retract', [down + clearance * up])
    pose = lambda label, pace: Block('pose', value=pace, duration=2., angles=poses[label])
    blocks = [Block('action', jaws, -1, .6)] if steps else []
    blocks += [pose('above', speed), pose('at', speed / 2)] if steps else []
    blocks += [Block('action', jaws, 1, 1.), Block('grasp', target, duration=.5),
               pose('lift', speed / 2), pose('over', speed), pose('down', speed / 2),
               Block('action', jaws, -1, .8), pose('retract', speed)]
    return Program(tuple(blocks))


PICK_FORWARD = .23      # m ahead of the drive axle where the tool meets an object: within
PLACE_FORWARD = .25     # the compact arm's reach at table and floor height, clear of the chassis
BACK_OFF = .25          # m to back away from the table before turning, so the arm clears it
DROP = .03              # m above the bin's floor the object is let go from
WATCH = 1.              # s a look at the object watches before it may end (ADR 0032)
LOOKING = 5.            # s before a look that has not seen the object hold still fails
KEEP_CLEAR = .01        # m a stop that follows its object keeps from what is fixed ahead of it (ADR 0035)
SEARCH_WIDE = .25       # m round the plan a look searches when the stop will follow what it sees:
                        # the Fetch table's half-width (the camera's own default is 12 cm)
SKIM = .005             # m: parts overlapping less than this in height only touch, as wheels the floor
SET_GAP = .002          # m over the surface an object's lowest corner is let go (ADR 0042)
JAWS_CLEAR = .005       # m the jaws keep over that surface as they set the object down
TILT_STEP = 5.          # degrees: jaw tilts tried over the place, from how they point
TILT_MOST = 60.         # degrees down: the steepest tilt tried
SQUEEZE = .02           # s the jaws keep closing once the object is felt held, before it is carried:
                        # their 1 s ramp ends just past the kit cube, holding it at about 0.5 N a pad,
                        # and tilted it then crept out (ADR 0042); 0.6 degrees more holds at about 1 N


FULL_CLOSE = 1.4        # s: the kit jaws' target from fully open (-12 deg) to fully closed (30 deg) at 30 deg/s


def squeezed(program, newtons, close=FULL_CLOSE):
    """A program whose jaws close as a servo in current-based position control does (FR-037):
    each close action held until the jaws' target is fully closed, `close` seconds at least, with
    a squeeze of `newtons` at each pad - its Goal Current - so the squeeze is the setting, not
    where the closing ramp ended (ADR 0042)."""
    from dataclasses import replace
    if not newtons > 0:
        raise ValueError('a squeeze is more than 0 N')
    return replace(program, blocks=tuple(replace(b, secondary=newtons, duration=max(b.duration, close))
                                         if b.kind == 'action' and b.value == 1 and b.duration >= .5 else
                                         replace(b, secondary=newtons) if b.kind == 'action' and b.value == 1 else b
                                         for b in program.blocks))


def at_base(base_now, base_plan, point):
    """A world point as it sits relative to the base now, if it sits relative to the base
    at `base_plan` as it does in the world: planar poses (x, y, yaw). A joint solution
    for the machine standing at `base_plan` is the solution for this point now."""
    x0, y0, yaw0 = base_plan
    x1, y1, yaw1 = base_now
    dx, dy = point[0] - x0, point[1] - y0
    c0, s0, c1, s1 = np.cos(-yaw0), np.sin(-yaw0), np.cos(yaw1), np.sin(yaw1)
    fx, fy = c0 * dx - s0 * dy, s0 * dx + c0 * dy
    return np.array((x1 + c1 * fx - s1 * fy, y1 + s1 * fx + c1 * fy, point[2]))


def fetch(motion, base, jaws, target, place, clearance=.06, speed=40., reach_in=0., look=False):
    """A program for a mobile manipulator: drive to the object, pick it up, back away,
    drive to `place` (x, y, height of the surface under it) and set it down. Each arm
    waypoint is solved for the machine standing where the program will have driven it,
    as it stands now - so plan it with the machine settled on the floor, not in its level
    design pose; the drive axle's midpoint comes to within 1 cm and 2 degrees of each stop.
    `reach_in` lets go that much short of `place`, on the side the machine comes from:
    a short arm reaching into a bin keeps its chassis off the bin's near wall. With `look`,
    a camera looks for the object once the machine has stopped at it, and the jaws are
    brought over where it was seen before they go down (ADR 0032)."""
    backend = motion.backend
    now = base.pose()
    body = backend.model.body(target).id
    held = backend.data.xpos[body].copy()
    half = float(held[2] - _bottom(backend, body))
    start = motion.targets()
    _, pointing = motion.tool(angles=start)
    hold = float(pointing[2])
    heading = float(np.arctan2(held[1] - now[1], held[0] - now[0]))
    ahead = np.array((np.cos(heading), np.sin(heading)))
    pick = (*(held[:2] - PICK_FORWARD * ahead), heading)
    retreat = (*(np.array(pick[:2]) - BACK_OFF * ahead), heading)
    goal = np.array((place[0], place[1], place[2] + half + DROP))
    towards = float(np.arctan2(goal[1] - retreat[1], goal[0] - retreat[0]))
    along = np.array((np.cos(towards), np.sin(towards)))
    goal[:2] -= reach_in * along
    drop = (*(goal[:2] - PLACE_FORWARD * along), towards)
    poses, points, seed = {}, {}, start

    def reach(label, stand, candidates):
        nonlocal seed
        blocked = False
        for angle in (hold, None):
            for point in candidates:
                angles, short = motion.solve(at_base(now, stand, point), seed, angle)
                if short <= REACHED:
                    if motion.self_collision(angles):
                        blocked = True
                        continue
                    poses[label], points[label], seed = motion.pose(angles), tuple(float(v) for v in point), angles
                    return
        if blocked:
            raise ValueError(f'The arm would hit its own machine reaching the {label} point')
        raise ValueError(f'The arm cannot reach the {label} point from where the base stops: {100 * short:.1f} cm short')
    up = np.array((0., 0., 1.))
    # The jaws close on the object's upper half - their lower edge level with its middle - so
    # its lower half hangs below them and reaches the place before they do (ADR 0042).
    reach('above', pick, [held + clearance * up])
    reach('at', pick, [held])
    jaws_low = _jaws_low(motion, seed)
    grasp = held + ((motion.tool(angles=seed)[0][2] - jaws_low) if np.isfinite(jaws_low) else 0.) * up
    reach('above', pick, [grasp + clearance * up])
    reach('at', pick, [grasp])
    reach('lift', pick, [grasp + clearance * up])
    # Set down, not dropped (ADR 0042): the jaws carry the object level and, over the place,
    # tilt down by whatever angle - as they point, or in TILT_STEP steps to TILT_MOST - lets the
    # arm lower it furthest: until its lowest corner is SET_GAP over the place or the jaws are
    # JAWS_CLEAR over it. Kept level, the kit arm stops with the cube's lowest corner 4.9 cm over
    # the bin's floor: any lower and it hits its own cart.
    corners = _held_corners(motion, now, pick, body, motion.angles(poses['at']))
    best, tilt_now = None, float(np.degrees(np.arcsin(np.clip(-hold, -1., 1.))))
    for tilt in [tilt_now] + [t for t in np.arange(TILT_STEP, TILT_MOST + 1e-9, TILT_STEP) if t > tilt_now + 1e-6]:
        angle = hold if tilt == tilt_now else -float(np.sin(np.radians(tilt)))
        low = _lowest(motion, now, drop, goal[:2], float(place[2]), corners, angle, seed)
        if low is not None and (best is None or low[0] < best[0] - .001):
            best = (*low, angle)
    if best is None:
        # Nothing reaches down over the place from where the base stops: let go as low as the
        # arm reaches. A short arm reaching down past its own chassis may be stopped by it.
        lowest = [goal + rise * up for rise in (0., .02, .04, .06, .08)]
        reach('over', drop, [point + clearance * up for point in lowest])
        reach('down', drop, lowest)
        reach('retract', drop, [goal + clearance * up])
    else:
        _, down, angle = best
        for label, where in (('over', down + clearance * up), ('down', down), ('retract', down + clearance * up)):
            q, short = motion.solve(at_base(now, drop, where), seed, angle)
            if short > REACHED or motion.self_collision(q):
                raise ValueError(f'The arm cannot reach the {label} point from where the base stops')
            poses[label], points[label], seed = motion.pose(q), tuple(float(v) for v in where), q
    if look:
        # Looking, the open jaws come in short of the object, a clearance over its middle, so
        # that a camera beyond it sees all of its top past them (ADR 0032).
        seed = motion.angles(poses['above'])
        short = (_jaws_reach(motion) + _plan_radius(backend, body) + .01) * np.array((*ahead, 0.))
        reach('ready', pick, [held + clearance * up - short, held + 2 * clearance * up - short])
    # Every pose taken at a stop is aimed at its point in the field (ADR 0025): the base
    # stops within 1 cm of its mark and a cart rocks onto another caster as its arm moves,
    # so where the tool got to is checked and the pose solved again. 'above' is taken at
    # the start, far from its point, and is a pose only.
    pose = lambda label, pace, aimed=True: Block('pose', value=pace, duration=2., angles=poses[label],
                                                 point=points[label] if aimed else ())
    planned = tuple(float(v) for v in held)
    # Looking, the stops at the object follow where the camera saw it - sideways as far as
    # it moved, towards it no further than the machine keeps clear of what is ahead of the
    # stop, the table the object stands on (ADR 0035).
    follow = 0.
    if look:
        clear = _clear_ahead(backend, base, now, pick)
        follow = max(clear - KEEP_CLEAR, .001) if np.isfinite(clear) else 0.
    goto = lambda stop, at='': Block('goto', at, value=.01, duration=60., secondary=follow if at else 0.,
                                     point=(stop[0], stop[1], float(np.degrees(stop[2]))))
    at_object = target if look else ''
    # The arm takes its 'above' pose before the drive, so the open jaws arrive over the
    # object instead of pushing it off the table on the way in - or, looking, its 'ready'
    # pose short of it; once the camera has seen where the object is, the jaws come over it.
    # The first look is before the drive, so the machine stops where the object is (ADR
    # 0035); the look at the stop gives the jaws where it is now (ADR 0032, 0033).
    first = (Block('look', target, value=0., duration=LOOKING, secondary=SEARCH_WIDE, point=planned),) if look else ()
    seen = (Block('look', target, value=WATCH, duration=LOOKING, secondary=SEARCH_WIDE, point=planned),
            pose('above', speed)) if look else ()
    return Program((
        Block('action', jaws, -1, .6), *first, pose('ready' if look else 'above', speed, aimed=False),
        goto(pick, at_object), *seen, pose('at', speed / 2),
        Block('action', jaws, 1, 1.), Block('grasp', target, duration=.5), Block('action', jaws, 1, SQUEEZE),
        pose('lift', speed / 2),
        goto(retreat, at_object), goto(drop),
        pose('over', speed / 2), pose('down', speed / 2),
        Block('action', jaws, -1, .8),
        pose('retract', speed)))


def _clear_ahead(backend, base, now, stop):
    """How far a machine standing at `stop` (x, y, heading) could drive on along its heading
    before one of its parts meets a part fixed to the world - the table in front of it (m;
    inf when nothing is). Its parts are taken as they stand `now`, moved to the stop; a fixed
    part counts when it is wholly ahead of a machine part and overlaps it across the heading
    and in height (by more than SKIM, so the floor it stands on does not)."""
    m, d = backend.model, backend.data
    machine = m.body_rootid[base.left[0]]
    u = np.array((np.cos(stop[2]), np.sin(stop[2])))
    v = np.array((-u[1], u[0]))

    def extent(points):
        rel = points[:, :2] - np.array(stop[:2])
        return (*(lambda a: (a.min(), a.max()))(rel @ u), *(lambda a: (a.min(), a.max()))(rel @ v),
                points[:, 2].min(), points[:, 2].max())
    ours, fixed = [], []
    for g in range(m.ngeom):
        body = int(m.geom_bodyid[g])
        if m.body_rootid[body] == machine:
            ours.append(extent(np.array([at_base(stop, now, p) for p in _corners(m, d, g)])))
        elif m.body_weldid[body] == 0 and m.geom_type[g] != mj.mjtGeom.mjGEOM_PLANE:
            fixed.append(extent(_corners(m, d, g)))
    gap = np.inf
    for a0, a1, b0, b1, z0, z1 in ours:
        for c0, c1, e0, e1, w0, w1 in fixed:
            if c0 >= a1 and min(b1, e1) > max(b0, e0) and min(z1, w1) - max(z0, w0) > SKIM:
                gap = min(gap, c0 - a1)
    return float(gap)


def _corners(m, d, g):
    """A geom's box corners in the world, or its bounding box's for other shapes."""
    half = m.geom_size[g] if m.geom_type[g] == mj.mjtGeom.mjGEOM_BOX else np.full(3, m.geom_rbound[g])
    corners = np.array([(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]) * half
    return d.geom_xpos[g] + corners @ d.geom_xmat[g].reshape(3, 3).T


def _held_corners(motion, now, stand, body, angles):
    """The corners of `body` - an object the jaws close on with the arm at `angles`, the
    machine standing at `stand` - in the frame of the tool's body, where they stay while it is
    held (m)."""
    m, d = motion.model, motion.data
    world = np.array([at_base(now, stand, c) for g in range(m.ngeom) if m.geom_bodyid[g] == body
                      for c in _corners(m, d, g)])
    tool = motion._pose(angles)
    return (world - tool.xpos[motion.body]) @ tool.xmat[motion.body].reshape(3, 3)


def _lowest(motion, now, stand, xy, floor, corners, angle, seed, step=.0025):
    """How low the arm, the machine standing at `stand` and the jaws pointing `angle` (the
    vertical part of where they point), sets an object it holds - its corners `corners` in the
    tool's frame - over the point `xy` on a surface at height `floor`: the tool is stepped down
    from 12 cm over the surface until the next step would bring the object's lowest corner
    within SET_GAP of the surface, the jaws within JAWS_CLEAR of it, or the arm out of reach or
    into its own machine. Returns (that corner's height over the surface, the tool point there),
    or None if the arm cannot bring that corner as low as 8 cm over it."""
    def held_low(q):
        tool = motion._pose(q)
        return float(np.min((corners @ tool.xmat[motion.body].reshape(3, 3).T + tool.xpos[motion.body])[:, 2]))
    best, chain = None, seed
    for z in np.arange(floor + .12, floor - .05, -step):
        q, short = motion.solve(at_base(now, stand, np.array((*xy, z))), chain, angle)
        if short > REACHED or motion.self_collision(q):
            break
        low = held_low(q) - floor
        if low < SET_GAP or _jaws_low(motion, q) < floor + JAWS_CLEAR:
            break
        chain = q
        if low <= .08:
            best = (low, np.array((*xy, z)))
    return best


def _jaws_low(motion, angles):
    """The lowest point of the tool's visible parts with the arm at `angles` (m), as the
    machine stands now."""
    m = motion.model
    d = motion._pose(angles)
    return min((float(np.min(_corners(m, d, g)[:, 2])) for g in range(m.ngeom)
                if _below(m, int(m.geom_bodyid[g]), motion.body) and m.geom_rgba[g][3] > 0), default=np.inf)


def _jaws_reach(motion):
    """How far the tool's visible parts reach past its tool point, the way it points (m)."""
    m, d = motion.model, motion.data
    point, pointing = motion.tool()
    far = 0.
    for g in range(m.ngeom):
        if _below(m, int(m.geom_bodyid[g]), motion.body) and m.geom_rgba[g][3] > 0:
            far = max(far, float(np.max((_corners(m, d, g) - point) @ pointing)))
    return far


def _plan_radius(backend, body):
    """How far a body's geoms reach from its centre in plan (m)."""
    m, d = backend.model, backend.data
    centre = d.xpos[body][:2]
    return max((float(np.max(np.linalg.norm(_corners(m, d, g)[:, :2] - centre, axis=1)))
                for g in range(m.ngeom) if m.geom_bodyid[g] == body), default=0.)


def _bottom(backend, body):
    """Lowest point of a body's geoms (their bounding spheres, which for a box on its
    face overstate the depth; used only to set a release height)."""
    m, d = backend.model, backend.data
    geoms = [g for g in range(m.ngeom) if m.geom_bodyid[g] == body]
    if not geoms:
        return float(d.xpos[body][2])
    low = []
    for g in geoms:
        if m.geom_type[g] == mj.mjtGeom.mjGEOM_BOX:
            half = m.geom_size[g]
            corners = np.array([(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]) * half
            low.append(float(np.min((d.geom_xmat[g].reshape(3, 3) @ corners.T)[2]) + d.geom_xpos[g][2]))
        else:
            low.append(float(d.geom_xpos[g][2] - m.geom_rbound[g]))
    return min(low)
