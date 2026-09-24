from dataclasses import dataclass
from .blueprint import Blueprint, identifier
from .component import Transform


@dataclass(frozen=True)
class Entity:
    id: str
    blueprint: Blueprint
    transform: Transform = Transform()

    def __post_init__(self):
        identifier(self.id)
