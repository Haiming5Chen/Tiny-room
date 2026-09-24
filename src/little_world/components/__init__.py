"""Reusable construction helpers return ordinary declarative parts."""
from little_world.core.component import Body, Camera, Geometry, Hinge, Motor, Transform


def box(id, size, material, **kwargs):
    return Body(id, Geometry("box", size), material, **kwargs)


def beam(id, length, width, material, **kwargs):
    return box(id, (length, width, width), material, **kwargs)


def wheel(id, radius, width, material, **kwargs):
    return Body(id, Geometry("cylinder", (radius, width)), material, **kwargs)


__all__ = ["box", "beam", "wheel", "Body", "Camera", "Hinge", "Motor", "Transform"]
