"""What a machine is made of, module by module, and how it stands (ADR 0015).

Standard library only. A module is a catalog part as it was inserted - its root body
and everything below it until the next module's root - so a mobile manipulator reads
as a base, two drives with their wheels, two supports, an arm and a tool rather than
as three hundred bodies. Mass comes from each body's geometry and material density,
exactly as the simulator derives it; a registered robot model's mass lives in its own
files, so it is reported as unknown here rather than guessed.

How it stands is found the way a rigid machine settles on a level floor: it rests on
its lowest points, and while its centre of mass is outside the polygon they make it
tips about the nearest edge of that polygon until another point meets the floor. The
same rocking on a tilted floor - gravity leaning off the floor's normal - finds the
slope each side can take before nothing catches it (ADR 0020).
"""
from dataclasses import dataclass
from math import acos, atan2, cos, degrees, pi, sin
from little_world.core.component import Body, Camera, Motor, RobotServo, Hinge
from .connections import rotate
from .docking import catalog_id, poses, subtree, world_bounds

ROLES = ('base', 'drive', 'wheel', 'support', 'arm', 'tool', 'sensor', 'mount', 'actuator',
         'structure', 'hardware', 'part')
VARIANT_ROLES = {
    'drive': 'drive', 'hw_gearmotor': 'actuator', 'hw_motor': 'actuator', 'hw_servo': 'actuator',
    'wheel': 'wheel', 'hw_tread': 'wheel', 'axle': 'wheel',
    'hw_caster': 'support', 'skid': 'support',
    'hw_arm': 'arm', 'hw_arm_compact': 'arm', 'hw_arm_long': 'arm', 'hw_wrist': 'arm',
    'real_robot': 'arm', 'ready_arm': 'arm', 'hinge': 'arm',
    'hw_gripper': 'tool', 'hw_gripper_compact': 'tool', 'hw_gripper_wide': 'tool',
    'ready_fork': 'tool', 'ready_scoop': 'tool', 'ready_tray': 'tool',
    'camera': 'sensor', 'mast': 'sensor', 'ready_camera': 'sensor',
    'hw_arm_deck': 'mount',
}
CATEGORY_ROLES = {'Hardware': 'hardware', 'Structure': 'structure', 'Housing': 'structure',
                  'Sensors': 'sensor', 'Driven parts': 'part'}
TOUCH = .0005       # m: a point this close to the floor carries load
TIPS_OVER = 45.     # degrees: rolled this far, a machine lies on parts not made to carry it
AIRBORNE = .005     # m: a design starting higher than this above the floor falls at the start
_DIRECTIONS = tuple((i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1) if (i, j, k) != (0, 0, 0))


@dataclass(frozen=True)
class Module:
    root: str                   # the module's root body
    item: str | None            # catalog id, or None for a part made in the editor
    title: str
    role: str
    parent: str | None          # root body of the module this one is mounted on
    depth: int
    bodies: tuple
    actuators: tuple            # Motor and RobotServo ids driving this module's joints
    keys: tuple                 # (label, positive key, negative key) of its keyboard controls
    mass: float | None          # kg; None when part of it is a registered robot model
    centre: tuple               # centre of mass at the design pose, machine frame


def body_mass(body, densities):
    """Mass of one body from its geometry and density, as the simulator computes it."""
    if body.robot_asset is not None:
        return None
    g = body.geometry
    if g.shape == 'box':
        volume = g.size[0] * g.size[1] * g.size[2]
    elif g.shape == 'cylinder':
        volume = pi * g.size[0] ** 2 * g.size[1]
    elif g.shape == 'capsule':
        volume = pi * g.size[0] ** 2 * g.size[1] + 4 / 3 * pi * g.size[0] ** 3
    else:
        volume = 4 / 3 * pi * g.size[0] ** 3
    return densities[body.material] * volume


def module_roots(blueprint):
    """Body id -> the root body of the module it belongs to."""
    bodies = {b.id: b for b in blueprint.components if isinstance(b, Body)}
    owner = {}

    def find(name):
        if name not in owner:
            b = bodies[name]
            root = b.parent is None or b.catalog_part is not None or catalog_id(b.id) is not None
            owner[name] = name if root else find(b.parent)
        return owner[name]
    for name in bodies:
        find(name)
    return owner


