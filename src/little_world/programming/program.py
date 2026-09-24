from dataclasses import dataclass,asdict
from math import isfinite
import json


@dataclass(frozen=True)
class Block:
    kind: str = 'wait'
    target: str = ''
    value: float = 0.
    duration: float = 1.
    other: str = ''
    secondary: float = 0.

    def __post_init__(self):
        if self.kind not in ('wait','action','drive','move','contact','distance','if_contact'):
            raise ValueError('Unsupported program block')
        if not isinstance(self.target,str) or not isinstance(self.other,str):raise ValueError('Block references must be names')
        if any(not isfinite(v) for v in (self.value,self.duration,self.secondary)):raise ValueError('Block numbers must be finite')
        if not .002<=self.duration<=120:raise ValueError('Duration / timeout must be 0.002 to 120 seconds')
        if self.kind=='action' and self.value not in (-1,1):raise ValueError('Direction must be -1 or 1')
        if self.kind=='drive' and max(abs(self.value),abs(self.secondary))>12:raise ValueError('Wheel targets must be within +/-12 rad/s')
        if self.kind=='distance' and self.value<0:raise ValueError('Distance must be nonnegative')


@dataclass(frozen=True)
class Program:
    blocks: tuple[Block,...] = ()
    repeat: int = 1
    trigger: str = 'F6'
    version: int = 1

    def __post_init__(self):
        object.__setattr__(self,'blocks',tuple(self.blocks))
        if self.version!=1 or type(self.version) is not int:raise ValueError('Unsupported program version')
        if type(self.repeat) is not int or not 1<=self.repeat<=100:raise ValueError('Repeat must be 1 to 100')
        if self.trigger not in ('F6','F7','F8'):raise ValueError('Trigger must be F6, F7 or F8')
        if len(self.blocks)>100 or any(not isinstance(b,Block) for b in self.blocks):raise ValueError('Program supports at most 100 blocks')

    def validate(self,blueprint,body_names=()):
        from little_world.core.component import Hinge,Motor,RobotServo
        specs={c.id:c for c in blueprint.controllers}
        parts={c.id:c for c in blueprint.components}
        for b in self.blocks:
            if b.kind in ('action','move'):
                if b.target not in specs or specs[b.target].kind!='keyboard_position':raise ValueError('Missing joint action: '+b.target)
                if b.kind=='move':
                    for name in specs[b.target].actuators:
                        if isinstance(parts[name],RobotServo):
                            from math import degrees
                            from little_world.assets.robot_models import metadata
                            channel=parts[name].channel
                            limits=(0,100) if channel==7 else tuple(degrees(x) for x in metadata(parts[parts[name].body].robot_asset)['limits'][channel])
                        else:limits=parts[parts[name].joint].limits
                        if not limits[0]<=b.value<=limits[1]:raise ValueError('Target angle exceeds joint limits')
            if b.kind=='drive' and not any(c.kind=='differential_torque' and len(c.actuators)==2 for c in specs.values()):raise ValueError('Program needs a two-wheel drive controller')
            if b.kind in ('contact','distance','if_contact'):
                if b.target not in body_names or b.other not in body_names:raise ValueError('Missing sensor body reference')
                if b.target==b.other:raise ValueError('Choose two different bodies')

    def to_json(self):return json.dumps(asdict(self),indent=2,allow_nan=False)

    @classmethod
    def from_json(cls,text):
        data=json.loads(text)
        if set(data)!={'blocks','repeat','trigger','version'}:raise ValueError('Invalid program fields')
        return cls(tuple(Block(**b) for b in data['blocks']),data['repeat'],data['trigger'],data['version'])


class Runner:
    def __init__(self):self.stop()
    def stop(self):
        self.state='stopped';self.index=0;self.elapsed=0.;self.cycle=0;self.single=False;self.message='Stopped'
    def start(self,program,single=False):
        if not program.blocks:raise ValueError('Add a program block first')
        self.stop();self.program=program;self.state='running';self.single=single;self.message='Running'
    def advance(self,skip=1):
        self.elapsed=0.;self.index+=skip
        if self.index>=len(self.program.blocks):
            self.cycle+=1
            if self.cycle>=self.program.repeat:self.state='completed';self.message='Completed';return
            self.index=0
        if self.single:self.state='paused';self.message='Step complete'
    def tick(self,dt,angles=None,contacts=(),distances=None):
        if not isfinite(dt) or dt<=0:raise ValueError('Timestep must be positive')
        output={'action':None,'drive':(0.,0.),'move':None}
        if self.state!='running':return output
        b=self.program.blocks[self.index];self.elapsed+=dt
        if b.kind=='action':output['action']=(b.target,b.value)
        elif b.kind=='drive':output['drive']=(b.value,b.secondary)
        elif b.kind=='move':output['move']=(b.target,b.value)
        condition=False
        if b.kind=='move':condition=bool((angles or {}).get(b.target)) and all(abs(v-b.value)<=2 for v in angles[b.target])
        elif b.kind in ('contact','if_contact'):condition=frozenset((b.target,b.other)) in contacts
        elif b.kind=='distance':condition=(distances or {}).get((b.target,b.other),float('inf'))<=b.value
        if b.kind=='if_contact':self.advance(1 if condition else 2)
        elif b.kind in ('move','contact','distance'):
            if condition:self.advance()
            elif self.elapsed+1e-9>=b.duration:self.state='failed';self.message='Timed out: '+b.kind+' '+b.target
        elif self.elapsed+1e-9>=b.duration:self.advance()
        return output
