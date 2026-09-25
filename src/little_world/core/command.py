"""Actuator commands that say how they change with speed (ADR 0014).

Standard library only. A controller's torque usually depends on the joint's speed - a
position servo's damping is -kd * speed - but a command is computed once per step,
from the speed at the start of it. Applied as a constant for the step, that feedback
acts late; at the gains servos use it is unstable. A `Torque` is still the torque to
apply, a float every backend can use as it is, and it also carries `slope`, the change
in that torque per unit of joint speed, so a backend that integrates implicitly can
let the torque follow the speed within the step, as the servo's own electronics do.
"""
from math import isfinite


class Torque(float):
    """A torque command, N m, with its slope with respect to joint speed, N m s/rad.

    The slope is never positive: a servo's feedback removes energy, and a positive
    slope would ask an implicit integrator to feed it in. Arithmetic on a Torque
    gives a plain float, so a command that has been changed loses its slope rather
    than keeping one that no longer describes it.
    """

    def __new__(cls, value, slope=0.):
        value, slope = float(value), float(slope)
        if not isfinite(value) or not isfinite(slope):
            raise ValueError('torque and slope must be finite')
        if slope > 0.:
            raise ValueError('a torque slope must not be positive: it would add energy')
        torque = super().__new__(cls, value)
        torque.slope = slope
        return torque

    def __repr__(self):
        return f'Torque({float(self)!r}, slope={self.slope!r})'


def slope_of(command):
    """The command's slope with respect to joint speed; zero for a plain number."""
    return getattr(command, 'slope', 0.)
