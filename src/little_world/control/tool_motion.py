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
LEVEL = .15         # m of position error that one unit of tool-direction error weighs as
DAMPING = .01       # damped least squares: keeps steps finite near a stretched-out arm


class ToolMotion:
    """The tool point of a kit arm, and joint targets that put it somewhere else."""

    def __init__(self, backend, blueprint, control, entity='machine'):
        self.backend, self.control = backend, control
        self.model, self.data = m, d = backend.model, backend.data
        self.prefix = entity + '/'
        found = modules(blueprint)
        tool = next((x for x in found if x.role == 'tool'), None)
        if tool is None:
            raise ValueError('Tool moves need an arm with a tool module, such as a gripper')
        self.tool_module = tool
        self.body = m.body(self.prefix + tool.root).id
        chain, body = set(), self.body
        while body > 0:
            chain.add(body)
            body = int(m.body_parentid[body])
        # The arm's joints: every position-controlled actuator whose joint moves the tool.
        self.joints = []   # (action id, actuator, qpos address, dof address, lower, upper)
        for spec in control.specs:
            for name in spec.actuators:
                if name not in control.channels or name in getattr(control, 'servos', {}):
                    continue
                joint = int(m.actuator(self.prefix + name).trnid[0])
                if int(m.jnt_bodyid[joint]) in chain:
                    q, v, lo, hi, _ = control.channels[name]
                    self.joints.append((spec.id, name, q, v, lo, hi))
        if not self.joints:
            raise ValueError('No keyboard-bound joint moves the tool: bind the arm first')
        self.qpos = np.array([j[2] for j in self.joints])
        self.dofs = np.array([j[3] for j in self.joints])
        self.lower = np.array([j[4] for j in self.joints]) + 1e-3
        self.upper = np.array([j[5] for j in self.joints]) - 1e-3
        self.actions = tuple(dict.fromkeys(j[0] for j in self.joints))
        # The tool point: midway between a gripper's pads, fixed in the tool's own frame.
        pads = [m.body(self.prefix + b).id for b in tool.bodies if b.endswith('_pad')]
        rotation = d.xmat[self.body].reshape(3, 3)
        centre = np.mean([d.xpos[p] for p in pads], axis=0) if pads else d.xpos[self.body]
        self.offset = rotation.T @ (centre - d.xpos[self.body])
        length = np.linalg.norm(self.offset)
        self.pointing = self.offset / length if length > 1e-3 else np.array((1., 0., 0.))
        # The arm's own base frame gives forward and left; up is always up.
        arm = next((x for x in found if x.role == 'arm' and x.root in {b for b in blueprint_ancestors(found, tool)}), None)
        self.base = m.body(self.prefix + (arm.root if arm else found[0].root)).id
        self.scratch = mj.MjData(m)
        self.jp = np.zeros((3, m.nv))
        self.jr = np.zeros((3, m.nv))

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
        joint = int(self.model.actuator(self.prefix + self.joints[0][1]).trnid[0])
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

    def pose(self, angles):
        """Joint angles as a program pose: ((action id, (degrees, ...)), ...)."""
        by_action = {}
        for (action, *_), value in zip(self.joints, angles):
            by_action.setdefault(action, []).append(round(degrees(float(value)), 3))
        return tuple((action, tuple(values)) for action, values in by_action.items())

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
                if short <= REACHED:
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
