"""Depth cameras with their makers' numbers (ADR 0032). Standard library only.

A stereo depth camera finds a point's depth from its disparity d between two imagers a
baseline B apart: z = f B / d, f the focal length in pixels. The disparity is matched to a
fraction of a pixel, so depth is uncertain by z^2 / (f B) times that fraction: it grows with
the square of the distance (Keselman et al., "Intel RealSense Stereoscopic Depth Cameras",
arXiv 1705.05548, section 2.1; about 0.08 pixel measured, section 4.2). Intel's tuning
guide gives the same "subpixel" figure as below 0.1 on textured targets and names
848 x 480 as the D435's best depth resolution.
"""
from dataclasses import dataclass
from math import isfinite, radians, tan


@dataclass(frozen=True)
class DepthSensor:
    """A depth camera as a pinhole with a stereo noise model. Depth is measured along the
    optical axis (z), as the RealSense cameras report it."""
    id: str
    title: str
    width: int                  # pixels
    height: int
    hfov: float                 # degrees, horizontal and vertical fields of view of the depth image
    vfov: float
    baseline: float             # m between the stereo imagers
    subpixel: float             # RMS disparity error, pixels
    min_depth: float            # m: nearer than this, no depth
    max_depth: float            # m: further than this, not used
    frame_rate: float           # pictures a second
    source: str = ''

    def __post_init__(self):
        if type(self.width) is not int or type(self.height) is not int or self.width < 2 or self.height < 2:
            raise ValueError('a depth picture is at least 2 x 2 pixels')
        numbers = (self.hfov, self.vfov, self.baseline, self.subpixel, self.min_depth, self.max_depth, self.frame_rate)
        if not all(isfinite(v) for v in numbers):
            raise ValueError('a depth sensor needs finite numbers')
        if not (0 < self.hfov < 180 and 0 < self.vfov < 180):
            raise ValueError('fields of view are between 0 and 180 degrees')
        if self.baseline <= 0 or self.subpixel < 0 or not 0 <= self.min_depth < self.max_depth or self.frame_rate <= 0:
            raise ValueError('a depth sensor sees forwards from its nearest depth to its furthest')

    @property
    def fx(self):
        """Focal length in pixels across the picture."""
        return self.width / 2 / tan(radians(self.hfov) / 2)

    @property
    def fy(self):
        """Focal length in pixels up the picture."""
        return self.height / 2 / tan(radians(self.vfov) / 2)

    def sigma(self, depth):
        """RMS depth error at `depth` metres: z^2 x subpixel / (f B)."""
        return depth * depth * self.subpixel / (self.fx * self.baseline)

    def direction(self, column, row):
        """The ray through a pixel's centre in the camera's frame - x right, y up, looking
        along -z, as MuJoCo's cameras do - scaled so that its z is -1: a distance along it
        is the depth."""
        return ((column + .5 - self.width / 2) / self.fx, -(row + .5 - self.height / 2) / self.fy, -1.)

    def pixel(self, point):
        """(column, row) where a point in the camera's frame lands, or None behind it."""
        x, y, z = point
        if z >= 0:
            return None
        depth = -z
        return (self.width / 2 + self.fx * x / depth - .5, self.height / 2 - self.fy * y / depth - .5)


# Intel RealSense D435: depth field of view 87 x 58 degrees, ideal range 0.3 to 3 m, depth
# accuracy better than 2 % at 2 m, up to 90 frames a second (intelrealsense.com, "Compare
# depth cameras"); baseline 50 mm, best depth at 848 x 480, nearest depth about 16.8 cm at
# that resolution (Intel, "Tuning depth cameras for best performance"); RMS disparity error
# 0.08 pixel (Keselman et al. 2017). Its noise at 2 m, 14 mm, is 0.7 % of the depth.
REALSENSE_D435 = DepthSensor(
    'realsense_d435', 'Intel RealSense D435', 848, 480, 87., 58., .050, .08, .168, 3., 30.,
    'intelrealsense.com compare-depth-cameras; Intel tuning guide (dev.realsenseai.com); arXiv 1705.05548')

SENSORS = {s.id: s for s in (REALSENSE_D435,)}