def modules(blueprint):
    """The machine's modules, depth first from its root(s)."""
    from little_world.assets.catalog import BY_ID
    bodies = [b for b in blueprint.components if isinstance(b, Body)]
    by_id = {b.id: b for b in bodies}
    owner = module_roots(blueprint)
    densities = {m.id: m.density for m in blueprint.materials}
    transforms = poses(blueprint)
    members = {}
    for b in bodies:
        members.setdefault(owner[b.id], []).append(b.id)
    joints = {c.id: c for c in blueprint.components if isinstance(c, Hinge)}
    actuators = {}
    for c in blueprint.components:
        body = joints[c.joint].body if isinstance(c, Motor) else c.body if isinstance(c, RobotServo) else None
        if body is not None:
            actuators.setdefault(owner[body], []).append(c.id)
    drive = {a for spec in blueprint.controllers if spec.kind == 'differential_torque' for a in spec.actuators}
    home = {a: root for root, ids in actuators.items() for a in ids}
    keys = {}
    for spec in blueprint.controllers:
        if spec.kind == 'keyboard_position' and spec.actuators and spec.actuators[0] in home:
            keys.setdefault(home[spec.actuators[0]], []).append((spec.label or spec.id, spec.positive_key, spec.negative_key))
    cameras = {owner[c.body] for c in blueprint.components if isinstance(c, Camera)}
    parent = {root: (owner[by_id[root].parent] if by_id[root].parent else None) for root in members}
    out = []

    def visit(root, depth):
        body = by_id[root]
        item_id = body.catalog_part if body.catalog_part in BY_ID else catalog_id(root)
        item = BY_ID.get(item_id)
        own = tuple(actuators.get(root, ()))
        if parent[root] is None:
            role = 'base'
        elif item is not None:
            role = VARIANT_ROLES.get(item.variant, CATEGORY_ROLES.get(item.category, 'part'))
            if role == 'actuator' and any(a in drive for a in own):
                role = 'drive'
        else:
            role = 'sensor' if root in cameras else 'part'
        masses = [(body_mass(by_id[n], densities), n) for n in members[root]]
        known = [(m, n) for m, n in masses if m is not None]
        total = sum(m for m, _ in known)
        centre = tuple(sum(m * transforms[n].position[i] for m, n in known) / total if total else
                       transforms[root].position[i] for i in range(3))
        title = item.title if item is not None else root.replace('_', ' ')
        out.append(Module(root, item_id if item is not None else None, title, role, parent[root], depth,
                          tuple(members[root]), own, tuple(keys.get(root, ())),
                          None if len(known) < len(masses) else total, centre))
        for child in sorted((r for r in members if parent[r] == root), key=lambda r: members[r][0]):
            visit(child, depth + 1)

    ordered = [b.id for b in bodies]
    for root in sorted((r for r in members if parent[r] is None), key=ordered.index):
        visit(root, 0)
    return tuple(out)


def centre_of_mass(blueprint):
    """(kg, (x, y, z)) of every body whose mass is known, at the design pose."""
    densities = {m.id: m.density for m in blueprint.materials}
    transforms = poses(blueprint)
    total, moment = 0., [0., 0., 0.]
    for b in blueprint.components:
        if isinstance(b, Body):
            m = body_mass(b, densities)
            if m:
                total += m
                for i in range(3):
                    moment[i] += m * transforms[b.id].position[i]
    return total, tuple(v / total for v in moment) if total else (0., 0., 0.)


def surface_points(body, transform):
    """Points of a body's outline that could meet a floor, in the machine frame: a box's
    corners, a cylinder's two rims (16 points each), a sphere in 26 directions. Round
    shapes are polygons whose flats sit within 2 % of their radius of the true surface."""
    g = body.geometry
    q, p = transform.quaternion, transform.position
    if g.shape == 'box':
        hx, hy, hz = (s / 2 for s in g.size)
        local = [(sx * hx, sy * hy, sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    elif g.shape in ('cylinder', 'capsule'):
        # A capsule's round ends within its radius of its straight part's: their rims, moved out.
        r, h = g.size[0], g.size[1] / 2 + (g.size[0] if g.shape == 'capsule' else 0.)
        local = [(r * cos(pi * k / 8), r * sin(pi * k / 8), end * h) for end in (-1, 1) for k in range(16)]
    else:
        r = g.size[0]
        local = [tuple(r * c / sum(v * v for v in d) ** .5 for c in d) for d in _DIRECTIONS]
    return [tuple(p[i] + v[i] for i in range(3)) for v in (rotate(q, l) for l in local)]


def hull(points):
    """Convex hull of 2-D points, anticlockwise (monotone chain)."""
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def area(polygon):
    """Area of a simple polygon (shoelace)."""
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1]))) / 2


def margin(polygon, point):
    """Signed distance from a point to a convex polygon's boundary: positive inside.
    A polygon of fewer than three corners supports nothing: the result is negative."""
    if len(polygon) < 3:
        if not polygon:
            return float('-inf')
        return -min(((point[0] - x) ** 2 + (point[1] - y) ** 2) ** .5 for x, y in polygon)
    best = float('inf')
    for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1]):
        dx, dy = x1 - x0, y1 - y0
        length = (dx * dx + dy * dy) ** .5
        if length < 1e-12:
            continue
        best = min(best, (dx * (point[1] - y0) - dy * (point[0] - x0)) / length)
    return best


