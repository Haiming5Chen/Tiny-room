"""Reserved interaction contract; no coupling scheduler or rules implemented."""
from typing import Protocol
from .state import State


class Interaction(Protocol):
    reads: frozenset[str]
    writes: frozenset[str]

    def evaluate(self, state: State, dt: float) -> State: ...
