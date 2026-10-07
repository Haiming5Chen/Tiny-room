"""Moving an arm's tool rather than its joints (ADR 0016).

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
from little_world.programming.program import Block, Program

REACHED = .002      # m: a solution this close to the goal reaches it
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
        if tool is not None:
            self.tool_module = tool
            self.body = m.body(self.prefix + tool.root).id
            self.jaws = tuple(tool.actuators)
        elif robot is not None:
            # A registered robot model: its tool point is given, its jaws are its gripper servo.
            from little_world.assets.robot_models import TOOLS, metadata
            native = self.prefix + robot.id + '__robot_'
            meta = metadata(robot.robot_asset)
            name, _ = TOOLS.get(robot.robot_asset, (None, None))
            if name is None:
                last = meta.get('servo_joints', meta['joints'])[min(6, len(meta['joints']) - 1)]
                self.body = int(m.jnt_bodyid[m.joint(native + last).id])
            else:
                self.body = m.body(native + name).id
            self.tool_module = next(x for x in found if x.root == robot.id)
            self.jaws = tuple(n for n, (_, channel) in servos.items() if channel == 7)
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
                    if servos[name][1] == 7:
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
            from little_world.assets.robot_models import TOOLS
            self.offset = np.array(TOOLS.get(robot.robot_asset, (None, (0., 0., 0.)))[1])
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
        """The arm's current joint targets as a pose."""
        return self.pose(self.targets())


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
    reach('above', pick, [held + clearance * up])
    reach('at', pick, [held])
    reach('lift', pick, [held + clearance * up])
    # A short arm reaching down past its own chassis may be stopped by it: let go higher.
    lowest = [goal + rise * up for rise in (0., .02, .04, .06, .08)]
    reach('over', drop, [point + clearance * up for point in lowest])
    reach('down', drop, lowest)
    reach('retract', drop, [goal + clearance * up])
    if look:
        # Looking, the open jaws come in short of the object at the height they will stand
        # over it, so that a camera beyond it sees all of its top past them (ADR 0032).
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
        Block('action', jaws, 1, 1.), Block('grasp', target, duration=.5),
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