@dataclass(frozen=True)
class Stance:
    """How a machine comes to rest on a level floor, with its joints as designed."""
    margin: float           # m from the centre of mass to the support polygon's nearest edge
    tilt: float             # degrees the machine settles away from its design attitude
    support: tuple          # the support polygon, in the floor plane's own 2-D frame
    centre: tuple           # the centre of mass, projected into that frame
    touching: tuple         # bodies that carry it
    tips_over: bool = False  # it rolls past TIPS_OVER, or onto nothing at all
    height: float = 0.      # m of the centre of mass above the floor it rests on
    # Static stability (ADR 0020): how far the floor could tilt, lowering each side of the
    # machine in turn, before its centre of mass passes over that edge of its supports -
    # ('forward', degrees), ('back', ...), ('left', ...), ('right', ...). A tilt-table angle.
    tips: tuple = ()

    def tip(self, side):
        return dict(self.tips).get(side)


def exit_distance(polygon, point, direction):
    """How far a point inside a convex (anticlockwise) polygon can move along a unit
    direction before it leaves it."""
    best = float('inf')
    for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1]):
        ex, ey = x1 - x0, y1 - y0
        length = (ex * ex + ey * ey) ** .5
        if length < 1e-12:
            continue
        nx, ny = ey / length, -ex / length               # outward, for an anticlockwise edge
        rate = direction[0] * nx + direction[1] * ny
        if rate > 1e-12:
            best = min(best, ((x0 - point[0]) * nx + (y0 - point[1]) * ny) / rate)
    return best


SIDES = (('forward', (1., 0., 0.)), ('back', (-1., 0., 0.)), ('left', (0., 1., 0.)), ('right', (0., -1., 0.)))


def _tips(points, centre, up):
    """Tilt angles, degrees, at which the machine rolls over as the floor under it is
    tilted, lowering each side in turn: the smallest slope at which rocking about its
    downhill edge finds no further point to catch it. A machine that rocks onto a caster
    has not tipped; with a single support polygon this is atan(reach / height), the
    static stability factor's angle."""
    out = []
    for side, direction in SIDES:
        along = _dot(direction, up)
        downhill = tuple(direction[i] - along * up[i] for i in range(3))
        norm = _dot(downhill, downhill) ** .5
        if norm < 1e-9:
            continue
        downhill = tuple(c / norm for c in downhill)
        lo, hi = 0., 89.
        if _rest(points, centre, up, downhill, hi)[0] == 'rests':
            continue
        for _ in range(14):
            mid = (lo + hi) / 2
            if _rest(points, centre, up, downhill, mid)[0] == 'rests':
                lo = mid
            else:
                hi = mid
        out.append((side, round((lo + hi) / 2, 2)))
    return tuple(out)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _plane(normal):
    """Two unit vectors spanning the plane perpendicular to `normal`."""
    helper = (1., 0., 0.) if abs(normal[0]) < .9 else (0., 1., 0.)
    u = (helper[1] * normal[2] - helper[2] * normal[1], helper[2] * normal[0] - helper[0] * normal[2],
         helper[0] * normal[1] - helper[1] * normal[0])
    length = _dot(u, u) ** .5
    u = tuple(c / length for c in u)
    v = (normal[1] * u[2] - normal[2] * u[1], normal[2] * u[0] - normal[0] * u[2], normal[0] * u[1] - normal[1] * u[0])
    return u, v


def _nearest_on_boundary(polygon, point):
    """The point of a polygon's boundary (or segment, or single point) nearest `point`."""
    if len(polygon) == 1:
        return polygon[0]
    best, found = float('inf'), polygon[0]
    edges = zip(polygon, polygon[1:] + polygon[:1]) if len(polygon) > 2 else [(polygon[0], polygon[1])]
    for (x0, y0), (x1, y1) in edges:
        dx, dy = x1 - x0, y1 - y0
        length = dx * dx + dy * dy
        t = 0. if length < 1e-18 else max(0., min(1., ((point[0] - x0) * dx + (point[1] - y0) * dy) / length))
        q = (x0 + t * dx, y0 + t * dy)
        d = (point[0] - q[0]) ** 2 + (point[1] - q[1]) ** 2
        if d < best:
            best, found = d, q
    return found


