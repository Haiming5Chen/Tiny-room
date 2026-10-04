"""Finding a known box in a depth picture (ADR 0032, FR-011).

Pictures here are drawn by intersecting each pixel's ray with boxes in numpy - no simulator,
no GL - so the finding is checked against geometry it cannot have peeked at. The camera
stands as the Fetch table's does: 0.9 m up, 0.45 m beyond the cube, 60 degrees down.
"""
from math import cos, radians, sin

import pytest

np = pytest.importorskip('numpy')

from little_world.perception.boxes import clusters, find_box, rectangle  # noqa: E402
from little_world.perception.sensors import REALSENSE_D435, DepthSensor  # noqa: E402

CUBE = (.025, .025, .040)
TABLE = .12
CAMERA = np.array((2.30, 0., .90))


def turned(yaw=0., tilt=0.):
    """Rotation about z by `yaw` then about x by `tilt`, degrees."""
    c, s = cos(radians(yaw)), sin(radians(yaw))
    z = np.array(((c, -s, 0), (s, c, 0), (0, 0, 1)))
    c, s = cos(radians(tilt)), sin(radians(tilt))
    return np.array(((1, 0, 0), (0, c, -s), (0, s, c))) @ z


def looking(position, target):
    f = np.asarray(target, float) - position
    f /= np.linalg.norm(f)
    r = np.cross(f, (0, 0, 1.))
    r /= np.linalg.norm(r)
    return np.stack((r, np.cross(r, f), -f), axis=1)          # columns: x right, y up, z back


def hits(origin, directions, centre, half, rotation):
    """Distance along each direction to an oriented box, inf where it misses (slabs)."""
    o = (origin - centre) @ rotation
    d = directions @ rotation
    with np.errstate(divide='ignore', invalid='ignore'):
        a, b = (-half - o) / d, (half - o) / d
    near = np.nanmax(np.minimum(a, b), axis=1)
    far = np.nanmin(np.maximum(a, b), axis=1)
    return np.where((far >= near) & (far > 0), np.maximum(near, 0), np.inf)


def picture(boxes, sensor=REALSENSE_D435, camera=CAMERA, aim=(1.85, 0., TABLE), noise=None, table_tilt=0.):
    """Depth of every pixel of a window round the aim, and the points it makes."""
    rotation = looking(camera, aim)
    rows, cols = np.arange(140, 340), np.arange(330, 520)
    x = (cols + .5 - sensor.width / 2) / sensor.fx
    y = -(rows + .5 - sensor.height / 2) / sensor.fy
    local = np.stack(np.broadcast_arrays(x[None, :], y[:, None], -1.), axis=-1).reshape(-1, 3)
    world = local @ rotation.T
    table = turned(0., table_tilt)          # turned about the middle of its top
    depth = hits(camera, world, np.array((2.0, 0., TABLE)) - table @ (0, 0, .5), np.array((.2, .25, .5)), table)
    for centre, size, r in boxes:
        depth = np.minimum(depth, hits(camera, world, np.asarray(centre, float), np.asarray(size) / 2, r))
    depth[~np.isfinite(depth)] = np.nan
    if noise is not None:
        depth = depth + noise.standard_normal(depth.shape) * sensor.sigma(np.nan_to_num(depth))
    ok = np.isfinite(depth)
    return camera + (local[ok] * depth[ok, None]) @ rotation.T


def cube_at(x, y, yaw=0., up=2):
    r = turned(yaw)
    size = CUBE if up == 2 else (CUBE[2], CUBE[1], CUBE[0])       # lying on its side
    return (x, y, TABLE + size[2] / 2), size, r


def look(points, planned=(1.84, 0., TABLE + .02), tolerance=.002, seed=0, camera=CAMERA):
    return find_box(points, planned, CUBE, tolerance, np.random.default_rng(seed), camera)


