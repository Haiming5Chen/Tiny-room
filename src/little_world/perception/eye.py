"""A depth camera in a running world, looking for known parts (ADR 0032).

A picture is the sensor's pixels cast as rays from the camera through the adapter
(`MujocoBackend.cast`): the distance to the first visible surface along each, as a depth -
the simulator's own geometry, no rendering context needed. Then the sensor's noise, its
nearest and furthest depths, and the points it makes in the field. Only the pixels that can
see the region round where the part was planned are cast: what the search would not use is
not computed. The part's pose is never read from the simulator.
"""
from dataclasses import dataclass
import numpy as np

from .boxes import REACH, SEARCH, find_box


@dataclass
class Picture:
    """One depth picture: rows and columns of the sensor it covers, depth in metres (NaN:
    no depth), and the camera's pose when it was taken."""
    rows: tuple
    columns: tuple
    depth: np.ndarray
    position: np.ndarray
    rotation: np.ndarray
    box: np.ndarray = None      # the pixels that were the part, when it was found

    def colours(self):
        """The picture as RGB bytes (rows x columns x 3) to show: near warm, far cool, no
        depth dark, the part's pixels green."""
        depth = self.depth
        rgb = np.full(depth.shape + (3,), 18, np.uint8)
        valid = np.isfinite(depth)
        if valid.any():
            low, high = np.nanmin(depth), np.nanmax(depth)
            t = np.clip((depth - low) / max(high - low, 1e-6), 0, 1)
            ramp = np.stack((235 - 175 * t, 120 + 40 * np.sin(np.pi * t), 60 + 175 * t), axis=-1)
            rgb[valid] = ramp[valid].astype(np.uint8)
        if self.box is not None and len(self.box):
            flat = rgb.reshape(-1, 3)
            flat[self.box] = (70, 230, 120)
        return rgb


class Eye:
    """Looks for known boxes with one depth camera. `sizes` maps a part's name to its size
    (m, its own x, y, z), as a lab knows the parts it picks. Calling it with a part and where
    the part was planned to be takes a picture and returns a `Sighting`, or None."""

    def __init__(self, backend, camera, sensor, sizes, seed=0, ideal=False):
        self.backend, self.camera, self.sensor = backend, camera, sensor
        self.sizes = {k: tuple(float(v) for v in s) for k, s in dict(sizes).items()}
        self.rng = np.random.default_rng(seed)
        self.ideal = ideal
        self.pictures = 0
        self.last = None

    def window(self, position, rotation, planned, search=SEARCH):
        """The rows and columns whose pixels can see the search round `planned`."""
        corners = [np.asarray(planned) + (dx, dy, dz) for dx in (-search, search)
                   for dy in (-search, search) for dz in (-REACH, REACH)]
        seen = [self.sensor.pixel(rotation.T @ (c - position)) for c in corners]
        if any(p is None for p in seen):
            return (0, self.sensor.height), (0, self.sensor.width)
        cols, rows = zip(*seen)
        top, bottom = max(0, int(np.floor(min(rows)))), min(self.sensor.height, int(np.ceil(max(rows))) + 1)
        left, right = max(0, int(np.floor(min(cols)))), min(self.sensor.width, int(np.ceil(max(cols))) + 1)
        return (top, bottom), (left, right)

    def picture(self, planned, search=SEARCH):
        """A depth picture of the region round `planned`, with the sensor's noise."""
        position, rotation = self.backend.camera_pose(self.camera)
        (top, bottom), (left, right) = self.window(position, rotation, planned, search)
        rows, cols = np.arange(top, bottom), np.arange(left, right)
        if not len(rows) or not len(cols):
            return Picture((top, bottom), (left, right), np.zeros((0, 0)), position, rotation)
        s = self.sensor
        x = (cols + .5 - s.width / 2) / s.fx
        y = -(rows + .5 - s.height / 2) / s.fy
        directions = np.stack(np.broadcast_arrays(x[None, :], y[:, None], -1.), axis=-1).reshape(-1, 3)
        depth = self.backend.cast(self.camera, directions, cutoff=s.max_depth * 1.5)
        if not self.ideal:
            noise = self.rng.standard_normal(depth.shape)
            depth = depth + noise * np.where(np.isfinite(depth), s.sigma(np.nan_to_num(depth)), 0.)
        depth = np.where((depth >= s.min_depth) & (depth <= s.max_depth), depth, np.nan)
        self.pictures += 1
        return Picture((top, bottom), (left, right), depth.reshape(len(rows), len(cols)), position, rotation)

    def points(self, picture):
        """The picture's pixels with depth as points in the field (n x 3), and their flat
        indices in the picture."""
        rows, cols = picture.depth.shape
        top, left = picture.rows[0], picture.columns[0]
        s = self.sensor
        x = (np.arange(left, left + cols) + .5 - s.width / 2) / s.fx
        y = -(np.arange(top, top + rows) + .5 - s.height / 2) / s.fy
        directions = np.stack(np.broadcast_arrays(x[None, :], y[:, None], -1.), axis=-1).reshape(-1, 3)
        depth = picture.depth.reshape(-1)
        valid = np.nonzero(np.isfinite(depth))[0]
        local = directions[valid] * depth[valid, None]
        return picture.position + local @ picture.rotation.T, valid

    def __call__(self, target, planned, search=None):
        """Where `target` is, looked for within `search` metres in plan of `planned` (None:
        SEARCH), or None when it is not seen."""
        search = SEARCH if search is None else float(search)
        if target not in self.sizes:
            raise ValueError(f'the camera does not know the size of {target}')
        picture = self.picture(planned, search)
        points, valid = self.points(picture)
        tolerance = max(.002, 3 * self.sensor.sigma(float(np.linalg.norm(np.asarray(planned) - picture.position))))
        found = find_box(points, planned, self.sizes[target], tolerance, np.random.default_rng(self.pictures),
                         picture.position, search)
        self.last = picture
        if found is None:
            return None
        sighting, members = found
        picture.box = valid[members]
        return sighting


def sizes_in(scene, entity='objects'):
    """The sizes of the loose boxes in a scene's entity, by their names in the running
    world ('objects/fetch_cube'): what a lab knows of the parts it picks."""
    from little_world.core.component import Body
    out = {}
    for e in scene.entities:
        if e.id != entity:
            continue
        for c in e.blueprint.components:
            if isinstance(c, Body) and c.geometry.shape == 'box':
                out[f'{e.id}/{c.id}'] = tuple(c.geometry.size)
    return out
