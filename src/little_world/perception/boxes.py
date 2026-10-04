"""Finding a known box in a depth picture, classically (ADR 0032).

The steps a lab would take without a learned model: the picture's pixels become points in
the field; the surface the part stands on is the plane most of them lie in (RANSAC, then
least squares); what stands above that plane is gathered into clusters; a cluster is the
part when its top face - a rectangle fitted to the points near its top - has the part's own
size and stands at one of the part's own heights. The part's size is known; its place and
its turn are what is measured. numpy, no simulator.
"""
from dataclasses import dataclass
import numpy as np

SEARCH = .12      # m either way in plan from where the part was planned to be: where it is looked for
REACH = .10       # m above and below the planned centre that the search takes in
LIFT = .008       # m above the support plane before a point counts as standing on it
TOP = .001        # m: points this close to the cluster's top are its top face, or 1.5 sigma
FITS = .008       # m: a top face or height this far off the part's own is not the part
LINK = .01        # m: points closer than this in plan belong to the same cluster
TRIES = 200       # RANSAC samples for the support plane
TRIM = 3          # per cent of a face's points left out at each edge when measuring it


@dataclass(frozen=True)
class Sighting:
    """Where a box was seen: its centre in the field (m), its turn about the support's
    normal (degrees, measured like a heading from the field's X; a square face repeats every
    90, an oblong one every 180), which of its axes points up (0, 1, 2: x, y, z of the part),
    and how many points its top face had."""
    centre: tuple
    yaw: float
    up: int
    points: int
    height: float               # m from the support plane to its top face


def plane(points, tolerance, rng):
    """The plane most points lie within `tolerance` of: (a point on it, its unit normal
    pointing up), refined by least squares over those points; None for too few points."""
    if len(points) < 3:
        return None
    best, count = None, 0
    for _ in range(TRIES):
        a, b, c = points[rng.choice(len(points), 3, replace=False)]
        normal = np.cross(b - a, c - a)
        length = np.linalg.norm(normal)
        if length < 1e-9:
            continue
        normal /= length
        inside = np.abs((points - a) @ normal) <= tolerance
        n = int(inside.sum())
        if n > count:
            best, count = inside, n
    if best is None or count < 3:
        return None
    on = points[best]
    centre = on.mean(axis=0)
    normal = np.linalg.svd(on - centre, full_matrices=False)[2][2]
    if normal[2] < 0:
        normal = -normal
    return centre, normal


