"""Portable, sourced motor endpoints; the derived envelope is an estimate."""
from dataclasses import dataclass
from math import isfinite,pi


@dataclass(frozen=True)
class MotorProfile:
    model: str
    voltage: float
    stall_torque: float
    no_load_rpm: float
    source: str
    checked_on: str
    envelope: str = 'linear_estimate_v1'

    def __post_init__(self):
        for value in (self.voltage,self.stall_torque,self.no_load_rpm):
            if not isfinite(value) or value<=0:raise ValueError('Motor endpoints must be finite and positive')
        for value in (self.model,self.source,self.checked_on):
            if not isinstance(value,str) or not value.strip():raise ValueError('Profile needs model and source provenance')
        if self.envelope!='linear_estimate_v1':raise ValueError('Unsupported motor envelope')

    def constrain(self,torque,velocity,operating_cap):
        """SI inputs. Directional drive envelope; simplified capped braking."""
        for value in (torque,velocity,operating_cap):
            if not isfinite(value):raise ValueError('Motor inputs must be finite')
        if operating_cap<=0:raise ValueError('Operating cap must be positive')
        direction=1 if torque>=0 else -1
        fraction=max(0.,1-max(0.,direction*velocity)/(self.no_load_rpm*2*pi/60))
        limit=min(operating_cap,self.stall_torque*fraction)
        return direction*min(abs(torque),limit)
