"""How near a machine is to tipping over while it moves: the force-angle measure (ADR 0059, FR-005).

The static margin (ADR 0015, 0022) says how far the centre of mass is inside the support polygon;
braking hard, or swinging a loaded arm, tips a machine with margin left. Papadopoulos and Rey's
force-angle measure (ICRA 1996; Vehicle System Dynamics 33, 2000; restated by Appala and Ghosal,
IISc) takes the net force and moment on the machine other than its supports' - its weight less its
inertia's - and for each edge of the support polygon the angle between that force and the line from
the centre of mass to the edge: zero as the machine starts to tip over it, negative as it tips.

- Each edge is a tip axis a_i, the polygon's corners taken anticlockwise seen from above it.
- l_i = (I - a_i a_i^T)(p_{i+1} - c): from the centre of mass c to the axis, square to it.
- f_r = m g - m a_c and n_r = -dL/dt about c: the force and moment the supports must answer.
- f_i = (I - a_i a_i^T) f_r, n_i = (a_i a_i^T) n_r; the moment becomes a couple, one force through
  c: f_i* = f_i + (l^_i x n_i) / |l_i|.
- theta_i = +-acos(f^_i* . l^_i), positive while f_i* passes inside the axis.

The measure is min_i(theta_i) |f_r|; a driver reads the angle. Numpy only.
"""
from math import acos, degrees

import numpy as np


def ordered(points, up):
    """`points` (3-D, round a roughly flat support) as their convex hull, anticlockwise seen
    from the side `up` points to."""
    points = np.asarray(points, dtype=float)
    up = np.asarray(up, dtype=float) / np.linalg.norm(up)
    centre = points.mean(axis=0)
    u = np.cross(up, (1., 0., 0.) if abs(up[0]) < .9 else (0., 1., 0.))
    u /= np.linalg.norm(u)
    v = np.cross(up, u)
    flat = sorted({(round(float((p - centre) @ u), 6), round(float((p - centre) @ v), 6)): i
                   for i, p in enumerate(points)}.items())

    def cross(o, a, b):
        return (a[0][0] - o[0][0]) * (b[0][1] - o[0][1]) - (a[0][1] - o[0][1]) * (b[0][0] - o[0][0])
    lower, upper = [], []
    for p in flat:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(flat):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return points[[i for _, i in lower[:-1] + upper[:-1]]]


def force_angles(corners, centre, force, moment=(0., 0., 0.)):
    """The signed angle (radians) for each edge of the support polygon `corners` (3-D, anticlockwise
    seen from above, as `ordered` gives them): edge i runs from corner i to corner i + 1."""
    corners = np.asarray(corners, dtype=float)
    c = np.asarray(centre, dtype=float)
    force, moment = np.asarray(force, dtype=float), np.asarray(moment, dtype=float)
    angles = []
    for i in range(len(corners)):
        p, q = corners[i], corners[(i + 1) % len(corners)]
        a = (q - p) / np.linalg.norm(q - p)
        l = (q - c) - ((q - c) @ a) * a
        span = np.linalg.norm(l)
        lh = l / span
        f = force - (force @ a) * a + np.cross(lh, (moment @ a) * a) / span
        fh = f / np.linalg.norm(f)
        angle = acos(max(-1., min(1., float(fh @ lh))))
        # Inside the axis the force turns from l towards the polygon: anticlockwise about a.
        angles.append(angle if float(np.cross(lh, fh) @ a) >= 0 else -angle)
    return angles


def measure(corners, centre, force, moment=(0., 0., 0.)):
    """(the smallest angle in degrees, its edge, the force-angle measure min(theta) |f_r|)."""
    angles = force_angles(corners, centre, force, moment)
    i = int(np.argmin(angles))
    return degrees(angles[i]), i, angles[i] * float(np.linalg.norm(force))


UPWARD = .7     # a contact whose normal is within 45 degrees of upright holds the machine up
WINDOW = .05    # s over which accelerations are taken: as the handling watch's pushes are (ADR 0040)
CATCH = .01     # m: a part this near what the machine stands on would catch it before it tipped over -
                # a cart rocking onto a caster (6.5 mm up before ADR 0041) is not tipping over