def _rest(points, centre, up, downhill=None, slope=0.):
    """Rock a rigid body to rest on a floor normal to `up` (both in the body's frame).
    Gravity leans `slope` degrees from the floor's normal towards `downhill`, a unit
    vector along the floor: 0 for a level floor. While the centre of mass, projected
    along gravity, lies outside the polygon of the lowest points, the body tips about
    the nearest point of that polygon's boundary until the next point meets the floor.

    Returns (outcome, up, polygon, centre in the floor's 2-D frame, touching indices,
    floor height, how far outside) with outcome 'rests', 'balanced' or 'tips'."""
    shear = 0. if slope <= 0. else sin(slope * pi / 180.) / cos(slope * pi / 180.)
    start = up
    for _ in range(24):
        heights = [_dot(p, up) for p in points]
        floor = min(heights)
        touching = [i for i, h in enumerate(heights) if h <= floor + TOUCH]
        u, v = _plane(up)
        flat = {(round(_dot(points[i], u), 7), round(_dot(points[i], v), 7)) for i in touching}
        lift = (_dot(centre, up) - floor) * shear
        c = (_dot(centre, u), _dot(centre, v))
        if downhill is not None and lift:
            c = (c[0] + lift * _dot(downhill, u), c[1] + lift * _dot(downhill, v))
        polygon = hull(list(flat))
        if len(polygon) >= 3 and area(polygon) > 1e-8 and margin(polygon, c) >= 0:
            return 'rests', up, polygon, c, touching, floor, 0.
        q = _nearest_on_boundary(polygon, c)
        away = (c[0] - q[0], c[1] - q[1])
        length = (away[0] ** 2 + away[1] ** 2) ** .5
        if length < 1e-9:   # balanced exactly over a line or a point: no margin either way
            return 'balanced', up, polygon, c, touching, floor, 0.
        m2 = (away[0] / length, away[1] / length)
        towards = tuple(m2[0] * u[i] + m2[1] * v[i] for i in range(3))
        pivot = tuple(q[0] * u[i] + q[1] * v[i] + floor * up[i] for i in range(3))
        angle = None
        for p in points:
            d = (p[0] - pivot[0], p[1] - pivot[1], p[2] - pivot[2])
            x = _dot(d, towards)
            if x > 1e-6:   # on the centre of mass's side of the pivot: it can come down
                a = atan2(max(_dot(d, up), 0.), x)
                if a > 1e-9 and (angle is None or a < angle):
                    angle = a
        rolled = degrees(acos(max(-1., min(1., _dot(start, up)))))
        if angle is None or rolled + degrees(angle) > TIPS_OVER:
            return 'tips', up, polygon, c, touching, floor, length
        if downhill is not None:   # the floor turns with the body's rocking: so does downhill
            along = _dot(downhill, towards)
            downhill = tuple(downhill[i] + along * ((cos(angle) - 1.) * towards[i] + sin(angle) * up[i])
                             for i in range(3))
        up = tuple(cos(angle) * up[i] - sin(angle) * towards[i] for i in range(3))
    return 'tips', up, polygon, c, touching, floor, length


def settle(points, centre, owners=None):
    """Where a rigid body resting on a level floor comes to rest (quasi-statically).

    `points` outline the body; `centre` is its centre of mass; `owners[i]` names the
    body point i belongs to. It rests on the points lowest along the current up
    direction; while the centre of mass lies outside the polygon they make it tips
    about the nearest point of that polygon's boundary, towards the centre of mass,
    until the next point meets the floor."""
    outcome, up, polygon, c, touching, floor, outside = _rest(points, centre, (0., 0., 1.))
    tilt = degrees(acos(max(-1., min(1., up[2]))))
    bodies = tuple(sorted({owners[i] for i in touching})) if owners else ()
    if outcome == 'rests':
        return Stance(margin(polygon, c), tilt, tuple(polygon), c, bodies, False,
                      _dot(centre, up) - floor, _tips(points, centre, up))
    if outcome == 'balanced':
        return Stance(0., tilt, tuple(polygon), c, bodies)
    return Stance(-outside, tilt, tuple(polygon), c, bodies, True)


def outline(blueprint):
    """Every body's outline points at the design pose, and the body each belongs to."""
    transforms = poses(blueprint)
    points, owners = [], []
    for b in blueprint.components:
        if isinstance(b, Body):
            found = surface_points(b, transforms[b.id])
            points.extend(found)
            owners.extend([b.id] * len(found))
    return points, owners


def clearance(blueprint):
    """How high, m, the lowest point of the design's free parts starts above the floor
    (z = 0), or None when nothing in it stands free. A run starts the design where it was
    built, so one built in the air falls - and lands with its wheels already driven, which
    moved the curb results of ADR 0022 (ADR 0023)."""
    roots = [b.id for b in blueprint.components if isinstance(b, Body) and b.parent is None and b.dynamic]
    if not roots:
        return None
    low, _ = world_bounds(blueprint, set().union(*(subtree(blueprint, r) for r in roots)))
    return low[2]


def standing(blueprint):
    """How the machine settles on a level floor with its joints as designed, or None
    when it has no body. The simulator's contacts decide at run time; this is the same
    question asked of the design before it runs."""
    points, owners = outline(blueprint)
    if not points:
        return None
    _, com = centre_of_mass(blueprint)
    return settle(points, com, owners)
