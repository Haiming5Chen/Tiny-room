"""Panda-only top-down manipulation using native IK and real contact grasps.

Where each part is comes from the simulator's state (known-object sensing) or from the cell's
overhead depth camera (ADR 0069), which never reads the part's pose. This fixed-cell waypoint
planner is not a general obstacle-avoidance or grasp-planning system.
"""
from dataclasses import dataclass
import numpy as np
import mujoco as mj
from .scene import TABLE
from little_world.fields.conveyor import PALLET
from little_world.programming.observations import Observations

@dataclass
class Stage:
    label:str
    target:np.ndarray
    grip:float
    duration:float
    point:np.ndarray
    path:np.ndarray|None=None   # joint solutions STEP apart along the straight line to `point` (ADR 0057)

# The stages that move the tool straight up or down. Moved joint by joint the tool swings off the
# vertical - lowering into the destination tray up to 15 mm halfway down - and a tall part's
# bottom caught the part beside it (ADR 0056, OPEN LW-037); along their line, joint solutions a
# centimetre apart keep it on the vertical.
LINES=('Lower to grasp','Lift and check grasp','Lower into bin','Retract')
STEP=.01        # m between joint solutions along a line
HAND_OPEN=.04   # m each Panda finger travels at the hand's widest, control 255 (Menagerie's hand)
SETTLE=.1       # s a pallet rests at the conveyor's stop before its part is picked (ADR 0068)
CLEAR=.008      # m each finger opens past a part to let it go: fully open (80 mm), a finger
                # reached the next tall part's top (ADR 0056)

# Where successive parts go in the destination tray: two rows along the fingers' closing
# direction, so an open hand lowering a part clears the parts already there (ADR 0019).
SLOTS=((0.,-.035),(0.,.035),(-.045,-.035),(-.045,.035),(.045,-.035),(.045,.035))
CAMERA='factory/overhead'   # the cell's camera, over the input tray's place


def camera_eye(backend,scene,seed=0,ideal=False):
    """The cell's overhead camera as a depth camera that finds its parts (ADR 0069): an Intel
    RealSense D435's pixels and noise (ADR 0032) from where the scene's camera is, knowing the
    sizes of the parts the scene has - as a lab knows the parts it picks."""
    from little_world.perception.eye import Eye,sizes_in
    from little_world.perception.sensors import REALSENSE_D435
    return Eye(backend,CAMERA,REALSENSE_D435,sizes_in(scene),seed,ideal)


