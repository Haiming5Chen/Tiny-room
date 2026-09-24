from dataclasses import dataclass
from typing import Mapping, Protocol
from .entity import Entity
from .state import State


@dataclass(frozen=True)
class Scene:
    entities: tuple[Entity, ...]

    def __post_init__(self):
        object.__setattr__(self, "entities", tuple(self.entities))
        if len({e.id for e in self.entities}) != len(self.entities):
            raise ValueError("duplicate entity ID")


@dataclass(frozen=True)
class Embodiment:
    entity_id: str
    actuators: tuple[str, ...]
    sensors: tuple[str, ...] = ()


class Task(Protocol):
    def evaluate(self, state: State, embodiment: Embodiment) -> Mapping[str, float]: ...


class Controller(Protocol):
    def command(self, state: State) -> Mapping[str, float]: ...
