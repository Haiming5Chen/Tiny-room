from enum import Enum
from typing import Mapping
from .component import positive
from .scene import Scene
from little_world.physics.backend import PhysicsBackend


class Mode(Enum):
    BUILD = "build"
    SIMULATE = "simulate"
    CLOSED = "closed"


class World:
    def __init__(self, backend: PhysicsBackend, scene: Scene, timestep: float = .002):
        positive(timestep, "timestep")
        self._backend, self._scene, self._timestep = backend, scene, timestep
        self._mode = Mode.BUILD
        self._prepared_scene = None

    @property
    def mode(self):
        return self._mode

    @property
    def scene(self):
        return self._scene

    @property
    def timestep(self):
        return self._timestep

    def set_scene(self, scene: Scene):
        self._require(Mode.BUILD)
        self._scene = scene

    def preview(self):
        """Compile the current design for inspection without leaving BUILD."""
        self._require(Mode.BUILD)
        if self._prepared_scene != self.scene:
            self._backend.compile(self.scene, self.timestep)
            self._prepared_scene = self.scene
        return self._backend.snapshot()

    def start(self):
        self._require(Mode.BUILD)
        self.preview()
        self._mode = Mode.SIMULATE
        return self._backend.snapshot()

    def step(self, commands: Mapping[str, float] | None = None):
        self._require(Mode.SIMULATE)
        return self._backend.step({} if commands is None else commands)

    def reset(self):
        self._require(Mode.SIMULATE)
        state = self._backend.reset()
        self._mode = Mode.BUILD
        return state

    def close(self):
        if self.mode != Mode.CLOSED:
            self._backend.close()
            self._mode = Mode.CLOSED

    def _require(self, mode):
        if self.mode != mode:
            raise RuntimeError(f"expected {mode.value}, got {self.mode.value}")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
