"""Opt-in OpenGL check: LITTLE_WORLD_TEST_RENDER=1 python -m pytest."""
import os
import pytest
pytest.importorskip("mujoco")
from little_world import Entity, World
from little_world.core.scene import Scene
from little_world.physics.mujoco_backend import MujocoBackend
from little_world.robots.two_wheel import two_wheel_blueprint
from little_world.scenes.room import room_entity


@pytest.mark.skipif(os.environ.get("LITTLE_WORLD_TEST_RENDER") != "1", reason="requires an OpenGL context")
def test_rgb_camera_and_resource_rebuild():
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("robot", two_wheel_blueprint())))) as world:
        world.start()
        first = backend.capture("robot/camera", 160, 120)
        assert first.shape == (120, 160, 3)
        assert str(first.dtype) == "uint8" and first.max() > first.min()
        world.reset()
        world.start()
        second = backend.capture("robot/camera", 160, 120)
        assert (first == second).all()
        assert backend.capture("robot/camera", 80, 60).shape == (60, 80, 3)
