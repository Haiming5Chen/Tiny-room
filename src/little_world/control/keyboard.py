"""Bounded joint-position control; independent of UI and native solver handles."""
from math import radians


class KeyboardPositionControl:
    def __init__(self, specs=()):
        self.specs=tuple(c for c in specs if c.kind=='keyboard_position')
        self.held=set()
        self.targets={}

    def press(self,key):
        self.held.add(key)

    def release(self,key):
        self.held.discard(key)

    def clear(self):
        self.held.clear()

    def reset(self):
        self.clear()
        self.targets.clear()

    def commands(self,observations,dt):
        """Observations: actuator -> (angle, speed, lower, upper, max torque[, model bias]), SI."""
        result={}
        for spec in self.specs:
            direction=int(spec.positive_key in self.held)-int(spec.negative_key in self.held)
            for name in spec.actuators:
                angle,velocity,lower,upper,limit,*extra=observations[name]
                bias=extra[0] if extra else 0.
                target=self.targets.get(name,angle)+direction*radians(spec.speed)*dt
                self.targets[name]=target=max(lower,min(upper,target))
                result[name]=max(-limit,min(limit,bias+spec.kp*(target-angle)-spec.kd*velocity))
        return result
