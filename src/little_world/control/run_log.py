"""A test run in numbers: what the driver saw, accumulated frame by frame (ADR 0012).

Standard library only. Samples come from `control/drive_telemetry.py` and are ideal:
exact simulator state, no noise, no latency. The log keeps running totals rather
than every frame, and its summary is what the run report shows and what the next
run is compared with.
"""
from dataclasses import dataclass
from math import dist

TIPPED = 60.   # degrees from upright: on its side, not merely leaning
STEP = .005    # metres the machine must move before the path counts it
SLIPPING = .05 # m/s of tread speed beyond the ground speed under that wheel


@dataclass(frozen=True)
class MotorSample:
    name: str
    rpm: float                  # output shaft, signed
    no_load_rpm: float | None   # the sourced profile's no-load speed; None for an ideal motor
    torque: float               # delivered, N m, signed
    available: float            # the most it could deliver at this speed, N m
    saturated: bool             # delivering all it can
    slip: float = 0.            # tread speed minus ground speed at the wheel, m/s
    kept: float | None = None   # a weakened motor's share of its own stall torque; None as built (ADR 0058)

    @property
    def slipping(self):
        return self.slip > SLIPPING


@dataclass(frozen=True)
class DriveSample:
    time: float                 # simulated seconds
    position: tuple             # machine root, world metres
    speed: float                # along the machine's forward axis, m/s, signed
    tilt: float                 # degrees from upright
    motors: tuple = ()
    margin: float | None = None # static tip margin: centre of mass inside the support polygon, m
    tip: float | None = None    # degrees left before it tips, its accelerations counted (ADR 0059)


@dataclass(frozen=True)
class RunSummary:
    duration: float = 0.
    distance: float = 0.        # path length over the floor
    displacement: float = 0.    # start to finish, over the floor
    top_speed: float = 0.
    max_tilt: float = 0.
    saturated_share: float = 0. # share of the run with any motor at its limit
    slip_share: float = 0.      # share of the run with any driven wheel slipping
    touched: tuple = ()
    min_margin: float | None = None  # the smallest static tip margin seen, m; None if never standing
    min_tip: float | None = None     # the fewest degrees it had left before tipping (ADR 0059)

    @property
    def tipped(self):
        """Seen to go over: tilted past TIPPED, on its side."""
        return self.max_tilt > TIPPED

    def stability_lines(self):
        """What the run report says of tipping, as (text, warn) lines (LW-048). The stance margin and
        the degrees from tipping (ADR 0059) are estimates, made each frame from what the machine stands
        on, and are labelled so: at a curb a frame's support can be one wheel's treads, or two casters
        with one pressed against the curb's edge, and both fall below zero while the machine stays
        upright. What was seen follows them when they say it was past tipping: only the tilt it reached
        says it went over (`tipped`), and the report says that on its own line."""
        lines = []
        if self.min_margin is not None:
            lines.append((f'estimated: lowest stance margin {100 * self.min_margin:.1f} cm', self.min_margin < .01))
        if self.min_tip is not None:
            lines.append((f'estimated: fewest {self.min_tip:.0f} deg from tipping', self.min_tip < 10))
        past = (self.min_margin is not None and self.min_margin < 0) or (self.min_tip is not None and self.min_tip <= 0)
        if past and not self.tipped:
            lines.append((f'seen: tilted {self.max_tilt:.0f} deg at most, did not tip', False))
        return tuple(lines)

    @property
    def average_speed(self):
        return self.distance / self.duration if self.duration > 0 else 0.

    def versus(self, previous):
        """Differences from an earlier run: positive means more in this one."""
        return {name: getattr(self, name) - getattr(previous, name)
                for name in ("duration", "distance", "top_speed", "max_tilt")}


class RunLog:
    def __init__(self):
        self.samples = 0
        self._first = self._last = None
        self._anchor = None
        self._distance = self._top = self._tilt = self._saturated = self._slipping = 0.
        self._touched = set()
        self._margin = None
        self._tip = None

    def add(self, sample, touched=()):
        """One displayed frame. A frame at the same simulated time (paused) adds nothing."""
        self._touched.update(touched)
        if self._last is not None:
            if sample.time < self._last.time:
                raise ValueError("samples must move forward in simulated time")
            if sample.time == self._last.time:
                return
            if any(m.saturated for m in self._last.motors):
                self._saturated += sample.time - self._last.time
            if any(m.slipping for m in self._last.motors):
                self._slipping += sample.time - self._last.time
        else:
            self._first = sample
            self._anchor = sample.position[:2]
        # Shimmer below STEP is not travel; slow driving still counts once it adds up.
        moved = dist(self._anchor, sample.position[:2])
        if moved >= STEP:
            self._distance += moved
            self._anchor = sample.position[:2]
        self._last = sample
        self.samples += 1
        self._top = max(self._top, abs(sample.speed))
        self._tilt = max(self._tilt, sample.tilt)
        if sample.margin is not None:
            self._margin = sample.margin if self._margin is None else min(self._margin, sample.margin)
        if sample.tip is not None:
            self._tip = sample.tip if self._tip is None else min(self._tip, sample.tip)

    def summary(self):
        if self._last is None:
            return RunSummary(touched=tuple(sorted(self._touched)))
        duration = self._last.time - self._first.time
        return RunSummary(
            duration=duration,
            distance=self._distance + dist(self._anchor, self._last.position[:2]),
            displacement=dist(self._first.position[:2], self._last.position[:2]),
            top_speed=self._top,
            max_tilt=self._tilt,
            saturated_share=self._saturated / duration if duration > 0 else 0.,
            slip_share=self._slipping / duration if duration > 0 else 0.,
            touched=tuple(sorted(self._touched)),
            min_margin=self._margin, min_tip=self._tip)
