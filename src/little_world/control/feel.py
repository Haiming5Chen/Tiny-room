"""What a gripper's servos tell a program about its grasp (ADR 0048, FR-026).

A program decides that it holds something - that a grasp worked, that it may carry on - and
until now it read that from the simulator's contacts: two jaw pads touching the same movable
part. A real robot has no such reading. A smart servo reports where it is and how hard it
pushes: a ROBOTIS X-series servo's control table has Present Position, Present Velocity and
Present Current, and a Moving flag. A jaw that has stopped short of where it was sent, pushing,
is a jaw closed on something. That is all `holding` uses, quantized as the registers count.

The kit gripper's jaws are read as ROBOTIS XH430-W350 servos at 12 V (the kit's servo, ADR
0007), each in current-based position control with its current limit at the 0.6 N m the kit
gives a jaw: a current limit of 85 units. The torque a current makes is taken from the
datasheet's stall point, 3.4 N m at 1.3 A - a line through zero, which the datasheet's
performance graph bends (ROBOTIS e-Manual, XH430-W350, read 2026-10-20).

Standard library only; `read` takes the backend's arrays.
"""
from dataclasses import dataclass
from math import pi

TORQUE_PER_AMP = 3.4 / 1.3      # N m/A: the XH430-W350's stall torque over its stall current at 12 V
CURRENT_UNIT = .00269           # A: what one count of Present Current (address 126) is
PULSE = 2 * pi / 4096           # rad: one count of Present Position (address 132), 4096 a turn
VELOCITY_UNIT = .229 * 2 * pi / 60   # rad/s: one count of Present Velocity (address 128), 0.229 rev/min
MOVING = 10                     # counts of velocity: the Moving Threshold's default (address 24) - slower
                                # than this, the servo reports itself still (Moving, address 122, is 0)
SHORT = 2                       # pulses a jaw must stop short of its goal to be closed on something
FELT = 6                        # counts of current (16 mA, 0.042 N m) a still jaw must push with to hold:
                                # what the kit jaw draws to move itself at full speed; a jaw just starting
                                # to move is still and behind its goal for some 15 ms, at 3 or 4 counts


@dataclass(frozen=True)
class Jaw:
    """One jaw servo's registers, its closing direction positive."""
    position: int       # pulses
    goal: int           # pulses: where it was sent
    velocity: int       # counts of VELOCITY_UNIT
    current: int        # counts of CURRENT_UNIT

    @property
    def moving(self):
        return abs(self.velocity) > MOVING

    @property
    def short(self):
        """How far it stopped short of its goal, closing (pulses)."""
        return self.goal - self.position


def counts(torque, angle, goal, speed):
    """A jaw's registers from its torque (N m), angle and goal (rad) and speed (rad/s)."""
    return Jaw(round(angle / PULSE), round(goal / PULSE), round(speed / VELOCITY_UNIT),
               round(torque / TORQUE_PER_AMP / CURRENT_UNIT))


def holding(jaws):
    """Whether these jaws hold something: every one still, stopped at least SHORT pulses short
    of its goal and pushing towards it with at least FELT counts of current."""
    jaws = tuple(jaws)
    return bool(jaws) and all(not j.moving and j.short >= SHORT and j.current >= FELT for j in jaws)


def read(backend, control, actuators, prefix='machine/'):
    """The jaw servos' registers now: `actuators`, the gripper's actuator names, driven by the
    kit's position control `control` (its targets are the goals). None for a gripper whose jaws
    are not the kit's motors - a registered model's own servo - which is not read this way."""
    m, d = backend.model, backend.data
    jaws = []
    for name in actuators:
        channel = getattr(control, 'channels', {}).get(name)
        if channel is None or name in getattr(control, 'servos', {}) or name not in control.targets:
            return None
        q, v = channel[0], channel[1]
        torque = float(d.actuator_force[m.actuator(prefix + name).id])
        jaws.append(counts(torque, float(d.qpos[q]), float(control.targets[name]), float(d.qvel[v])))
    return tuple(jaws)
