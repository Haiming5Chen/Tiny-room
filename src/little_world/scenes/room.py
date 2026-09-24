from little_world.components import box, Transform
from little_world.core.blueprint import Blueprint
from little_world.core.entity import Entity
from little_world.core.scene import Scene
from little_world.materials import FLOOR, WOOD


def room_entity():
    return Entity("room", Blueprint((
        box("floor", (6, 6, .1), "floor", transform=Transform((0, 0, -.05))),
        box("north_wall", (6, .1, .5), "floor", transform=Transform((0, 3, .25))),
        box("south_wall", (6, .1, .5), "floor", transform=Transform((0, -3, .25))),
        box("east_wall", (.1, 6, .5), "floor", transform=Transform((3, 0, .25))),
        box("west_wall", (.1, 6, .5), "floor", transform=Transform((-3, 0, .25))),
        box("obstacle", (.4, .6, .3), "wood", transform=Transform((1.4, .8, .15))),
    ), (FLOOR, WOOD)))


def empty_room():
    return Scene((room_entity(),))
