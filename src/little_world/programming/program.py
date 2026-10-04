from dataclasses import dataclass,asdict
from math import isfinite
import json

KINDS=('wait','action','drive','move','contact','distance','if_contact','pose','grasp','goto','look')
# Blocks a version-1 reader does not know: a program that uses them is written as version 2,
# which such a reader refuses instead of misreading (ADR 0016); a look, as version 3 (ADR 0032).
VERSION_2_KINDS=('pose','grasp','goto')
VERSION_3_KINDS=('look',)
SETTLE=2.   # degrees: a joint this close to its target has arrived
CORRECTIONS=2   # times an aimed pose is solved again for where the tool actually got to
REAPPROACH=.02  # m: an aimed pose settling this far from the stop its machine drove to goes back to it (ADR 0031)
RETRIES=1       # times a program may go back to a stop
RUN_UP=.25      # m: going back, the machine first backs off this far behind the stop, then drives in straight
PICTURE=.1      # s between a look's pictures (ADR 0032)
STEADY=3        # a look ends once this many pictures in a row have seen its object in one place:
STILL=.005      # m: within this of where they saw it, together
NEAR=.15        # m: a look re-aims the poses at its stop aimed within this of where its object was planned
SHIFT=.005      # m: seen further than this from the plan, those poses are solved for it before they move


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
    # goto: (x, y) in metres in the field's frame, or (x, y, heading in degrees). The
    # base's drive axle midpoint is brought within `value` metres of it (0: 1 cm),
    # then turned to the heading; `duration` is the timeout (ADR 0017).
    # pose, optionally: (x, y, z), the point in the field's frame its tool was aimed at when
    # the angles were solved. A runner given an aim moves the joints there, then solves the
    # pose again for where the machine actually stands until the tool is at the point
    # (ADR 0025); without an aim, or without a point, the angles are the pose.
    # look: (x, y, z), where its object - `target` - was planned to be. The runner's camera
    # looks for it for `value` seconds, a picture every PICTURE, until STEADY pictures in a row
    # agree; the poses at this stop aimed near it are then aimed where it was seen (ADR 0032).
    # `duration` is the timeout.
    point: tuple = ()

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError('Unsupported program block')
        if not isinstance(self.target,str) or not isinstance(self.other,str):raise ValueError('Block references must be names')
        if any(not isfinite(v) for v in (self.value,self.duration,self.secondary)):raise ValueError('Block numbers must be finite')
        if not .002<=self.duration<=120:raise ValueError('Duration / timeout must be 0.002 to 120 seconds')
        if self.kind=='action' and self.value not in (-1,1):raise ValueError('Direction must be -1 or 1')
        if self.kind=='drive' and max(abs(self.value),abs(self.secondary))>12:raise ValueError('Wheel targets must be within +/-12 rad/s')
        if self.kind=='distance' and self.value<0:raise ValueError('Distance must be nonnegative')
        if self.kind=='look':
            if not self.target:raise ValueError('A look names the object it looks for')
            if not 0<=self.value<=10:raise ValueError('A look watches for 0 to 10 seconds')
            if self.duration<self.value+PICTURE:raise ValueError('A look needs a timeout longer than it watches')
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
        try:
            point=tuple(float(v) for v in self.point)
        except (TypeError,ValueError):
            raise ValueError('A goto point is (x, y) or (x, y, heading)') from None
        object.__setattr__(self,'point',point)
        if self.kind=='goto':
            if len(point) not in (2,3) or any(not isfinite(v) for v in point):raise ValueError('A goto point is (x, y) or (x, y, heading)')
            if any(abs(v)>100 for v in point[:2]):raise ValueError('A goto point must be within 100 m')
            if self.value and not .002<=self.value<=.5:raise ValueError('Goto tolerance must be 0.002 to 0.5 m (0: 1 cm)')
        elif self.kind=='look' or self.kind=='pose' and point:
            if len(point)!=3 or any(not isfinite(v) for v in point):
                raise ValueError('A look needs where its object was planned (x, y, z)' if self.kind=='look' else 'A pose is aimed at a point (x, y, z)')
            if any(abs(v)>100 for v in point):raise ValueError('A pose point must be within 100 m')
        elif point:
            raise ValueError('Only a goto, a pose or a look carries a point')


