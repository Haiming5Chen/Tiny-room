"""A depth camera in a running world, looking for known parts (ADR 0032).

A picture is the sensor's pixels cast as rays from the camera through the adapter
(`MujocoBackend.cast`): the distance to the first visible surface along each, as a depth -
the simulator's own geometry, no rendering context needed. Then the sensor's noise, its
nearest and furthest depths, and the points it makes in the field. Only the pixels that can
see the region round where the part was planned are cast: what the search would not use is
not computed. The part's pose is never read from the simulator.
"""
from collections import deque
from dataclasses import dataclass
import numpy as np

from .boxes import REACH, SEARCH, find_box, place


@dataclass
class Picture:
    """One depth picture: rows and columns of the sensor it covers, depth in metres (NaN:
    no depth), and the camera's pose when it was taken. Like a RealSense frame it carries a
    frame number and the time it was taken (ADR 0038)."""
    rows: tuple
    columns: tuple
    depth: np.ndarray
    position: np.ndarray
    rotation: np.ndarray
    box: np.ndarray = None      # the pixels that were the part, when it was found
    frame: int = 0              # counts the camera's frames: a new picture has a new number
    stamp: float = 0.           # simulated seconds when it was taken

    @property
    def valid(self):
        """The share of its pixels that have a depth."""
        return float(np.isfinite(self.depth).mean()) if self.depth.size else 0.

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
    the part was planned to be takes a picture and returns a `Sighting`, or None.

    The camera can fail as a disturbance makes it (`fail`, ADR 0038): frozen, it sends the last
    picture it took - of the region it was last asked about - again and again, frame number
    and all; dark, its pictures are new and have no depth. The Eye does not hide either: each
    picture carries its frame number and how much of it has depth, for the program to judge."""

    FAULTS = ('freeze', 'dark')

    def __init__(self, backend, camera, sensor, sizes, seed=0, ideal=False, believed=None):
        self.backend, self.camera, self.sensor = backend, camera, sensor
        # Where the program believes the camera is - (position, rotation) as `camera_pose`
        # gives them - when that is not where it is (ADR 0039): its pictures are cast from the
        # camera as it stands and read as if it stood there. None: it stands where believed.
        self.believed = None if believed is None else tuple(np.array(v, dtype=float) for v in believed)
        self.sizes = {k: tuple(float(v) for v in s) for k, s in dict(sizes).items()}
        self.rng = np.random.default_rng(seed)
        self.ideal = ideal
        self.pictures = 0           # pictures cast (each draws its own noise)
        self.frames = 0             # frames the camera has made: what a picture's number counts
        self.last = None
        self.fault = None           # None, or one of FAULTS
        self.frozen = None          # the picture a frozen camera keeps sending
        self.asked = None           # the region of the last picture asked for: (planned, search)

    def fail(self, fault):
        """The camera fails now - 'freeze' or 'dark' - or, with None, works again. Frozen, its
        last picture is taken now, of the region it was last asked about: the world as it is
        at this moment, sent from then on."""
        if fault is not None and fault not in self.FAULTS:
            raise ValueError(f'a camera fails in one of {self.FAULTS}, not {fault!r}')
        self.fault, self.frozen = fault, None
        if fault == 'freeze' and self.asked is not None:
            self.frozen = self._take(*self.asked)

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
        """A depth picture of the region round `planned`, with the sensor's noise - or, from a
        camera that has failed, its last picture again (frozen) or a picture without depth
        (dark)."""
        self.asked = (tuple(planned), search)
        if self.fault == 'freeze':
            if self.frozen is None:         # frozen before it was asked for anything
                self.frozen = self._take(planned, search)
            return self.frozen
        return self._take(planned, search, dark=self.fault == 'dark')

    def _take(self, planned, search=SEARCH, dark=False):
        """A new frame of the region round `planned`: cast, with noise - or, dark, without depth.
        The rays leave the camera as it stands; the picture says it was taken from where the
        camera is believed to be, which is all a program has to read it by."""
        position, rotation = self.believed or self.backend.camera_pose(self.camera)
        (top, bottom), (left, right) = self.window(position, rotation, planned, search)
        rows, cols = np.arange(top, bottom), np.arange(left, right)
        self.frames += 1
        stamp = float(getattr(getattr(self.backend, 'sight', getattr(self.backend, 'data', None)), 'time', 0.))
        if not len(rows) or not len(cols) or dark:
            return Picture((top, bottom), (left, right), np.full((len(rows), len(cols)), np.nan), position, rotation,
                           frame=self.frames, stamp=stamp)
        self.pictures += 1
        s = self.sensor
        x = (cols + .5 - s.width / 2) / s.fx
        y = -(rows + .5 - s.height / 2) / s.fy
        directions = np.stack(np.broadcast_arrays(x[None, :], y[:, None], -1.), axis=-1).reshape(-1, 3)
        depth = self.backend.cast(self.camera, directions, cutoff=s.max_depth * 1.5)
        if not self.ideal:
            noise = self.rng.standard_normal(depth.shape)
            depth = depth + noise * np.where(np.isfinite(depth), s.sigma(np.nan_to_num(depth)), 0.)
        depth = np.where((depth >= s.min_depth) & (depth <= s.max_depth), depth, np.nan)
        return Picture((top, bottom), (left, right), depth.reshape(len(rows), len(cols)), position, rotation,
                       frame=self.frames, stamp=stamp)

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

    def place(self, target, centre):
        """What the last picture shows where `target` was seen centred at `centre`: 'there',
        'empty' or 'hidden' (`boxes.place`) - for when the last call found nothing there. The
        open jaws above a part can hide its top face, which the finder needs, while the rest of
        it is plainly in the picture (OPEN LW-022)."""
        if target not in self.sizes:
            raise ValueError(f'the camera does not know the size of {target}')
        picture = self.last if self.last is not None else self.picture(centre)
        points, _ = self.points(picture)
        tolerance = max(.005, 3 * self.sensor.sigma(float(np.linalg.norm(np.asarray(centre) - picture.position))))
        return place(points, picture.position, centre, self.sizes[target], tolerance)


class Late:
    """A camera whose sightings reach the program late (FR-028): each picture shows the world as
    it was `steps` steps of the simulation ago - the frame interval and the finder's time - while
    the world has moved on. `keep()` after every step keeps the moments it will show; until it has
    kept that many, a picture shows the oldest. Everything else is the camera's own (`Eye`)."""

    def __init__(self, eye, backend, steps):
        self.eye, self.backend = eye, backend
        self.moments = deque(maxlen=int(steps) + 1)

    def keep(self):
        self.moments.append(self.backend.kept())

    def _then(self):
        if not self.moments:
            self.keep()
        return self.backend.as_it_was(self.moments[0])

    def __call__(self, target, planned, search=None):
        with self._then():
            return self.eye(target, planned, search)

    def place(self, target, centre):
        with self._then():
            return self.eye.place(target, centre)

    def fail(self, fault):
        with self._then():
            return self.eye.fail(fault)

    def __getattr__(self, name):
        return getattr(self.eye, name)


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