def test_the_d435_is_its_makers_numbers():
    s = REALSENSE_D435
    assert s.fx == pytest.approx(446.8, abs=.1) and (s.width, s.height) == (848, 480)
    # Stereo depth error grows as z^2: at 2 m, 14 mm - within the maker's "under 2 % at 2 m".
    assert s.sigma(2.) == pytest.approx(.0143, abs=.0002) and s.sigma(2.) < .02 * 2.
    assert s.sigma(.87) == pytest.approx(.0027, abs=.0001)
    column, row = s.pixel(np.array(s.direction(100, 50)) * 1.7)
    assert (column, row) == (pytest.approx(100), pytest.approx(50))
    with pytest.raises(ValueError):
        DepthSensor('x', 'x', 848, 480, 87., 58., .05, .08, 3., .2, 30.)


def test_a_cube_on_the_table_is_found_where_it_stands():
    for x, y, yaw in ((1.84, 0., 0.), (1.86, .05, 0.), (1.83, -.06, 20.), (1.90, .02, -35.)):
        seen, members = look(picture([cube_at(x, y, yaw)]))
        assert seen.up == 2 and len(members) > 100
        assert np.allclose(seen.centre, (x, y, TABLE + .02), atol=.0015), (x, y, seen.centre)
        assert abs((seen.yaw - yaw + 45) % 90 - 45) < 1.5, (yaw, seen.yaw)


def test_lying_on_its_side_it_is_found_lower():
    seen, _ = look(picture([cube_at(1.85, .01, 30., up=0)]))
    assert seen.up in (0, 1) and seen.height == pytest.approx(.025, abs=.002)
    assert np.allclose(seen.centre, (1.85, .01, TABLE + .0125), atol=.002)
    assert abs((seen.yaw - 30 + 90) % 180 - 90) < 2


def test_with_the_cameras_noise_it_is_within_5_mm_and_5_degrees():
    rng = np.random.default_rng(7)
    errors, turns = [], []
    for k in range(12):
        x, y, yaw = 1.84 + .01 * (k % 3), -.05 + .01 * k, (-20. + 4 * k)
        seen, _ = look(picture([cube_at(x, y, yaw)], noise=rng), tolerance=3 * REALSENSE_D435.sigma(.87), seed=k)
        errors.append(np.linalg.norm(np.subtract(seen.centre, (x, y, TABLE + .02))))
        turns.append(abs((seen.yaw - yaw + 45) % 90 - 45))
    assert max(errors) < .005 and max(turns) < 5., (max(errors), max(turns))


def test_nothing_there_or_another_size_is_not_the_cube():
    assert look(picture([])) is None
    assert look(picture([((1.85, 0., TABLE + .025), (.05, .05, .05), turned())])) is None
    # A cube beside a larger box: the cube is found, not the box.
    seen, _ = look(picture([((1.90, -.06, TABLE + .03), (.06, .04, .06), turned()), cube_at(1.83, .04)]))
    assert np.allclose(seen.centre[:2], (1.83, .04), atol=.0015)


def test_a_tilted_support_is_still_found_as_its_plane():
    tilt = 8.
    r = turned(0., tilt)
    top = r @ (0, 0, 1.)
    at = np.array((1.84, .03, 0.))
    at[2] = TABLE - (top[1] * at[1]) / top[2]                     # on the tilted top
    cube = (at + top * .02, CUBE, r)
    seen, _ = look(picture([cube], table_tilt=tilt), planned=(1.84, .03, TABLE + .02))
    assert np.allclose(seen.centre, cube[0], atol=.002)


def test_points_in_clusters_and_rectangles():
    a = np.array([(x, y) for x in np.arange(0, .02, .002) for y in np.arange(0, .02, .002)])
    b = a + (.05, 0)
    groups = clusters(np.vstack((a, b)))
    assert sorted(len(g) for g in groups) == [100, 100]
    c, s = cos(radians(30)), sin(radians(30))
    square = np.array([(x, y) for x in np.linspace(-.01, .01, 21) for y in np.linspace(-.02, .02, 41)]) @ np.array(((c, s), (-s, c)))
    centre, sides, angle = rectangle(square + (1., 2.))
    assert np.allclose(centre, (1., 2.)) and sides == (pytest.approx(.04), pytest.approx(.02))
    assert (np.degrees(angle) - 120) % 180 == pytest.approx(0, abs=1e-6) or (np.degrees(angle) - 120) % 180 == pytest.approx(180, abs=1e-6)