class FactoryCycle:
    def __init__(self,backend,source='input',line=None,eye=None):
        """The cell's controller on `backend`'s model; `line` the roller conveyor that feeds the
        source when it does (a fields.conveyor.Line, ADR 0068), its stop the source's place; `eye`
        the cell's camera (`camera_eye`) when it finds the parts, else the state is read (ADR 0069)."""
        from .recipe import TRAYS
        if source not in TRAYS:raise ValueError('Unknown source tray')
        self.source=source;self.line=line;self.eye=eye
        self.sightings=[]   # with the camera: (part, where it was seen, where it was, seen turn, its turn) - the truth kept for the record only
        self.provisional=False  # a plan made before the camera could see the part: the arm clears its view first
        self.backend=backend;self.model=backend.model;self.data=backend.data
        self.prefix='machine/root__robot_'
        self.hand=self.model.body(self.prefix+'hand').id
        self.qids=np.array([self.model.jnt_qposadr[self.model.joint(self.prefix+'joint'+str(i)).id] for i in range(1,8)])
        self.dofs=np.array([self.model.jnt_dofadr[self.model.joint(self.prefix+'joint'+str(i)).id] for i in range(1,8)])
        self.limits=np.array([self.model.jnt_range[self.model.joint(self.prefix+'joint'+str(i)).id] for i in range(1,8)])
        self.product='objects/product'
        self.object_id=self.model.body(self.product).id
        self.slot=(0.,0.)
        self.run=None   # a production run in progress, or None
        self.feeder=None    # where the feeder puts part i: i -> (dx, dy in m, turn in deg) off the tray's centre, or None
        self.placement=None # the last part placed, as it was left: a process.Placement (ADR 0056)
        # The trays the scene has: fed by the conveyor, its stop is the source's place (ADR 0068).
        self.trays={name:self.data.xpos[self.model.body('factory/'+name+'_base').id][:2].copy() for name in TRAYS
                    if mj.mj_name2id(self.model,mj.mjtObj.mjOBJ_BODY,'factory/'+name+'_base')>=0}
        if line is not None:self.bind_line(line)
        self.scratch=mj.MjData(self.model)
        self.state='idle';self.message='Select a product and output tray, then Preview path.'
        self.stages=[];self.index=0;self.elapsed=0.;self.total=0.;self.lift_verified=False
        self.observations=Observations(self.model,self.data)
        self.local_tool=np.array((0.,0.,.103))

    # -- the roller conveyor that feeds the source, when it does (ADR 0068) ------------------

    def bind_line(self,line):
        from little_world.fields.conveyor import ROLLERS
        self.trays[self.source]=np.array((line.at_stop(1),line.start[1]))
        self.rollers=np.array([self.model.jnt_dofadr[self.model.joint(f'{line.entity}/roller_{i}_hinge').id] for i in range(ROLLERS)])
        self.pallets=[]
        while mj.mj_name2id(self.model,mj.mjtObj.mjOBJ_BODY,'objects/pallet_'+str(len(self.pallets)+1))>=0:
            self.pallets.append('objects/pallet_'+str(len(self.pallets)+1))
        # Which part rides on which pallet: the part resting over its centre.
        self.carrier={}
        for pallet in self.pallets:
            at=self.data.xpos[self.model.body(pallet).id]
            for b in range(self.model.nbody):
                name=self.model.body(b).name
                if name.startswith('objects/product') and np.linalg.norm(self.data.xpos[b][:2]-at[:2])<.04 and self.data.xpos[b][2]>at[2]:
                    self.carrier[name]=pallet
        self.waited=0.;self.settled=0.

    def belt(self):
        """The conveyor's rollers held at its speed, every step, the cell running or not."""
        return {} if self.line is None else self.line.torques(self.data.qvel[self.rollers])

    def free(self,body):
        """(qpos address, dof address) of a loose body's free joint."""
        joint=self.model.body_jntadr[self.model.body(body).id]
        return self.model.jnt_qposadr[joint],self.model.jnt_dofadr[joint]

    def resting_at_stop(self):
        """Whether the pallet carrying the current part rests at the stop, and the part on it."""
        pallet=self.carrier.get(self.product)
        if pallet is None:return False
        x,y,_=self.data.xpos[self.model.body(pallet).id]
        if abs(x-self.line.at_stop(1))>.002 or abs(y-self.line.start[1])>.01:return False
        return all(np.linalg.norm(self.data.qvel[dof:dof+3])<.002 for dof in (self.free(pallet)[1],self.free(self.product)[1]))

    def arrived(self,dt):
        """Waiting for the current part: once its pallet has rested at the stop for SETTLE, its pick
        is planned and started, and where it arrived is noted - mm from the pallet's place there."""
        self.waited+=dt
        self.settled=self.settled+dt if self.resting_at_stop() else 0.
        if self.settled<SETTLE:
            if self.waited>12.:self.fail('The next pallet did not reach the stop.')
            return
        pos=self.data.xpos[self.object_id]
        if self.run is not None:
            self.run['arrivals'].append((1000*float(pos[0]-self.line.at_stop(1)),1000*float(pos[1]-self.line.start[1]),self.waited))
        self.state='idle';self.plan(self.run['destination'] if self.run is not None else self.destination);self.start()
        if self.run is not None:self.message=f"Part {self.run['done']+1} of {len(self.run['parts'])}: "+self.step_label()

    def send_back(self):
        """The current part is off its pallet: unless it was the run's last, the pallet goes back
        to the line's start - with the next part waiting on the shelf on it, if one does - and the
        pallet behind rides up to the stop. The return and the loading are a person's, not
        simulated: one move."""
        pallet=self.carrier.pop(self.product,None);run=self.run
        if pallet is None or run is None:return
        later=list(run['parts'][run['done']+1:])
        if not later:return
        adr,dof=self.free(pallet)
        self.data.qpos[adr:adr+7]=(self.line.entry(),self.line.start[1],self.line.pallet_z()+.0005,1.,0.,0.,0.)
        self.data.qvel[dof:dof+6]=0.
        mj.mj_forward(self.model,self.data)
        waiting=[p for p in later if p not in self.carrier]
        if waiting:
            self.carrier[waiting[0]]=pallet
            self.feed(waiting[0],run['parts'].index(waiting[0]))

    def tool(self,data):
        return data.xpos[self.hand]+data.xmat[self.hand].reshape(3,3)@self.local_tool

    def solve(self,point,seed):
        d=self.scratch;d.qpos[:]=self.data.qpos;d.qvel[:]=0;d.qpos[self.qids]=seed
        goal=np.diag((1.,-1.,-1.));jp=np.zeros((3,self.model.nv));jr=jp.copy()
        for _ in range(400):
            mj.mj_forward(self.model,d)
            current=self.tool(d);rotation=d.xmat[self.hand].reshape(3,3)
            angle=.5*sum((np.cross(rotation[:,i],goal[:,i]) for i in range(3)))
            error=np.r_[point-current,angle]
            if np.linalg.norm(error[:3])<.0007 and np.linalg.norm(angle)<.008:return d.qpos[self.qids].copy()
            mj.mj_jac(self.model,d,jp,jr,current,self.hand)
            jac=np.vstack((jp[:,self.dofs],jr[:,self.dofs]))
            delta=jac.T@np.linalg.solve(jac@jac.T+np.eye(6)*.0004,error)
            delta*=min(1.,.12/max(.00001,np.max(np.abs(delta))))
            d.qpos[self.qids]=np.clip(d.qpos[self.qids]+delta,self.limits[:,0]+.005,self.limits[:,1]-.005)
        raise ValueError('Target is not reachable with this top-down grasp; reset the cell.')

    # -- where the part is: the state, or the cell's camera (ADR 0069) -------------------------

    def nominal(self):
        """Where the current part stands at its source if it stands where it should: the source's
        place, on the tray's floor or the pallet's top."""
        size=self.part_size()
        floor=TABLE+.008 if self.line is None else self.line.top+PALLET[2]
        x,y=self.trays[self.source]
        return np.array((x,y,floor+size[2]+.001))

    def part_size(self):
        """The current part's half sizes (MuJoCo's geom size), m."""
        return self.model.geom_size[next(g for g in range(self.model.ngeom) if self.model.geom_bodyid[g]==self.object_id)]

    def view_clear(self):
        """Whether the camera sees the source's place: no ray from it to the corners and centre
        of the part's top face there meets the machine first."""
        i=mj.mj_name2id(self.model,mj.mjtObj.mjOBJ_CAMERA,self.eye.camera)
        origin=self.data.cam_xpos[i];body=int(self.model.cam_bodyid[i])
        centre=self.nominal();half=self.part_size()
        geom=np.zeros(1,np.int32)
        for dx,dy in ((0,0),(-1,-1),(-1,1),(1,-1),(1,1)):
            point=centre+np.array((dx*half[0],dy*half[1],half[2]))
            ray=point-origin;far=float(np.linalg.norm(ray))
            hit=mj.mj_ray(self.model,self.data,origin,ray/far,np.array((1,1,1,0,0,0),np.uint8),1,body,geom)
            if 0<=hit<far-.01 and geom[0]>=0 and self.model.body(self.model.geom_bodyid[geom[0]]).name.startswith('machine/'):
                return False
        return True

    def locate(self):
        """Where the current part is: the simulator's state, or where the cell's camera sees it
        round the source's place. With the arm in the camera's view, where it should be, marked
        provisional: `start` clears the view and looks before the arm goes for it."""
        if self.eye is None:return self.data.xpos[self.object_id].copy()
        if not self.view_clear():
            self.provisional=True
            return self.nominal()
        self.provisional=False
        seen=self.eye(self.product,tuple(self.nominal()))
        if seen is None:raise ValueError('The camera does not see the part at the source.')
        from math import atan2,degrees
        w,qx,qy,qz=self.data.xquat[self.object_id]
        turn=(degrees(atan2(2*(w*qz+qx*qy),1-2*(qy*qy+qz*qz)))+45)%90-45
        self.sightings.append((self.product,tuple(seen.centre),tuple(float(v) for v in self.data.xpos[self.object_id]),seen.yaw,turn))
        return np.array(seen.centre)

    def plan(self,destination):
        if self.state=='running':raise ValueError('Pause or reset before planning')
        if destination not in self.trays:raise ValueError('Unknown output tray')
        if destination==self.source:raise ValueError('Source and destination must differ')
        self.destination=destination
        pick=self.locate();self.initial_height=float(pick[2])
        if np.linalg.norm(pick[:2]-self.trays[self.source])>.07:raise ValueError('Reset the product to the input tray before planning.')
        pick[2]+=.001
        # Lowered to where it would sit on the tray's floor, 9 mm over it: from a pallet, the
        # pallet's top is that much higher than a tray's floor (ADR 0068).
        lift=0. if self.line is None else self.line.top+PALLET[2]-(TABLE+.008)
        drop=np.array((*(self.trays[destination]+np.array(self.slot)),pick[2]+.009-lift))
        above=pick+np.array((0,0,.16));over_bin=drop+np.array((0,0,.16))
        release=self.release_grip()
        points=(('Approach product',above,255),('Lower to grasp',pick,255),('Close gripper',pick,0),
                ('Lift and check grasp',above,0),('Transfer to '+destination,over_bin,0),
                ('Lower into bin',drop,0),('Release product',drop,release),('Retract',over_bin,release))
        stages=[];seed=self.data.qpos[self.qids].copy();last=None
        for label,point,grip in points:
            path=None
            if label in LINES and last is not None:
                # Solved a centimetre at a time along the line, each from the one before.
                n=max(1,int(np.ceil(np.linalg.norm(point-last)/STEP-1e-9)));q=seed;path=[seed]
                for f in np.linspace(0,1,n+1)[1:]:
                    q=self.solve(last+(point-last)*f,q);path.append(q)
                path=np.array(path)
            else:q=self.solve(point,seed)
            duration=max(1.2,float(np.max(np.abs(q-seed)))/.5)
            if label in ('Close gripper','Release product'):duration=1.
            stages.append(Stage(label,q,grip,duration,point.copy(),path));seed=q;last=point
        self.preview_points=[self.tool(self.data).copy()]
        seed=self.data.qpos[self.qids].copy()
        for stage in stages:
            for t in np.linspace(0,1,16)[1:]:
                self.scratch.qpos[self.qids]=self.along(stage,seed,t)
                mj.mj_forward(self.model,self.scratch)
                self.preview_points.append(self.tool(self.scratch).copy())
            seed=stage.target
        self.stages=stages;self.state='planned';self.message='Path ready. Known-object sensing; fixed-cell waypoints.'
        self.index=0;self.total=0.;self.lift_verified=False

    @staticmethod
    def along(stage,start,blend):
        """The joints `blend` (0 to 1) of the way through `stage` from `start`: along its line's
        solutions, or straight from joint to joint."""
        if stage.path is None:return start+(stage.target-start)*blend
        k=len(stage.path)-1;x=blend*k;i=min(int(x),k-1)
        return stage.path[i]+(stage.path[i+1]-stage.path[i])*(x-i)

    def release_grip(self):
        """The hand's control that opens it CLEAR past the part on each side, to let it go."""
        size=self.model.geom_size[next(g for g in range(self.model.ngeom) if self.model.geom_bodyid[g]==self.object_id)]
        return float(min(255.,(size[1]+CLEAR)/HAND_OPEN*255))

    def start(self):
        if self.state!='planned':raise ValueError('Preview a path first')
        self.start_q=self.data.qpos[self.qids].copy();self.elapsed=0.
        if self.provisional:
            # Planned before the camera could see the part: first out of its view, to above the
            # destination as the plan goes there, then look, plan again and go (ADR 0069).
            self.clear_q=self.stages[4].target.copy()
            self.clear_time=max(1.2,float(np.max(np.abs(self.clear_q-self.start_q)))/.5)
            self.state='clearing';self.message="Clearing the camera's view";return
        self.state='running';self.index=0;self.total=0.
        self.message=self.stages[0].label

    def step_label(self):
        """What the cell is doing now, in a few words."""
        return "clearing the camera's view" if self.state=='clearing' else self.stages[self.index].label

    def clearing(self,dt):
        """The arm on its way out of the camera's view; once there, the cell looks and goes."""
        self.elapsed+=dt;self.total+=dt
        t=min(1.,self.elapsed/self.clear_time);blend=t*t*(3-2*t)
        target=self.start_q+(self.clear_q-self.start_q)*blend
        result={'machine/servo_'+str(i+1):float(v) for i,v in enumerate(target)}
        result['machine/servo_8']=self.stages[0].grip
        if self.elapsed>=self.clear_time+.35 and np.max(np.abs(self.data.qpos[self.qids]-self.clear_q))<.10:
            total=self.total;self.state='idle'
            self.plan(self.destination)
            if self.provisional:self.fail("The arm hides the part from the camera.");return result
            self.start();self.total=total
        elif self.elapsed>self.clear_time+2:self.fail('Motion did not reach its target. Reset and inspect the cell.')
        return result

    def fail(self,message):
        self.state='failed';self.message=message
        if self.run is not None and message!=self.run.get('failure'):
            self.run['failure']=message

    # -- a production run: part after part (ADR 0019) --------------------------------

    def production(self,parts,destination):
        """Run the cell for each of `parts` (body names) in turn: the first must be on the
        source tray; each next one is moved there by the feeder, which is not simulated,
        once the one before has been placed and the hand has retracted. Each part goes to
        the next slot of the destination bin."""
        if self.state=='running':raise ValueError('Pause or reset before starting a run')
        parts=tuple(parts)
        if not parts or parts[0]!=self.product:raise ValueError('A run starts with the part on the input tray')
        self.run=dict(parts=parts,done=0,failed=0,times=[],placements=[],arrivals=[],destination=destination,failure=None,started=float(self.data.time))
        self.slot=SLOTS[0]
        if self.line is not None:
            # Fed by the conveyor (ADR 0068): each part on a pallet where the feeder puts it, the
            # first picked once its pallet rests at the stop.
            if self.feeder is not None:
                for i,part in enumerate(parts):
                    if part in self.carrier:self.feed(part,i)
            self.destination=destination;self.state='waiting';self.waited=0.;self.settled=0.
            self.message=f'Part 1 of {len(parts)}: waiting for its pallet at the stop'
            return
        if self.feeder is not None:self.feed(self.product,0)
        self.plan(destination);self.start()

    def feed(self,body,i):
        """Put part `body` on the source tray where the feeder puts the i-th: its centre, or off it
        by `feeder(i)` - the feeder, not simulated, as placed by a person or a chute."""
        from math import cos,radians,sin
        object_id=self.model.body(body).id
        joint=self.model.body_jntadr[object_id];adr=self.model.jnt_qposadr[joint];dof=self.model.jnt_dofadr[joint]
        size=self.model.geom_size[next(g for g in range(self.model.ngeom) if self.model.geom_bodyid[g]==object_id)]
        dx,dy,turn=self.feeder(i) if self.feeder is not None else (0.,0.,0.)
        x,y=self.trays[self.source];a=radians(turn)/2;z=TABLE+.008+size[2]+.001
        if self.line is not None:
            # On its pallet, wherever the pallet is now, between its nest's bars (ADR 0068).
            from .scene import NEST
            reach=size[0]*abs(cos(radians(turn)))+size[1]*abs(sin(radians(turn)))+abs(dx)
            if reach>size[0]+NEST[0]+1e-9:raise ValueError(f'A part {1000*dx:+.1f} mm along the line and turned {turn:g} deg does not fit between its pallet\'s bars.')
            x,y,z=self.data.xpos[self.model.body(self.carrier[body]).id];z+=PALLET[2]/2+size[2]+.001
        self.data.qpos[adr:adr+7]=(x+dx,y+dy,z,cos(a),0.,0.,sin(a))
        self.data.qvel[dof:dof+6]=0.
        mj.mj_forward(self.model,self.data)

    def left(self):
        """The part just placed as it was left (process.Placement): from its slot's centre, turned
        from square, and its cycle."""
        from math import atan2,degrees
        from .process import Placement
        x,y=self.trays[self.destination]+np.array(self.slot);pos=self.data.xpos[self.object_id]
        w,qx,qy,qz=self.data.xquat[self.object_id]
        yaw=(degrees(atan2(2*(w*qz+qx*qy),1-2*(qy*qy+qz*qz)))+45)%90-45
        part=self.run['done'] if self.run is not None else 0
        return Placement(part,1000*float(pos[0]-x),1000*float(pos[1]-y),float(yaw),float(self.total))

    def next_part(self):
        """The part just placed is counted; the next is fed onto the source tray, planned
        for the next slot and started."""
        run=self.run
        run['done']+=1;run['times'].append(self.total)
        if run['done']>=len(run['parts']):
            self.message=f"Run complete: {run['done']} parts placed in the {run['destination']} tray."
            return
        if run['done']>=len(SLOTS):
            self.message=f"The {run['destination']} tray is full after {run['done']} parts.";return
        self.product='objects/'+run['parts'][run['done']].split('/')[-1]
        self.object_id=self.model.body(self.product).id
        self.slot=SLOTS[run['done']]
        if self.line is not None:
            self.state='waiting';self.waited=0.;self.settled=0.
            self.message=f"Part {run['done']+1} of {len(run['parts'])}: waiting for its pallet at the stop"
            return
        self.feed(self.product,run['done'])
        self.state='idle'
        self.plan(run['destination']);self.start()
        self.message=f"Part {run['done']+1} of {len(run['parts'])}: "+self.step_label()

    def run_summary(self):
        """(placed, failed, seconds per part, parts per minute) of the run so far, or None."""
        run=self.run
        if run is None:return None
        per=sum(run['times'])/len(run['times']) if run['times'] else None
        elapsed=float(self.data.time)-run['started']
        rate=60*run['done']/elapsed if elapsed>0 and run['done'] else None
        return run['done'],run['failed'],per,rate

    def commands(self,dt):
        """The cell's commands for one step: its conveyor's rollers, if it has one, and the arm's."""
        belt=self.belt()
        if self.state=='waiting':self.arrived(dt)
        if self.state=='clearing':
            result=self.clearing(dt);result.update(belt)
            return result
        if self.state!='running':return belt
        result=self.arm(dt);result.update(belt)
        return result

    def arm(self,dt):
        if self.state!='running':return {}
        stage=self.stages[self.index];self.elapsed+=dt;self.total+=dt
        t=min(1.,self.elapsed/stage.duration);blend=t*t*(3-2*t)
        target=self.along(stage,self.start_q,blend)
        result={'machine/servo_'+str(i+1):float(v) for i,v in enumerate(target)}
        result['machine/servo_8']=stage.grip
        if self.elapsed>=stage.duration+.35:
            error=np.max(np.abs(self.data.qpos[self.qids]-stage.target))
            if error>.10:
                if self.elapsed>stage.duration+2:self.fail('Motion did not reach its target. Reset and inspect the cell.')
                return result
            pos=self.data.xpos[self.object_id]
            if self.index==2 and self.product not in self.observations.grasped():
                self.fail('Grasp failed: both fingers did not contact the product.');return result
            if self.index==3:
                self.lift_verified=bool(pos[2]>self.initial_height+.09)
                if not self.lift_verified:self.fail('Product slipped or did not lift.');return result
                if self.line is not None:self.send_back()
            if self.index==7:
                x,y=self.trays[self.destination]
                if abs(pos[0]-x)<.08 and abs(pos[1]-y)<.07 and TABLE<pos[2]<TABLE+.12:
                    self.state='completed';self.message='Placed in the '+self.destination+' tray. Physical lift and placement verified.'
                    self.placement=self.left()
                    if self.run is not None:
                        self.run['placements'].append(self.placement);self.next_part()
                else:
                    self.fail('Placement failed: product is outside the selected tray.')
                    if self.run is not None:self.run['failed']+=1
                return result
            self.index+=1;self.elapsed=0.;self.start_q=stage.target.copy();self.message=self.stages[self.index].label
        return result
