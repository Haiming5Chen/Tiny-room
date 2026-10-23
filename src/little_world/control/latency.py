"""Time passes while the program looks and moves: what its camera and its servo bus take (FR-028).

In a lab a depth frame reaches the program some time after it was exposed, the finder takes its
time to find the part in it, and every servo command and reading crosses a serial bus; meanwhile
the world moves on. Each delay here is from a source:

- a picture: the frame interval at the camera's frame rate - the newest frame is up to one
  interval old (the D435 at 848 x 480 runs 30 fps, perception/sensors.py) - and the finder's own
  time, measured (FINDER);
- a command or a reading over a ROBOTIS Dynamixel bus (Protocol 2.0, X series, as the kit's jaws
  are read, ADR 0048): its packets' bytes at the bus's baud rate, ten bits a byte (a start bit,
  eight data bits, a stop bit), and each servo's return delay before it answers - the e-Manual's
  defaults, 57,600 bps and 500 us. A command is a Sync Write of every servo's goal position; a
  reading, a Sync Read of the registers a grasp is felt by, Moving to Present Position.

`Lag` holds a program's commands and readings back by their latencies, step by step; a picture's
is the camera's (perception/eye.py `Late`). Standard library only.
"""
from collections import deque
from dataclasses import dataclass
from math import isfinite

BAUD = 57600            # bps: the X series' default Baud Rate (1) (ROBOTIS e-Manual, XH430 control table)
RETURN_DELAY = 500e-6   # s: its default Return Delay Time, 250 x 2 us
BITS = 10               # bits a byte takes on the wire: start, 8 data, stop
INSTRUCTION = 10        # bytes of a Protocol 2.0 instruction packet besides its parameters: header (3),
                        # reserved, ID, length (2), instruction, CRC (2)
STATUS = 11             # bytes of a status packet besides its data: the same and an error byte
POSITION = 4            # bytes of Goal Position and of Present Position
REGISTERS = 14          # bytes from Moving (122) to the end of Present Position (135): what a grasp is felt by
FINDER = .106           # s: the classical finder (perception/boxes.find_box) on a Fetch look's picture,
                        # searching 25 cm round the plan - the median of 30, measured on a 2.1 GHz Xeon
                        # (31 ms searching the default 12 cm)
KIT_SERVOS = 6          # the kit arm's four joints and the gripper's two jaws, on one bus


def wire(count, baud=BAUD):
    """Seconds `count` bytes take on the bus."""
    return count * BITS / baud


def sync_write(servos, data=POSITION, baud=BAUD):
    """Seconds a Sync Write of `data` bytes to each of `servos` takes: one instruction packet whose
    parameters are the start address and length (4 bytes), then each servo's ID and data."""
    return wire(INSTRUCTION + 4 + servos * (1 + data), baud)


def sync_read(servos, data=POSITION, baud=BAUD, return_delay=RETURN_DELAY):
    """Seconds a Sync Read of `data` bytes from each of `servos` takes until the last answer is in:
    the instruction (start address, length and the servos' IDs), then each servo's status packet in
    turn, each after its return delay."""
    return wire(INSTRUCTION + 4 + servos + servos * (STATUS + data), baud) + servos * return_delay


@dataclass(frozen=True)
class Latency:
    """How late each of a program's paths is, in seconds: a picture's sighting reaches the program
    that long after the picture was exposed; a command reaches the servos that long after it was
    sent; a reading of the servos reaches the program that long after they were read."""
    picture: float = 0.
    command: float = 0.
    reading: float = 0.

    def __post_init__(self):
        if not all(isfinite(v) and v >= 0 for v in (self.picture, self.command, self.reading)):
            raise ValueError('a latency is a finite time, 0 or more seconds')

    @property
    def zero(self):
        return not (self.picture or self.command or self.reading)

    def steps(self, timestep):
        """The latencies in whole steps of `timestep`: (picture, command, reading)."""
        return tuple(round(v / timestep) for v in (self.picture, self.command, self.reading))

    @classmethod
    def every(cls, seconds):
        """The same latency on every path."""
        return cls(seconds, seconds, seconds)


def sourced(servos=KIT_SERVOS, frame_rate=30., finder=FINDER, baud=BAUD, return_delay=RETURN_DELAY):
    """The latencies of a camera at `frame_rate` whose pictures the finder reads in `finder` seconds,
    and of `servos` on one Dynamixel bus at its defaults."""
    if frame_rate <= 0 or servos < 1:
        raise ValueError('a camera has a frame rate and a bus at least one servo')
    return Latency(1. / frame_rate + finder, sync_write(servos, POSITION, baud),
                   sync_read(servos, REGISTERS, baud, return_delay))


class Lag:
    """A program's commands to its servos and its readings of them, held back by their latencies,
    a step at a time. The wheels are driven directly, not over the bus: their commands go at once."""
    BUS = ('action', 'move', 'pose')

    def __init__(self, latency, timestep):
        _, command, reading = latency.steps(timestep)
        self.sent = deque(maxlen=command + 1)
        self.read = deque(maxlen=reading + 1)

    def reading(self, value):
        """This step's reading in; the one the program has now out - the oldest still on its way,
        or the first ever taken until the bus has brought one that old."""
        self.read.append(value)
        return self.read[0]

    def command(self, output):
        """This step's runner output in; out, the same with what reaches the servos now: the bus's
        part of the output sent that many steps ago - nothing until then."""
        self.sent.append({k: output.get(k) for k in self.BUS})
        late = self.sent[0] if len(self.sent) == self.sent.maxlen else dict.fromkeys(self.BUS)
        return {**output, **late}
