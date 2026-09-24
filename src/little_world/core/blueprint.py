"""Version 1 portable construction schema with strict reference validation."""
from dataclasses import asdict, dataclass
import json
import re
from math import isfinite

BINDABLE_KEYS = frozenset("QERTYUIOGHJKLZXVBNM0123456789")
from .component import Attachment, Body, Camera, Component, Geometry, Hinge, Motor, RobotServo, Transform
from .material import Material
from .motor_profile import MotorProfile
from .drive_settings import DriveSettings


def identifier(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", name):
        raise ValueError(f"invalid ID: {name!r}")


@dataclass(frozen=True)
class ControllerSpec:
    id: str
    kind: str
    actuators: tuple[str, ...]
    label: str = ''
    positive_key: str | None = None
    negative_key: str | None = None
    speed: float = 30.  # degrees / second
    kp: float = 12.    # Nm / rad
    kd: float = .8     # Nm s / rad

    drive_sides: tuple[int, ...] = ()
    drive_settings: DriveSettings = DriveSettings()

    def __post_init__(self):
        if isinstance(self.drive_settings,dict):object.__setattr__(self,"drive_settings",DriveSettings(**self.drive_settings))
        if not isinstance(self.drive_settings,DriveSettings):raise ValueError("Invalid drive settings")
        object.__setattr__(self,"drive_sides",tuple(self.drive_sides))
        if self.drive_sides and (len(self.drive_sides)!=len(self.actuators) or any(s not in (0,1) for s in self.drive_sides)):raise ValueError("Drive sides must identify left/right for each motor")
        object.__setattr__(self, "actuators", tuple(self.actuators))
        if self.kind == 'keyboard_position':
            if self.positive_key not in BINDABLE_KEYS or self.negative_key not in BINDABLE_KEYS:
                raise ValueError('Choose unused letter/number keys; WASD, F, C and P are reserved')
            if self.positive_key == self.negative_key:
                raise ValueError('Increase and decrease keys must differ')
            if not self.actuators or len(set(self.actuators)) != len(self.actuators):
                raise ValueError('Keyboard action needs unique actuators')
            if not isinstance(self.label,str) or len(self.label)>48:
                raise ValueError('Action name must be at most 48 characters')
            for value,lo,hi in ((self.speed,.1,180),(self.kp,.01,100),(self.kd,0,20)):
                if not isfinite(value) or not lo<=value<=hi:
                    raise ValueError('Speed or position-control gain is out of range')


@dataclass(frozen=True)
class Blueprint:
    components: tuple[Component, ...]
    materials: tuple[Material, ...]
    controllers: tuple[ControllerSpec, ...] = ()
    version: int = 1

    def __post_init__(self):
        for field in ("components", "materials", "controllers"):
            object.__setattr__(self, field, tuple(getattr(self, field)))
        self.validate()

    def validate(self):
        if type(self.version) is not int or self.version != 1:
            raise ValueError("unsupported Blueprint version")
        for collection in (self.components, self.materials, self.controllers):
            ids = [c.id for c in collection]
            for name in ids:
                identifier(name)
            if len(ids) != len(set(ids)):
                raise ValueError("duplicate ID")
        parts = {c.id: c for c in self.components}
        mats = {m.id for m in self.materials}
        hinged = set()
        for c in self.components:
            if type(c) not in (Body, Hinge, Motor, Camera, RobotServo):
                raise ValueError(f"unsupported component: {type(c).__name__}")
            if isinstance(c, Body):
                if c.material not in mats:
                    raise ValueError(f"unknown material: {c.material}")
                if c.parent is not None and not isinstance(parts.get(c.parent), Body):
                    raise ValueError("parent must reference a body")
                if c.parent is not None and c.dynamic:
                    raise ValueError("only roots may be free")
                seen = {c.id}
                parent = c.parent
                while parent is not None:
                    if parent in seen:
                        raise ValueError("body hierarchy cycle")
                    seen.add(parent)
                    ancestor = parts.get(parent)
                    if not isinstance(ancestor, Body):
                        raise ValueError("parent must reference a body")
                    parent = ancestor.parent
            elif isinstance(c, (Camera, Hinge)):
                body = parts.get(c.body)
                if not isinstance(body, Body):
                    raise ValueError("component must reference a body")
                if isinstance(c, Hinge):
                    if body.dynamic or c.body in hinged:
                        raise ValueError("one hinge per non-free body supported")
                    hinged.add(c.body)
            elif isinstance(c, RobotServo):
                if not isinstance(parts.get(c.body),Body) or not parts[c.body].robot_asset:
                    raise ValueError('Robot servo needs a registered robot body')
                if parts[c.body].robot_asset!='franka_panda' and c.channel >= (6 if parts[c.body].robot_asset=='ur5e' else 7):
                    raise ValueError('Servo channel outside registered robot model')
                if sum(isinstance(v,RobotServo) and v.body==c.body and v.channel==c.channel for v in self.components)>1:
                    raise ValueError('Duplicate robot servo channel')
            elif isinstance(c, Motor) and not isinstance(parts.get(c.joint), Hinge):
                raise ValueError("motor must reference a hinge")
        controlled=set()
        for c in self.controllers:
            if not c.kind or any(not isinstance(parts.get(a), (Motor,RobotServo)) for a in c.actuators):
                raise ValueError("controller needs a kind and valid actuators")
            if any(isinstance(parts[a],RobotServo) for a in c.actuators) and (c.kind!='keyboard_position' or len(c.actuators)!=1):
                raise ValueError('Robot servos use keyboard position actions')
            if c.kind in ('keyboard_position','differential_torque'):
                if controlled & set(c.actuators):
                    raise ValueError('An actuator cannot belong to two controllers')
                controlled.update(c.actuators)
            if c.kind == 'keyboard_position':
                for name in c.actuators:
                    if isinstance(parts[name],RobotServo):continue
                    joint=parts[parts[name].joint]
                    if joint.limits is None:
                        raise ValueError('Keyboard position control needs hinge angle limits')

    def to_json(self):
        data = asdict(self)
        data["components"] = [dict(asdict(c), kind=type(c).__name__.lower()) for c in self.components]
        return json.dumps(data, indent=2, allow_nan=False)

    @classmethod
    def from_json(cls, text):
        data = json.loads(text)
        if set(data) != {"version", "components", "materials", "controllers"}:
            raise ValueError("invalid Blueprint fields")
        parts = []
        kinds = {"body": Body, "hinge": Hinge, "motor": Motor, "camera": Camera, "robotservo": RobotServo}
        for raw in data["components"]:
            values = dict(raw)
            kind = values.pop("kind")
            if kind not in kinds:
                raise ValueError(f"unsupported component kind: {kind}")
            if "transform" in values:
                values["transform"] = Transform(**values["transform"])
            if kind == "body":
                values["geometry"] = Geometry(**values["geometry"])
                values["attachments"] = tuple(Attachment(a["id"], Transform(**a["transform"])) for a in values.get("attachments", []))
            if kind=='motor' and values.get('profile') is not None:
                values['profile']=MotorProfile(**values['profile'])
            parts.append(kinds[kind](**values))
        return cls(tuple(parts), tuple(Material(**m) for m in data["materials"]),
                   tuple(ControllerSpec(**c) for c in data["controllers"]), data["version"])
