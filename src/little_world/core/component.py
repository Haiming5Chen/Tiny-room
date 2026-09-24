"""Declarative physical parts; SI units, scalar-first quaternions."""
from dataclasses import dataclass
from math import isfinite, sqrt
from .motor_profile import MotorProfile


def vector(value, length, name):
    result = tuple(float(x) for x in value)
    if len(result) != length or not all(isfinite(x) for x in result):
        raise ValueError(f"{name} must have {length} finite values")
    return result


def positive(value, name):
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")


@dataclass(frozen=True)
class Transform:
    position: tuple = (0., 0., 0.)
    quaternion: tuple = (1., 0., 0., 0.)

    def __post_init__(self):
        object.__setattr__(self, "position", vector(self.position, 3, "position"))
        q = vector(self.quaternion, 4, "quaternion")
        if abs(sum(x*x for x in q) - 1) > 1e-6:
            raise ValueError("quaternion must be unit length")
        object.__setattr__(self, "quaternion", q)


@dataclass(frozen=True)
class Geometry:
    shape: str
    size: tuple

    def __post_init__(self):
        counts = {"box": 3, "cylinder": 2, "sphere": 1}
        if self.shape not in counts:
            raise ValueError(f"unsupported geometry: {self.shape}")
        size = vector(self.size, counts[self.shape], "size")
        for x in size:
            positive(x, "size")
        object.__setattr__(self, "size", size)


@dataclass(frozen=True)
class Attachment:
    id: str
    transform: Transform = Transform()


@dataclass(frozen=True)
class Component:
    id: str


@dataclass(frozen=True)
class Body(Component):
    geometry: Geometry
    material: str
    transform: Transform = Transform()
    parent: str | None = None
    dynamic: bool = False  # only root bodies can be free
    attachments: tuple[Attachment, ...] = ()
    catalog_part: str | None = None  # optional module provenance, not a native handle
    robot_asset: str | None = None  # registered immutable robot assembly

    def __post_init__(self):
        if self.robot_asset is not None and self.robot_asset not in ('franka_panda','franka_fr3','kinova_gen3','ur5e'):
            raise ValueError('Unknown registered robot asset')
        if self.catalog_part is not None and (not isinstance(self.catalog_part,str) or not self.catalog_part.strip()):
            raise ValueError("catalog_part must be a nonempty string")
        object.__setattr__(self, "attachments", tuple(self.attachments))
        names = [a.id for a in self.attachments]
        if len(set(names)) != len(names) or any(not n for n in names):
            raise ValueError("attachment IDs must be unique and nonempty")


@dataclass(frozen=True)
class Hinge(Component):
    body: str
    axis: tuple = (0., 0., 1.)
    damping: float = 0.01
    position: tuple = (0., 0., 0.)  # child-local pivot, metres
    limits: tuple | None = None  # lower/upper angle, degrees

    def __post_init__(self):
        object.__setattr__(self, "position", vector(self.position, 3, "hinge position"))
        if self.limits is not None:
            limits = vector(self.limits, 2, "hinge limits")
            if limits[0] >= limits[1]:
                raise ValueError("hinge lower limit must be less than upper limit")
            object.__setattr__(self, "limits", limits)
        axis = vector(self.axis, 3, "axis")
        norm = sqrt(sum(x*x for x in axis))
        positive(norm, "axis norm")
        object.__setattr__(self, "axis", tuple(x/norm for x in axis))
        if not isfinite(self.damping) or self.damping < 0:
            raise ValueError("damping must be finite and nonnegative")


@dataclass(frozen=True)
class Motor(Component):
    joint: str
    max_torque: float = 1.0
    profile: MotorProfile | None = None

    def __post_init__(self):
        positive(self.max_torque, "max_torque")
        if self.profile is not None:
            if not isinstance(self.profile,MotorProfile):raise ValueError('Invalid motor profile')
            if self.max_torque>self.profile.stall_torque:raise ValueError('Operating cap exceeds profile stall torque; remove profile for an ideal motor')


@dataclass(frozen=True)
class Camera(Component):
    body: str
    transform: Transform = Transform()
    fovy: float = 60.

    def __post_init__(self):
        if not isfinite(self.fovy) or not 0 < self.fovy < 180:
            raise ValueError("camera fovy must be between 0 and 180 degrees")


@dataclass(frozen=True)
class RobotServo(Component):
    """Named native position actuator in a registered robot, not a torque motor."""
    body: str
    channel: int

    def __post_init__(self):
        if type(self.channel) is not int or not 0 <= self.channel < 8:
            raise ValueError('Robot servo channel must be 0 through 7')
