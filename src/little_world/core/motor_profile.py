"""Portable, sourced motor endpoints; the derived envelope is an estimate."""
from dataclasses import dataclass
from math import isfinite,pi

ENVELOPES=('linear_estimate_v1','dc_friction_v1')


@dataclass(frozen=True)
class MotorProfile:
    model: str
    voltage: float
    stall_torque: float
    no_load_rpm: float
    source: str
    checked_on: str
    envelope: str = 'linear_estimate_v1'
    # Datasheet currents at `voltage`, in amperes. With both present the profile also
    # implies the motor's own friction: at no load the motor still draws current, and
    # the torque that current makes is exactly what its brushes, bearings and gearbox
    # consume. Referred to the output shaft that is stall_torque * I0 / (Is - I0);
    # gear ratio and efficiency cancel because stall torque is quoted at the output.
    no_load_current: float | None = None
    stall_current: float | None = None

    def __post_init__(self):
        for value in (self.voltage,self.stall_torque,self.no_load_rpm):
            if not isfinite(value) or value<=0:raise ValueError('Motor endpoints must be finite and positive')
        for value in (self.model,self.source,self.checked_on):
            if not isinstance(value,str) or not value.strip():raise ValueError('Profile needs model and source provenance')
        if self.envelope not in ENVELOPES:raise ValueError('Unsupported motor envelope')
        currents=(self.no_load_current,self.stall_current)
        if self.envelope=='dc_friction_v1':
            if any(c is None or not isfinite(c) for c in currents) or not 0<self.no_load_current<self.stall_current:
                raise ValueError('A friction envelope needs 0 < no-load current < stall current')
        elif any(c is not None for c in currents):
            raise ValueError('Currents are only used by the dc_friction_v1 envelope')

    @property
    def friction_torque(self):
        """Internal friction referred to the output shaft, N m; zero for linear_estimate_v1."""
        if self.envelope!='dc_friction_v1':return 0.
        return self.stall_torque*self.no_load_current/(self.stall_current-self.no_load_current)

    def weakened(self,torque=1.,speed=1.):
        """This motor with its own speed-torque line scaled - its stall torque by `torque`, its
        free speed by `speed` - and its friction as it was (ADR 0058): a winding grown hot has
        more resistance, so less stall current and torque at the same free speed; a sagging
        supply scales both. The returned profile's net endpoints are what the motor then
        delivers past its unchanged friction."""
        from dataclasses import replace
        for value in (torque,speed):
            if not isfinite(value) or not 0<value<=1:raise ValueError('A weakened motor keeps 0 to 1 of its torque and speed')
        if torque==1 and speed==1:return self
        stall,free=self.line()
        friction=self.friction_torque
        stall2,free2=stall*torque,free*speed
        net=stall2-friction
        if net<=0:raise ValueError('So weak a motor cannot turn past its own friction')
        rpm=free2*net/stall2*60/(2*pi)
        if self.envelope!='dc_friction_v1':
            return replace(self,stall_torque=stall2,no_load_rpm=free2*60/(2*pi))
        # The same no-load current and friction; the stall current the net stall torque implies.
        current=self.no_load_current+net*self.no_load_current/friction
        return replace(self,stall_torque=net,no_load_rpm=rpm,stall_current=current)

    def line(self):
        """The motor's own speed-torque line as (stall torque N m, free speed rad/s).

        It passes through both points. With friction both exceed the datasheet's, so
        that the net output - this line minus the friction - meets the datasheet."""
        friction=self.friction_torque
        stall=self.stall_torque+friction
        return stall,self.no_load_rpm*2*pi/60*stall/self.stall_torque

    def constrain(self,torque,velocity,operating_cap):
        """SI inputs. Directional drive envelope; simplified capped braking.

        linear_estimate_v1: the net torque falls linearly from stall torque to zero at
        no-load speed. dc_friction_v1: the same line for the motor's own torque, which
        is larger by the friction torque the joint then subtracts - so the net output
        still meets both datasheet endpoints (stall torque at rest, zero at no-load
        speed) instead of falling short of each by the friction.
        """
        for value in (torque,velocity,operating_cap):
            if not isfinite(value):raise ValueError('Motor inputs must be finite')
        if operating_cap<=0:raise ValueError('Operating cap must be positive')
        stall,free=self.line()
        direction=1 if torque>=0 else -1
        fraction=max(0.,1-max(0.,direction*velocity)/free)
        limit=min(operating_cap,stall*fraction)
        return direction*min(abs(torque),limit)

    def slope(self,torque,velocity,operating_cap,reach=0.):
        """d(delivered torque)/d(velocity) for an implicit integrator, N m s/rad.

        The line's slope, -stall/free, wherever the speed-torque line limits this
        command, or could within one step: `reach` is the most that step can add to
        the speed (rad/s). Zero where the torque is the command itself, the operating
        cap or nothing at all. Evaluating the line once per step instead overshoots
        whenever timestep * stall / (free * inertia) is above about 2, which a bare
        gearbox output shaft exceeds four-thousand-fold.
        """
        stall,free=self.line()
        direction=1 if torque>=0 else -1
        speed=direction*velocity
        wanted=min(abs(torque),operating_cap)
        if speed>=free or wanted==0:return 0.
        corner=free*(1-min(wanted,stall)/stall)  # the line meets the wanted torque here
        return -stall/free if speed+max(reach,0.)>=corner else 0.