@dataclass(frozen=True)
class Program:
    blocks: tuple[Block,...] = ()
    repeat: int = 1
    trigger: str = 'F6'
    version: int = 1

    def __post_init__(self):
        object.__setattr__(self,'blocks',tuple(self.blocks))
        if type(self.version) is not int or self.version not in (1,2,3):raise ValueError('Unsupported program version')
        if type(self.repeat) is not int or not 1<=self.repeat<=100:raise ValueError('Repeat must be 1 to 100')
        if self.trigger not in ('F6','F7','F8'):raise ValueError('Trigger must be F6, F7 or F8')
        if len(self.blocks)>100 or any(not isinstance(b,Block) for b in self.blocks):raise ValueError('Program supports at most 100 blocks')
        if any(b.kind in VERSION_2_KINDS for b in self.blocks):object.__setattr__(self,'version',max(self.version,2))
        if any(b.kind in VERSION_3_KINDS for b in self.blocks):object.__setattr__(self,'version',3)

    def validate(self,blueprint,body_names=()):
        from little_world.core.component import RobotServo
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
            if b.kind=='look' and b.target not in body_names:raise ValueError('Missing object to look for: '+b.target)
            if b.kind=='goto' and not any(c.kind=='differential_torque' and len(c.actuators)>=2 for c in specs.values()):raise ValueError('Driving to a point needs a two-wheel drive controller')

    def to_json(self):
        data=asdict(self)
        for block in data['blocks']:
            for key in ('angles','point'):
                if not block[key]:del block[key]   # version-1 files stay exactly as they were
        return json.dumps(data,indent=2,allow_nan=False)

    @classmethod
    def from_json(cls,text):
        data=json.loads(text)
        if set(data)!={'blocks','repeat','trigger','version'}:raise ValueError('Invalid program fields')
        if data['version']==1 and any('angles' in b or 'point' in b for b in data['blocks']):raise ValueError('Invalid program fields')
        return cls(tuple(Block(**b) for b in data['blocks']),data['repeat'],data['trigger'],data['version'])


def smoothstep(s):
    """0 to 1 with zero speed at both ends: joints start and stop without a jolt."""
    s=max(0.,min(1.,s))
    return s*s*(3-2*s)


