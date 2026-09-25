from dataclasses import dataclass,asdict
from math import isfinite
import json

KINDS=('wait','action','drive','move','contact','distance','if_contact','pose','grasp')
# Blocks a version-1 reader does not know: a program that uses them is written as version 2,
# which such a reader refuses instead of misreading (ADR 0016).
VERSION_2_KINDS=('pose','grasp')
SETTLE=2.   # degrees: a joint this close to its target has arrived


@dataclass(frozen=True)
class Block:
    kind: str = 'wait'
    target: str = ''
    value: float = 0.
    duration: float = 1.
    other: str = ''
    secondary: float = 0.
    # pose: ((joint action id, (degrees per actuator, ...)), ...). The joints move together
    # and arrive together at up to `value` degrees per second; `duration` is how long they
    # may take to settle after that before the block fails.
    angles: tuple = ()

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError('Unsupported program block')
        if not isinstance(self.target,str) or not isinstance(self.other,str):raise ValueError('Block references must be names')
        if any(not isfinite(v) for v in (self.value,self.duration,self.secondary)):raise ValueError('Block numbers must be finite')
        if not .002<=self.duration<=120:raise ValueError('Duration / timeout must be 0.002 to 120 seconds')
        if self.kind=='action' and self.value not in (-1,1):raise ValueError('Direction must be -1 or 1')
        if self.kind=='drive' and max(abs(self.value),abs(self.secondary))>12:raise ValueError('Wheel targets must be within +/-12 rad/s')
        if self.kind=='distance' and self.value<0:raise ValueError('Distance must be nonnegative')
        try:
            angles=tuple((str(a) if isinstance(a,str) else None,tuple(float(v) for v in values)) for a,values in self.angles)
        except (TypeError,ValueError):
            raise ValueError('Pose angles must be (joint action, degrees) pairs') from None
        object.__setattr__(self,'angles',angles)
        if self.kind=='pose':
            if not angles:raise ValueError('A pose needs at least one joint action')
            if any(a is None or not values for a,values in angles):raise ValueError('Pose angles must name a joint action and give its angles')
            if len({a for a,_ in angles})!=len(angles):raise ValueError('A joint action appears twice in the pose')
            if any(not isfinite(v) for _,values in angles for v in values):raise ValueError('Pose angles must be finite')
            if not 1<=self.value<=180:raise ValueError('Pose speed must be 1 to 180 degrees per second')
        elif angles:
            raise ValueError('Only a pose block carries joint angles')


@dataclass(frozen=True)
class Program:
    blocks: tuple[Block,...] = ()
    repeat: int = 1
    trigger: str = 'F6'
    version: int = 1

    def __post_init__(self):
        object.__setattr__(self,'blocks',tuple(self.blocks))
        if type(self.version) is not int or self.version not in (1,2):raise ValueError('Unsupported program version')
        if type(self.repeat) is not int or not 1<=self.repeat<=100:raise ValueError('Repeat must be 1 to 100')
        if self.trigger not in ('F6','F7','F8'):raise ValueError('Trigger must be F6, F7 or F8')
        if len(self.blocks)>100 or any(not isinstance(b,Block) for b in self.blocks):raise ValueError('Program supports at most 100 blocks')
        if any(b.kind in VERSION_2_KINDS for b in self.blocks):object.__setattr__(self,'version',2)

    def validate(self,blueprint,body_names=()):
        from little_world.core.component import Hinge,Motor,RobotServo
        specs={c.id:c for c in blueprint.controllers}
        parts={c.id:c for c in blueprint.components}

        def limits(name):
            if isinstance(parts[name],RobotServo):
                from math import degrees
                from little_world.assets.robot_models import metadata
                channel=parts[name].channel
                return (0,100) if channel==7 else tuple(degrees(x) for x in metadata(parts[parts[name].body].robot_asset)['limits'][channel])
            return parts[parts[name].joint].limits
        for b in self.blocks:
            if b.kind in ('action','move'):
                if b.target not in specs or specs[b.target].kind!='keyboard_position':raise ValueError('Missing joint action: '+b.target)
                if b.kind=='move':
                    for name in specs[b.target].actuators:
                        low,high=limits(name) or (-180.,180.)
                        if not low<=b.value<=high:raise ValueError('Target angle exceeds joint limits')
            if b.kind=='pose':
                for action,values in b.angles:
                    if action not in specs or specs[action].kind!='keyboard_position':raise ValueError('Missing joint action: '+action)
                    if len(values)!=len(specs[action].actuators):raise ValueError('Pose gives '+str(len(values))+' angles for '+action)
                    for name,value in zip(specs[action].actuators,values):
                        low,high=limits(name) or (-180.,180.)
                        if not low-1e-6<=value<=high+1e-6:raise ValueError('Pose angle exceeds joint limits: '+action)
            if b.kind=='drive' and not any(c.kind=='differential_torque' and len(c.actuators)==2 for c in specs.values()):raise ValueError('Program needs a two-wheel drive controller')
            if b.kind in ('contact','distance','if_contact'):
                if b.target not in body_names or b.other not in body_names:raise ValueError('Missing sensor body reference')
                if b.target==b.other:raise ValueError('Choose two different bodies')
            if b.kind=='grasp' and b.target and b.target not in body_names:raise ValueError('Missing object to grasp: '+b.target)

    def to_json(self):
        data=asdict(self)
        for block in data['blocks']:
            if not block['angles']:del block['angles']   # version-1 files stay exactly as they were
        return json.dumps(data,indent=2,allow_nan=False)

    @classmethod
    def from_json(cls,text):
        data=json.loads(text)
        if set(data)!={'blocks','repeat','trigger','version'}:raise ValueError('Invalid program fields')
        if data['version']==1 and any('angles' in b for b in data['blocks']):raise ValueError('Invalid program fields')
        return cls(tuple(Block(**b) for b in data['blocks']),data['repeat'],data['trigger'],data['version'])


