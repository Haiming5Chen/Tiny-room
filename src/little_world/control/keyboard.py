"""Bounded joint-position control; independent of UI and native solver handles."""
from math import radians
from little_world.core.command import Torque


class KeyboardPositionControl:
    def __init__(self, specs=()):
        self.specs=tuple(c for c in specs if c.kind=='keyboard_position')
        self.held=set()
        self.targets={}
        # actuator -> the most torque it may push with, below its motor's: a smart servo's Goal
        # Current in current-based position control (FR-037). None set: the motor's own limit.
        self.limits={}

    def press(self,key):
        self.held.add(key)

    def release(self,key):
        self.held.discard(key)

    def clear(self):
        self.held.clear()

    def reset(self):
        self.clear()
        self.targets.clear()
        self.limits.clear()

    def commands(self,observations,dt):
        """Observations: actuator -> (angle, speed, lower, upper, max torque[, model bias]), SI.

        Each command is a Torque whose slope is the controller's damping, -kd, so a
        backend can apply that damping to the speed during the step rather than the
        speed before it (ADR 0014). A command at its limit no longer follows speed:
        it is the limit, a plain float."""
        result={}
        for spec in self.specs:
            direction=int(spec.positive_key in self.held)-int(spec.negative_key in self.held)
            for name in spec.actuators:
                angle,velocity,lower,upper,limit,*extra=observations[name]
                limit=min(limit,self.limits.get(name,limit))
                bias=extra[0] if extra else 0.
                target=self.targets.get(name,angle)+direction*radians(spec.speed)*dt
                self.targets[name]=target=max(lower,min(upper,target))
                torque=bias+spec.kp*(target-angle)-spec.kd*velocity
                result[name]=Torque(torque,-spec.kd) if -limit<torque<limit else max(-limit,min(limit,torque))
        return result
