"""What a test driver can read off the machine: ideal sensors over MuJoCo state (ADR 0012).

Everything here is state the physics has already computed - body pose and velocity,
joint velocity, actuator force, contacts. Nothing is estimated for display. Forward
is the machine base's +X axis, the direction the drive assist drives it.
"""
from math import acos, atan2, degrees, pi
import mujoco as mj
import numpy as np
from little_world.core.component import Body, Motor
from .run_log import DriveSample, MotorSample

SATURATED = .98   # delivering at least this share of what is available counts as at the limit
UPWARD = .7       # a contact whose normal is within 45 degrees of vertical holds the machine up


def display_name(body_name):
    """'objects/pickup_stand' -> 'pickup stand'."""
    return body_name.rsplit('/', 1)[-1].replace('_', ' ').strip()


class DriveTelemetry:
    def __init__(self, backend, blueprint, drive, prefix='machine/'):
        m = backend.model
        self.backend = backend
        motors = {c.id: c for c in blueprint.components if isinstance(c, Motor)}
        roots = [b for b in blueprint.components if isinstance(b, Body) and b.parent is None]
        free = [b for b in roots if b.dynamic] or roots
        if drive.channels:
            self.root = drive.channels[0][5]
        else:
            self.root = m.body(prefix + free[0].id).id if free else -1
        per_side = {}
        for *_, side, _, _ in drive.channels:
            per_side[side] = per_side.get(side, 0) + 1
        seen = {}
        self.channels = []
        for name, dof, limit, radius, side, _, lateral in drive.channels:
            label = ('left', 'right')[side] if side in (0, 1) else f'side {side}'
            seen[side] = seen.get(side, 0) + 1
            if per_side[side] > 1:
                label += f' {seen[side]}'
            profile = motors[name[len(prefix):]].profile
            self.channels.append((label, m.actuator(name).id, dof, limit, radius, profile, lateral))
        self.assist = min((settings.max_speed for settings in drive.groups), default=None)
        self._machine = np.array([m.body(i).name.startswith(prefix) for i in range(m.nbody)])
        # Only a free machine can tip; a base bolted to the world has no tip margin.
        self._free = self.root >= 0 and any(
            m.jnt_type[m.body_jntadr[self.root] + k] == mj.mjtJoint.mjJNT_FREE
            for k in range(m.body_jntnum[self.root]))
        self._names = [display_name(m.body(i).name) for i in range(m.nbody)]

    def sample(self):
        m, d = self.backend.model, self.backend.data
        if self.root < 0:
            return DriveSample(float(d.time), (0., 0., 0.), 0., 0.)
        axes = d.xmat[self.root].reshape(3, 3)
        velocity = np.zeros(6)
        mj.mj_objectVelocity(m, d, mj.mjtObj.mjOBJ_BODY, self.root, velocity, 1)
        tilt = degrees(acos(max(-1., min(1., float(axes[2, 2])))))
        # Position and speed of the whole machine's centre of mass: a base whose origin
        # is off-centre (a chassis rail) would otherwise travel while turning in place.
        centre = d.subtree_com[self.root]
        world = np.zeros(6)
        mj.mj_objectVelocity(m, d, mj.mjtObj.mjOBJ_BODY, self.root, world, 0)
        moving = world[3:] + np.cross(world[:3], centre - d.xpos[self.root])
        forward = float(moving @ axes[:, 0])
        motors = []
        for label, actuator, dof, limit, radius, profile, lateral in self.channels:
            speed = float(d.qvel[dof])
            # As the drive assist sees it: the floor passes under a wheel at the base's
            # forward speed less its yaw rate times the wheel's sideways offset.
            ground = float(velocity[3] - velocity[2] * lateral)
            torque = float(d.actuator_force[actuator])
            if profile is None:
                available = limit
            else:
                available = abs(profile.constrain(limit if torque >= 0 else -limit, speed, limit))
            saturated = available > 0 and abs(torque) >= SATURATED * available
            motors.append(MotorSample(label, speed * 60 / (2 * pi),
                                      None if profile is None else profile.no_load_rpm,
                                      torque, available, saturated,
                                      abs(speed * radius) - abs(ground)))
        return DriveSample(float(d.time), tuple(float(v) for v in centre), forward, tilt, tuple(motors),
                           self.margin(centre))

    @property
    def anchored(self):
        """The machine is bolted to the world: an arm on a pedestal, not a vehicle."""
        return not self._free

    def support(self):
        """Contact points, over the floor plane, where the machine is held up from below."""
        m, d = self.backend.model, self.backend.data
        points = []
        for i in range(d.ncon):
            contact = d.contact[i]
            if contact.dist > 0 or abs(float(contact.frame[2])) < UPWARD:
                continue
            a, b = int(m.geom_bodyid[contact.geom1]), int(m.geom_bodyid[contact.geom2])
            if self._machine[a] != self._machine[b]:
                points.append((float(contact.pos[0]), float(contact.pos[1])))
        return points

    def margin(self, centre):
        """Static tip margin: how far the centre of mass is inside the polygon of the
        machine's supporting contacts, in metres; negative outside; None off the ground.
        It ignores acceleration, so hard braking can tip a machine with margin left."""
        if self.root < 0 or not self._free:
            return None
        points = self.support()
        if not points:
            return None
        from little_world.construction.structure import area, hull, margin
        polygon = hull([(round(x, 5), round(y, 5)) for x, y in points])
        if len(polygon) < 3 or area(polygon) < 1e-4:
            return None     # on one wheel or an edge: no stance to measure
        return margin(polygon, (float(centre[0]), float(centre[1])))

    def centre(self):
        """The machine's centre of mass, where the chase view looks."""
        return self.backend.data.subtree_com[self.root] if self.root >= 0 else np.zeros(3)

    def heading(self):
        """Degrees of the machine's forward axis over the floor, anticlockwise from +X."""
        if self.root < 0:
            return 0.
        axes = self.backend.data.xmat[self.root].reshape(3, 3)
        return degrees(atan2(float(axes[1, 0]), float(axes[0, 0])))

    def speed_limit(self):
        """(top speed m/s, what sets it, what the motors alone could reach or None).

        The drive assist caps the wheel speed it asks for; a sourced motor cannot turn
        faster than its no-load speed. Whichever is lower is what the driver meets."""
        motors = [profile.no_load_rpm * 2 * pi / 60 * radius
                  for _, _, _, _, radius, profile, _ in self.channels if profile is not None]
        alone = min(motors) if motors else None
        if self.assist is not None and (alone is None or self.assist <= alone):
            return self.assist, 'drive assist', alone
        return alone, 'motors', alone

    def touched(self):
        """Names of things outside the machine that it is touching now; not the floor."""
        m, d = self.backend.model, self.backend.data
        names = set()
        for i in range(d.ncon):
            contact = d.contact[i]
            if contact.dist > 0:
                continue
            a, b = int(m.geom_bodyid[contact.geom1]), int(m.geom_bodyid[contact.geom2])
            if self._machine[a] == self._machine[b]:
                continue
            name = self._names[b if self._machine[a] else a]
            if name and 'floor' not in name and name != 'world':
                names.add(name)
        return names
