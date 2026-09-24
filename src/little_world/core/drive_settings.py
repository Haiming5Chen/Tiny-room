"""Portable drive-assistance settings in SI units."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class DriveSettings:
    max_speed: float = .425
    acceleration: float = .7
    torque_fraction: float = 1.
    gain: float = .3
    traction: bool = True

    def __post_init__(self):
        for name,lo,hi in (('max_speed',.01,5),('acceleration',.01,10),('torque_fraction',.05,1),('gain',.01,20)):
            v=getattr(self,name)
            if not isfinite(v) or not lo<=v<=hi:raise ValueError(f'{name} must be between {lo} and {hi}')
        if type(self.traction) is not bool:raise ValueError('traction must be true or false')