class Watch:
    """A machine's force angle, step after step, from the solver: its mass and centre of mass, the
    acceleration of the one and the rate of change of its angular momentum about the other (both
    differenced over the last WINDOW of simulated time: a spinning wheel braked in a step makes an
    impulse a machine cannot tip on), and its support - the points of its own geoms that press into what
    holds it up (`ground`'s bodies if given, else anything under it within 45 degrees of upright). Call it
    after each step; it returns (angle in degrees, edge, measure) or None off the ground."""

    def __init__(self, backend, root, prefix='machine/', ground=()):
        m = backend.model
        self.backend, self.root = backend, root
        self.machine = np.array([m.body(i).name.startswith(prefix) for i in range(m.nbody)])
        self.ground = {i for i in range(m.nbody) if m.body(i).name in set(ground)}
        self.mass = float(m.body_subtreemass[root])
        # Its geoms that can touch anything: the ones that can hold it up.
        self.geoms = [g for g in range(m.ngeom) if self.machine[m.geom_bodyid[g]] and (m.geom_contype[g] or m.geom_conaffinity[g])]
        self.samples = []       # (time, the centre of mass's velocity, angular momentum about it)
        self.angle = self.edge = None
        self.last = None        # what it last said

    def support(self):
        """(points, up): the 3-D points the machine stands on - of its geoms, those within CATCH of
        what holds it up, so that a cart rocking onto a caster a few millimetres up is not taken
        for one tipping over - and the support's outward normal."""
        from .drive_telemetry import lowest_points
        m, d = self.backend.model, self.backend.data
        touching, normals = [], []
        for i in range(d.ncon):
            contact = d.contact[i]
            if contact.dist > 0:
                continue
            a, b = int(m.geom_bodyid[contact.geom1]), int(m.geom_bodyid[contact.geom2])
            if self.machine[a] == self.machine[b]:
                continue
            other = b if self.machine[a] else a
            into = np.array(contact.frame[:3], dtype=float) * (1. if self.machine[a] else -1.)   # into the support
            if (other not in self.ground) if self.ground else -into[2] < UPWARD:
                continue                # a field's own ground only, where it has one: not a rail beside it
            touching.append(np.array(contact.pos, dtype=float))
            normals.append(-into)
        if not normals:
            return [], None
        up = np.mean(normals, axis=0)
        up /= np.linalg.norm(up)
        level = float(np.mean([p @ up for p in touching]))      # the plane it stands on
        points = []
        for geom in self.geoms:
            for p in lowest_points(m, d, geom, -up, full=True):
                if float(np.asarray(p) @ up) - level <= CATCH:
                    points.append(p)
        return points, up

    def __call__(self):
        import mujoco as mj
        m, d = self.backend.model, self.backend.data
        mj.mj_subtreeVel(m, d)
        now = (float(d.time), d.subtree_linvel[self.root].copy(), d.subtree_angmom[self.root].copy())
        if self.samples and now[0] == self.samples[-1][0]:
            return self.last                        # paused: nothing new
        if self.samples and now[0] < self.samples[-1][0]:
            self.samples, self.last = [], None      # time went back: a reset world
        self.samples.append(now)
        while len(self.samples) > 2 and now[0] - self.samples[1][0] >= WINDOW:
            self.samples.pop(0)
        first = self.samples[0]
        if now[0] - first[0] < WINDOW - 1e-9:
            return None
        dt = now[0] - first[0]
        acceleration, turning = (now[1] - first[1]) / dt, (now[2] - first[2]) / dt
        points, up = self.support()
        if len(points) < 3:
            self.angle = self.edge = self.last = None
            return None
        corners = ordered(points, up)
        if len(corners) < 3:
            self.angle = self.edge = self.last = None
            return None
        force = self.mass * (np.array(m.opt.gravity) - acceleration)
        self.angle, self.edge, value = measure(corners, d.subtree_com[self.root], force, -turning)
        self.last = (self.angle, self.edge, value)
        return self.last