def clusters(flat, link=LINK):
    """Groups of points (arrays of indices) chained together by neighbours within `link`
    of each other in plan - single linkage. Points share a grid cell only when they are
    within `link` of each other, so cells are joined, not points."""
    flat = np.asarray(flat, dtype=float).reshape(-1, 2)
    cells = {}
    for i, key in enumerate(map(tuple, np.floor(flat / (link / np.sqrt(2))).astype(int))):
        cells.setdefault(key, []).append(i)
    keys = list(cells)
    number = {key: n for n, key in enumerate(keys)}
    parent = list(range(len(keys)))

    def root(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n
    for key in keys:
        mine = flat[cells[key]]
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                other = (key[0] + dx, key[1] + dy)
                if other <= key or other not in cells:
                    continue                    # each pair of cells once
                a, b = root(number[key]), root(number[other])
                if a != b and (np.linalg.norm(mine[:, None] - flat[cells[other]][None], axis=2) <= link).any():
                    parent[b] = a
    groups = {}
    for key in keys:
        groups.setdefault(root(number[key]), []).extend(cells[key])
    return [np.array(sorted(g)) for g in groups.values()]


def hull(flat):
    """Convex hull of points in plan (monotone chain), anticlockwise."""
    pts = sorted(set(map(tuple, np.round(flat, 9))))
    if len(pts) < 3:
        return np.array(pts)

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
    return np.array(lower[:-1] + upper[:-1])


def rectangle(flat):
    """The smallest rectangle round points in plan: (centre, (long side, short side),
    angle of the long side in radians); a hull edge lies along one of its sides."""
    edges = hull(flat)
    if len(edges) < 3:
        return None
    best = None
    for i in range(len(edges)):
        d = edges[(i + 1) % len(edges)] - edges[i]
        if not d.any():
            continue
        angle = np.arctan2(d[1], d[0])
        c, s = np.cos(angle), np.sin(angle)
        turned = flat @ np.array(((c, -s), (s, c)))
        low, high = turned.min(axis=0), turned.max(axis=0)
        area = float(np.prod(high - low))
        if best is None or area < best[0] - 1e-12:
            best = (area, angle, low, high)
    _, angle, low, high = best
    c, s = np.cos(angle), np.sin(angle)
    middle = (low + high) / 2
    centre = np.array((c * middle[0] - s * middle[1], s * middle[0] + c * middle[1]))
    sides = high - low
    if sides[1] > sides[0]:
        sides, angle = sides[::-1], angle + np.pi / 2
    return centre, (float(sides[0]), float(sides[1])), float(angle)


def oriented(flat):
    """A face's rectangle from its points in plan: turned as the smallest rectangle round
    them (`rectangle`), its sides and middle from the TRIM and 100 - TRIM percentiles along
    that turn, so that a few stray points do not move it. (centre, (long side, short side),
    angle of the long side in radians); the sides come out short by about 2 x TRIM per cent."""
    flat = np.asarray(flat, dtype=float)
    smallest = rectangle(flat)
    if smallest is None:
        return None
    angle = smallest[2]
    c, s = np.cos(angle), np.sin(angle)
    turned = flat @ np.array(((c, -s), (s, c)))
    low, high = np.percentile(turned, TRIM, axis=0), np.percentile(turned, 100 - TRIM, axis=0)
    middle = (low + high) / 2
    centre = np.array((c * middle[0] - s * middle[1], s * middle[0] + c * middle[1]))
    sides = high - low
    if sides[1] > sides[0]:
        sides, angle = sides[::-1], angle + np.pi / 2
    return centre, (float(sides[0]), float(sides[1])), float(angle)


def _fit(top, height, size):
    """Which of the part's axes points up, and how far off its top face and height are, for
    the best match; None when none matches within FITS."""
    best = None
    for up in range(3):
        rest = sorted((size[i] for i in range(3) if i != up), reverse=True)
        error = max(abs(top[0] - rest[0]), abs(top[1] - rest[1]), abs(height - size[up]))
        if error <= FITS and (best is None or error < best[1]):
            best = (up, error)
    return best


def find_box(points, planned, size, tolerance, rng, camera=None):
    """Where a box of `size` (m, its own x, y, z) stands among `points` (n x 3, the field's
    frame), looked for within SEARCH along X and Y and REACH in height of `planned`, its centre as
    planned. `tolerance` is how far off its plane a point of the support may lie: three times
    the camera's depth noise. Given where the `camera` was, the top face's points are laid on
    the top along the rays that saw them - a depth camera's error lies along its rays, so
    their place across the face is as sure as the pixels are. Returns (Sighting, indices of
    the points that are the box) or None."""
    points = np.asarray(points, dtype=float)
    planned = np.asarray(planned, dtype=float)
    if not len(points):
        return None
    near = np.all(np.abs(points - planned) <= (SEARCH, SEARCH, REACH), axis=1)
    index = np.nonzero(near)[0]
    found = plane(points[index], tolerance, rng)
    if found is None:
        return None
    origin, normal = found
    across = np.array((1., 0., 0.)) - normal[0] * normal       # the field's X laid on the plane
    if np.linalg.norm(across) < 1e-6:
        return None
    across /= np.linalg.norm(across)
    along = np.cross(normal, across)
    local = points[index] - origin
    height = local @ normal
    flat = np.stack((local @ across, local @ along), axis=1)
    lift = max(LIFT, tolerance + .002)
    standing = np.nonzero((height > lift) & (height < max(size) + .02))[0]
    best = None
    band = max(TOP, tolerance / 2)              # 1.5 sigma below the top
    for group in clusters(flat[standing]):
        members = standing[group]
        if len(members) < 6:
            continue
        rise = height[members]
        top = float(np.percentile(rise, 95))
        top = float(np.median(rise[np.abs(rise - top) <= tolerance]))
        face = members[np.abs(rise - top) <= band]
        if len(face) < 6:
            continue
        across_face = flat[face]
        if camera is not None:
            ray = local[face] - (np.asarray(camera, dtype=float) - origin)
            reach = (top - (np.asarray(camera) - origin) @ normal) / (ray @ normal)
            on_top = (np.asarray(camera) - origin) + reach[:, None] * ray
            across_face = np.stack((on_top @ across, on_top @ along), axis=1)
        box = oriented(across_face)
        if box is None:
            continue
        centre, sides, angle = box
        sides = tuple(v / (1 - 2 * TRIM / 100) for v in sides)
        fit = _fit(sides, top, size)
        if fit is None:
            continue
        up, error = fit
        miss = float(np.linalg.norm(origin[:2] + centre[0] * across[:2] + centre[1] * along[:2] - planned[:2]))
        if best is None or (error, miss) < best[0]:
            best = ((error, miss), members, centre, sides, angle, top, up, len(face))
    if best is None:
        return None
    _, members, centre, sides, angle, top, up, count = best
    middle = origin + centre[0] * across + centre[1] * along + normal * (top / 2)
    rest = sorted((size[i] for i in range(3) if i != up), reverse=True)
    period = 90. if abs(rest[0] - rest[1]) <= FITS else 180.
    yaw = (np.degrees(angle) + period / 2) % period - period / 2
    return Sighting(tuple(float(v) for v in middle), float(yaw), up, count, top), index[members]