def smoothstep(s):
    """0 to 1 with zero speed at both ends: joints start and stop without a jolt."""
    s=max(0.,min(1.,s))
    return s*s*(3-2*s)


class Runner:
    def __init__(self):self.stop()
    def stop(self):
        self.state='stopped';self.index=0;self.elapsed=0.;self.cycle=0;self.single=False;self.message='Stopped'
        self.pose_from=None
    def start(self,program,single=False):
        if not program.blocks:raise ValueError('Add a program block first')
        self.stop();self.program=program;self.state='running';self.single=single;self.message='Running'
    def advance(self,skip=1):
        self.elapsed=0.;self.index+=skip;self.pose_from=None
        if self.index>=len(self.program.blocks):
            self.cycle+=1
            if self.cycle>=self.program.repeat:self.state='completed';self.message='Completed';return
            self.index=0
        if self.single:self.state='paused';self.message='Step complete'
    def fail(self,message):
        self.state='failed';self.message=message
    def travel(self,block):
        """Seconds a pose's slowest joint needs at the pose's speed, from where it started."""
        return max((abs(g-s) for a,goal in block.angles for s,g in zip(self.pose_from[a],goal)),default=0.)/block.value
    def tick(self,dt,angles=None,contacts=(),distances=None,held=frozenset()):
        """One step of simulated time. `angles`: joint action -> current angles (degrees);
        `held`: names of the objects a gripper holds between both jaws."""
        if not isfinite(dt) or dt<=0:raise ValueError('Timestep must be positive')
        output={'action':None,'drive':(0.,0.),'move':None,'pose':None}
        if self.state!='running':return output
        b=self.program.blocks[self.index];self.elapsed+=dt
        if b.kind=='action':output['action']=(b.target,b.value)
        elif b.kind=='drive':output['drive']=(b.value,b.secondary)
        elif b.kind=='move':output['move']=(b.target,b.value)
        elif b.kind=='pose':
            angles=angles or {}
            if self.pose_from is None:
                missing=[a for a,_ in b.angles if a not in angles]
                if missing:self.fail('Missing joint for pose: '+missing[0]);return output
                self.pose_from={a:tuple(angles[a])[:len(goal)] for a,goal in b.angles}
            travel=self.travel(b)
            u=smoothstep(self.elapsed/travel) if travel>0 else 1.
            output['pose']={a:tuple(s+(g-s)*u for s,g in zip(self.pose_from[a],goal)) for a,goal in b.angles}
        condition=False
        if b.kind=='move':condition=bool((angles or {}).get(b.target)) and all(abs(v-b.value)<=SETTLE for v in angles[b.target])
        elif b.kind=='pose':
            condition=self.elapsed+1e-9>=self.travel(b) and all(
                a in angles and all(abs(v-g)<=SETTLE for v,g in zip(angles[a],goal)) for a,goal in b.angles)
        elif b.kind in ('contact','if_contact'):condition=frozenset((b.target,b.other)) in contacts
        elif b.kind=='distance':condition=(distances or {}).get((b.target,b.other),float('inf'))<=b.value
        elif b.kind=='grasp':condition=(b.target in held) if b.target else bool(held)
        if b.kind=='if_contact':self.advance(1 if condition else 2)
        elif b.kind in ('move','contact','distance','grasp'):
            if condition:self.advance()
            elif self.elapsed+1e-9>=b.duration:
                self.fail('Nothing held: the grasp missed' if b.kind=='grasp' else 'Timed out: '+b.kind+' '+b.target)
        elif b.kind=='pose':
            if condition:self.advance()
            elif self.elapsed+1e-9>=self.travel(b)+b.duration:self.fail('Timed out: pose did not settle')
        elif self.elapsed+1e-9>=b.duration:self.advance()
        return output
