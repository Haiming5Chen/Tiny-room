"""What a camera standing off its believed pose does to where things are seen (ADR 0039).

A program reads a depth picture by where it believes the camera stands. If the camera stands
elsewhere - its stand set up by hand, or bumped - every point is read as the camera saw it,
but from the wrong place: a point at `p`, measured from the camera as it stands, is read at
c + R R'^T (p - c'), where c, R is the believed pose and c', R' the true one. For a camera
shifted by d and not turned that is p - d; turned by a small angle, the point swings about
the camera by the angle times its distance. Closed form, to predict what a sweep then
measures. numpy.
"""
import numpy as np


def _about(axis, degrees):
    a = np.radians(degrees)
    c, s = np.cos(a), np.sin(a)
    i, j = [(1, 2), (2, 0), (0, 1)][axis]
    m = np.eye(3)
    m[i, i], m[i, j], m[j, i], m[j, j] = c, -s, s, c
    return m


def turned(rotation, turn):
    """A camera's axes (columns of `rotation`) turned `turn` degrees about its own axes: pan
    about its up axis (y), then tilt about its right axis (x), then roll about its view (z) -
    as `MujocoBackend.move_camera` turns it."""
    pan, tilt, roll = (float(v) for v in turn)
    return np.asarray(rotation, dtype=float) @ _about(1, pan) @ _about(0, tilt) @ _about(2, roll)


def seen(point, position, rotation, shift=(0., 0., 0.), turn=(0., 0., 0.)):
    """Where `point` is read to be by a program that believes the camera stands at
    (`position`, `rotation`) when it stands shifted by `shift` metres and turned by `turn`
    degrees from there."""
    position, rotation = np.asarray(position, dtype=float), np.asarray(rotation, dtype=float)
    true_position = position + np.asarray(shift, dtype=float)
    true_rotation = turned(rotation, turn)
    return position + rotation @ true_rotation.T @ (np.asarray(point, dtype=float) - true_position)
