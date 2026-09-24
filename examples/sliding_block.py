"""A block slides down a ramp; gravity, contact and friction come from MuJoCo."""
from math import sin, cos
from little_world import Blueprint, Entity, World
from little_world.components import box, Transform
from little_world.core.material import Material
from little_world.core.scene import Scene
from little_world.physics.mujoco_backend import MujocoBackend
from little_world.scenes.room import room_entity
from little_world.ui.viewer import inspect

if __name__ == "__main__":
    surface = Material("surface", 600, .1, (.8, .5, .2, 1))
    rotation = (cos(.15), 0, sin(.15), 0)
    bp = Blueprint((
        box("ramp", (2, .7, .1), "surface", transform=Transform((0, 0, .4), rotation)),
        box("block", (.15, .15, .15), "surface", dynamic=True,
            transform=Transform((-.6, 0, .74), rotation)),
    ), (surface,))
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("slide", bp)))) as world:
        while inspect(world, backend) == "reset":
            pass
