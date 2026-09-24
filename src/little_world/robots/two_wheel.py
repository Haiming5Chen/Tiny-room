"""A Blueprint factory, not a privileged Robot class."""
from math import sqrt
from little_world.components import box, wheel, Camera, Hinge, Motor, Transform
from little_world.core.blueprint import Blueprint, ControllerSpec
from little_world.core.component import Body, Geometry
from little_world.materials import METAL, RUBBER, SKID


def two_wheel_blueprint():
    axle = (sqrt(.5), -sqrt(.5), 0, 0)  # wheel local Z points along world +Y
    return Blueprint((
        box("chassis", (.32, .24, .09), "metal", dynamic=True,
            transform=Transform((0, 0, .13))),
        wheel("left_wheel", .085, .035, "rubber", parent="chassis",
              transform=Transform((0, .145, -.035), axle)),
        wheel("right_wheel", .085, .035, "rubber", parent="chassis",
              transform=Transform((0, -.145, -.035), axle)),
        Hinge("left_hinge", "left_wheel"), Hinge("right_hinge", "right_wheel"),
        Motor("left_motor", "left_hinge", 1.0), Motor("right_motor", "right_hinge", 1.0),
        # Passive skids support pitch; these are ordinary spheres.
        Body("front_skid", Geometry("sphere", (.025,)), "skid", parent="chassis",
             transform=Transform((.12, 0, -.08))),
        Body("rear_skid", Geometry("sphere", (.025,)), "skid", parent="chassis",
             transform=Transform((-.12, 0, -.08))),
        # Camera looks along chassis +X, local camera -Z, image up +Z.
        Camera("camera", "chassis", Transform((.17, 0, .04), (.5, .5, -.5, -.5))),
    ), (METAL, RUBBER, SKID),
       (ControllerSpec("drive", "differential_torque", ("left_motor", "right_motor")),))
