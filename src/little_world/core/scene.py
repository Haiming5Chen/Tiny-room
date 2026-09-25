from dataclasses import dataclass
from typing import Mapping, Protocol
from .entity import Entity
from .state import State


BACKDROPS = ("sky",)


@dataclass(frozen=True)
class Scene:
    entities: tuple[Entity, ...]
    # Appearance only: what an adapter shows where nothing is (None: its default).
    backdrop: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "entities", tuple(self.entities))
        if len({e.id for e in self.entities}) != len(self.entities):
            raise ValueError("duplicate entity ID")
        if self.backdrop is not None and self.backdrop not in BACKDROPS:
            raise ValueError(f"unsupported backdrop: {self.backdrop}")


@dataclass(frozen=True)
class Embodiment:
    entity_id: str
    actuators: tuple[str, ...]
    sensors: tuple[str, ...] = ()


class Task(Protocol):
    def evaluate(self, state: State, embodiment: Embodiment) -> Mapping[str, float]: ...


class Controller(Protocol):
    def command(self, state: State) -> Mapping[str, float]: ...