class Runner:
    def __init__(self,corrections=CORRECTIONS,retries=RETRIES):
        # How often an aimed pose may be solved again (ADR 0025); 0 runs poses as taught.
        # How often a program may go back to a stop it was pushed off (ADR 0031); 0 never.
        if corrections<0 or retries<0:raise ValueError('corrections and retries are counted from zero')
        self.limit=corrections;self.retry_limit=retries;self.stop()
    def stop(self):
        self.state='stopped';self.index=0;self.elapsed=0.;self.cycle=0;self.single=False;self.message='Stopped'
        self.pose_from=None;self.pose_goal=None;self.corrections=0;self.driver=None
        self.retries=0;self.stop_at=None;self.stop_block=None;self.run_up=None
        self.sightings=[];self.picture_at=0.;self.offset=None;self.looked=None;self.seen=[]
    def start(self,program,single=False):
        if not program.blocks:raise ValueError('Add a program block first')
        self.stop();self.program=program;self.state='running';self.single=single;self.message='Running'
    def advance(self,skip=1):
        self.elapsed=0.;self.index+=skip;self.pose_from=None;self.pose_goal=None;self.corrections=0;self.driver=None
        self.sightings=[];self.picture_at=0.
        if self.index>=len(self.program.blocks):
            self.cycle+=1
            if self.cycle>=self.program.repeat:self.state='completed';self.message='Completed';return
            self.index=0
        if self.single:self.state='paused';self.message='Step complete'
    def fail(self,message):
        self.state='failed';self.message=message
    def off_stop(self,base):
        """How far the base is from the stop its last goto brought it to, when that is more
        than REAPPROACH and a retry is left; else None."""
        if self.stop_at is None or base is None or self.retries>=self.retry_limit:return None
        off=((base[0]-self.stop_at[0])**2+(base[1]-self.stop_at[1])**2)**.5
        return off if off>REAPPROACH else None
    def reapproach(self,off):
        """Pushed off its stop, the machine goes back to it the way it came - the pose it
        drove in, if one came just before the goto, then the goto - and takes its aimed pose
        again from where the pose was planned (ADR 0031)."""
        from math import cos,radians,sin
        blocks=self.program.blocks;start=self.stop_block;stop=blocks[start].point
        # Come in along the stop's own heading, as the first approach did: from the side, a
        # drive to a point accepts a few centimetres across its line (ADR 0018).
        if len(stop)>2:
            heading=radians(stop[2]);self.run_up=(stop[0]-RUN_UP*cos(heading),stop[1]-RUN_UP*sin(heading))
        if start>0 and blocks[start-1].kind=='pose':start-=1
        self.retries+=1;self.message=f'Pushed {100*off:.0f} cm off its stop: going back'
        self.elapsed=0.;self.index=start;self.pose_from=None;self.pose_goal=None;self.corrections=0;self.driver=None
        self.sightings=[];self.picture_at=0.;self.offset=None;self.looked=None
    def aimed(self,block):
        """Where a pose is aimed: its point, or - near where a look at this stop expected its
        object - its point moved as far as the object was seen to be from there (ADR 0032)."""
        if not block.point or self.offset is None:return block.point
        if sum((p-q)**2 for p,q in zip(block.point,self.looked))>NEAR**2:return block.point
        return tuple(p+o for p,o in zip(block.point,self.offset))
    def look(self,block,see):
        """A look's next picture, when one is due; True once STEADY pictures in a row have
        seen its object within STILL of their middle, after it has watched `value` seconds."""
        if self.elapsed+1e-9>=self.picture_at:
            self.picture_at+=PICTURE
            sighting=see(block.target,block.point)
            self.sightings.append(None if sighting is None else tuple(float(v) for v in sighting.centre))
        last=self.sightings[-STEADY:]
        if self.elapsed+1e-9<block.value or len(last)<STEADY or None in last:return False
        middle=tuple(sorted(v[i] for v in last)[STEADY//2] for i in range(3))
        if any(sum((a-b)**2 for a,b in zip(v,middle))>STILL**2 for v in last):return False
        self.offset=tuple(a-b for a,b in zip(middle,block.point));self.looked=block.point
        self.seen.append((block.target,block.point,middle))
        return True
    def travel(self,block):
        """Seconds a pose's slowest joint needs at the pose's speed, from where it started."""
        goal=self.pose_goal or block.angles
        return max((abs(g-s) for a,target in goal for s,g in zip(self.pose_from[a],target)),default=0.)/block.value
    def tick(self,dt,angles=None,contacts=(),distances=None,held=frozenset(),base=None,aim=None,see=None):
        """One step of simulated time. `angles`: joint action -> current angles (degrees);
        `held`: names of the objects a gripper holds between both jaws; `base`: the drive
        base's (x, y, yaw radians), for goto blocks; `aim(point, pose)`: for a pose aimed at a
        point, None when the tool is there, else the pose solved again for where the machine
        now stands (ADR 0025); `see(object, planned)`: a camera's picture of an object planned
        at `planned`, something with its `centre` where it was seen, or None (ADR 0032)."""
        if not isfinite(dt) or dt<=0:raise ValueError('Timestep must be positive')
        output={'action':None,'drive':(0.,0.),'move':None,'pose':None,'base':None}
        if self.state!='running':return output
        b=self.program.blocks[self.index];self.elapsed+=dt
        if b.kind=='action':output['action']=(b.target,b.value)
        elif b.kind=='drive':output['drive']=(b.value,b.secondary);self.offset=None
        elif b.kind=='move':output['move']=(b.target,b.value)
        elif b.kind=='pose':
            angles=angles or {}
            if self.pose_from is None:
                missing=[a for a,_ in b.angles if a not in angles]
                if missing:self.fail('Missing joint for pose: '+missing[0]);return output
                self.pose_from={a:tuple(angles[a])[:len(goal)] for a,goal in b.angles}
                self.pose_goal=b.angles
                # Its object was seen elsewhere: solve the pose for there before moving.
                if aim is not None and self.aimed(b)!=b.point and sum(v*v for v in self.offset)>SHIFT**2:
                    better=aim(self.aimed(b),b.angles)
                    if better:self.pose_goal=tuple(better)
            travel=self.travel(b)
            u=smoothstep(self.elapsed/travel) if travel>0 else 1.
            output['pose']={a:tuple(s+(g-s)*u for s,g in zip(self.pose_from[a],goal)) for a,goal in self.pose_goal}
        elif b.kind=='goto':
            if base is None:self.fail('No drive base to drive to a point');return output
            if self.driver is None:
                from math import radians
                from little_world.control.navigation import GoTo
                self.offset=None            # a new stop: what was seen at the last one is behind it
                if self.run_up and self.index==self.stop_block:
                    self.driver=GoTo(self.run_up,None,.03)
                else:
                    self.driver=GoTo(b.point[:2],radians(b.point[2]) if len(b.point)>2 else None,b.value or .01)
            forward,turn,arrived=self.driver.step(base)
            output['base']=(forward,turn)
            if arrived and self.run_up and self.index==self.stop_block and self.driver.goal==tuple(self.run_up):
                self.run_up=None;self.driver=None;arrived=False      # backed off: now in to the stop
            elif arrived:self.stop_at=b.point[:2];self.stop_block=self.index
        condition=False
        if b.kind=='move':condition=bool((angles or {}).get(b.target)) and all(abs(v-b.value)<=SETTLE for v in angles[b.target])
        elif b.kind=='pose':
            condition=self.elapsed+1e-9>=self.travel(b) and all(
                a in angles and all(abs(v-g)<=SETTLE for v,g in zip(angles[a],goal)) for a,goal in self.pose_goal)
        elif b.kind in ('contact','if_contact'):condition=frozenset((b.target,b.other)) in contacts
        elif b.kind=='distance':condition=(distances or {}).get((b.target,b.other),float('inf'))<=b.value
        elif b.kind=='grasp':condition=(b.target in held) if b.target else bool(held)
        elif b.kind=='goto':condition=arrived
        elif b.kind=='look':
            if see is None:self.fail('No camera to look with');return output
            condition=self.look(b,see)
        if b.kind=='if_contact':self.advance(1 if condition else 2)
        elif b.kind in ('move','contact','distance','grasp','goto'):
            if condition:self.advance()
            elif self.elapsed+1e-9>=b.duration:
                self.fail('Nothing held: the grasp missed' if b.kind=='grasp' else 'Timed out: '+b.kind+' '+b.target)
        elif b.kind=='look':
            if condition:self.advance()
            elif self.elapsed+1e-9>=b.duration:
                name=b.target.split('/')[-1]
                self.fail(f'Looked for {name}: not found' if not any(self.sightings) else f'Looked for {name}: it would not keep still')
        elif b.kind=='pose':
            off=self.off_stop(base) if condition and b.point else None
            if off:self.reapproach(off)
            elif condition:
                # Aimed at a point: arrived where the joints were sent, is the tool there?
                better=aim(self.aimed(b),self.pose_goal) if b.point and aim is not None and self.corrections<self.limit else None
                if better:
                    self.corrections+=1;self.elapsed=0.;self.pose_goal=tuple(better)
                    self.pose_from={a:tuple(angles.get(a,goal))[:len(goal)] for a,goal in self.pose_goal}
                else:self.advance()
            elif self.elapsed+1e-9>=self.travel(b)+b.duration:
                # A correction that cannot settle keeps what the joints reached; the pose itself
                # settled before it, so the program goes on. A pose that cannot settle because
                # its machine was pushed off its stop goes back to the stop (ADR 0031).
                off=self.off_stop(base) if b.point else None
                if self.corrections:self.advance()
                elif off:self.reapproach(off)
                else:self.fail('Timed out: pose did not settle')
        elif self.elapsed+1e-9>=b.duration:self.advance()
        return output
