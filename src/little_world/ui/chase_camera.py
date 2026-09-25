"""A chase view that follows a machine and turns with it (ADR 0012).

Pure Python, so its smoothing is testable without a window. The workshop copies the
result into MuJoCo's free camera, which places the eye `distance` behind `lookat`
along azimuth and elevation: azimuth equal to the machine's heading puts the camera
behind it, looking the way it drives.
"""
from dataclasses import dataclass
from math import exp


def wrap(angle):
    """Degrees into [-180, 180)."""
    return (angle + 180.) % 360. - 180.


@dataclass
class ChaseCamera:
    distance: float = 1.2
    elevation: float = -20.     # degrees; negative looks down
    offset: float = 0.          # the user's orbit, degrees relative to the heading
    follow_time: float = .12    # seconds for the look-at point to close 63 % of a gap
    turn_time: float = .35      # the same for the heading, so turns read as turns
    lookat: tuple | None = None
    yaw: float | None = None

    def reset(self, position, heading):
        self.lookat = tuple(float(v) for v in position)
        self.yaw = wrap(float(heading))

    def update(self, position, heading, dt):
        """Ease towards the machine; return (lookat, azimuth, elevation, distance)."""
        if self.lookat is None or self.yaw is None:
            self.reset(position, heading)
        dt = max(0., dt)
        follow = 1. - exp(-dt / self.follow_time)
        turn = 1. - exp(-dt / self.turn_time)
        self.lookat = tuple(a + follow * (float(b) - a) for a, b in zip(self.lookat, position))
        self.yaw = wrap(self.yaw + turn * wrap(float(heading) - self.yaw))
        return self.lookat, wrap(self.yaw + self.offset), self.elevation, self.distance

    def orbit(self, azimuth, elevation):
        self.offset = wrap(self.offset + azimuth)
        self.elevation = max(-85., min(-3., self.elevation + elevation))

    def zoom(self, factor):
        self.distance = max(.3, min(15., self.distance * factor))
