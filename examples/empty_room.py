from little_world import World
from little_world.physics.mujoco_backend import MujocoBackend
from little_world.scenes.room import empty_room
from little_world.ui.viewer import inspect

if __name__ == "__main__":
    backend = MujocoBackend()
    with World(backend, empty_room()) as world:
        while inspect(world, backend) == "reset":
            pass
