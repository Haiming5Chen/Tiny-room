from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from .component import Transform


@dataclass(frozen=True)
class BodyState:
    pose: Transform
    linear_velocity: tuple[float, float, float]
    angular_velocity: tuple[float, float, float]


class DeferredBodyStates(Mapping):
    """Detached immutable records; materialize a BodyState only when accessed.

    The snapshot owns Python tuples, never views into native simulation memory.
    The private cache is a representation optimization, not mutable world state.
    """
    def __init__(self, records):
        self._records = MappingProxyType({
            name: value if isinstance(value, BodyState) else tuple(tuple(v) for v in value)
            for name, value in records.items()})
        self._cache = {}

    def __len__(self):
        return len(self._records)

    def __iter__(self):
        return iter(self._records)

    def __getitem__(self, name):
        if name not in self._cache:
            value = self._records[name]
            self._cache[name] = value if isinstance(value, BodyState) else BodyState(
                Transform(value[0],value[1]), value[2],value[3])
        return self._cache[name]


@dataclass(frozen=True)
class State:
    time: float
    bodies: Mapping[str, BodyState]

    def __post_init__(self):
        object.__setattr__(self, "bodies", self.bodies if isinstance(self.bodies, DeferredBodyStates) else MappingProxyType(dict(self.bodies)))
