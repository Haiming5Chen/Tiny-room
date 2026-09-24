"""Panda-only top-down manipulation using native IK and real contact grasps.

Known object state is an ideal observation, not computer vision. This fixed-cell
waypoint planner is not a general obstacle-avoidance or grasp-planning system.
"""
from dataclasses import dataclass
import numpy as np
import mujoco as mj
from .scene import BINS,TABLE
from little_world.programming.observations import Observations

@dataclass
class Stage:
    label:str
    target:np.ndarray
    grip:float
    duration:float
    point:np.ndarray

class FactoryCycle:
    def __init__(self,backend,source='input'):
        from .recipe import TRAYS
        if source not in TRAYS:raise ValueError('Unknown source tray')
        self.source=source
        self.backend=backend;self.model=backend.model;self.data=backend.data
        self.prefix='machine/root__robot_'
        self.hand=self.model.body(self.prefix+'hand').id
        self.qids=np.array([self.model.jnt_qposadr[self.model.joint(self.prefix+'joint'+str(i)).id] for i in range(1,8)])
        self.dofs=np.array([self.model.jnt_dofadr[self.model.joint(self.prefix+'joint'+str(i)).id] for i in range(1,8)])
        self.limits=np.array([self.model.jnt_range[self.model.joint(self.prefix+'joint'+str(i)).id] for i in range(1,8)])
        self.object_id=self.model.body('objects/product').id
        self.trays={name:self.data.xpos[self.model.body('factory/'+name+'_base').id][:2].copy() for name in TRAYS}
        self.scratch=mj.MjData(self.model)
        self.state='idle';self.message='Select a product and output bin, then Preview path.'
        self.stages=[];self.index=0;self.elapsed=0.;self.total=0.;self.lift_verified=False
        self.observations=Observations(self.model,self.data)
        self.local_tool=np.array((0.,0.,.103))

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

    def plan(self,destination):
        if self.state=='running':raise ValueError('Pause or reset before planning')
        if destination not in self.trays:raise ValueError('Unknown output bin')
        if destination==self.source:raise ValueError('Source and destination must differ')
        self.destination=destination
        pick=self.data.xpos[self.object_id].copy();self.initial_height=float(pick[2])
        if np.linalg.norm(pick[:2]-self.trays[self.source])>.07:raise ValueError('Reset the product to the input tray before planning.')
        pick[2]+=.001
        drop=np.array((*self.trays[destination],pick[2]+.009))
        above=pick+np.array((0,0,.16));over_bin=drop+np.array((0,0,.16))
        points=(('Approach product',above,255),('Lower to grasp',pick,255),('Close gripper',pick,0),
                ('Lift and check grasp',above,0),('Transfer to '+destination,over_bin,0),
                ('Lower into bin',drop,0),('Release product',drop,255),('Retract',over_bin,255))
        stages=[];seed=self.data.qpos[self.qids].copy()
        for label,point,grip in points:
            q=self.solve(point,seed)
            duration=max(1.2,float(np.max(np.abs(q-seed)))/.5)
            if label in ('Close gripper','Release product'):duration=1.
            stages.append(Stage(label,q,grip,duration,point.copy()));seed=q
        self.preview_points=[self.tool(self.data).copy()]
        seed=self.data.qpos[self.qids].copy()
        for stage in stages:
            for t in np.linspace(0,1,16)[1:]:
                self.scratch.qpos[self.qids]=seed+(stage.target-seed)*t
                mj.mj_forward(self.model,self.scratch)
                self.preview_points.append(self.tool(self.scratch).copy())
            seed=stage.target
        self.stages=stages;self.state='planned';self.message='Path ready. Known-object sensing; fixed-cell waypoints.'
        self.index=0;self.total=0.;self.lift_verified=False

    def start(self):
        if self.state!='planned':raise ValueError('Preview a path first')
        self.state='running';self.index=0;self.elapsed=0.;self.total=0.
        self.start_q=self.data.qpos[self.qids].copy();self.message=self.stages[0].label

    def fail(self,message):
        self.state='failed';self.message=message

    def commands(self,dt):
        if self.state!='running':return {}
        stage=self.stages[self.index];self.elapsed+=dt;self.total+=dt
        t=min(1.,self.elapsed/stage.duration);blend=t*t*(3-2*t)
        target=self.start_q+(stage.target-self.start_q)*blend
        result={'machine/servo_'+str(i+1):float(v) for i,v in enumerate(target)}
        result['machine/servo_8']=stage.grip
        if self.elapsed>=stage.duration+.35:
            error=np.max(np.abs(self.data.qpos[self.qids]-stage.target))
            if error>.10:
                if self.elapsed>stage.duration+2:self.fail('Motion did not reach its target. Reset and inspect the cell.')
                return result
            pos=self.data.xpos[self.object_id]
            if self.index==2 and 'objects/product' not in self.observations.grasped():
                self.fail('Grasp failed: both fingers did not contact the product.');return result
            if self.index==3:
                self.lift_verified=bool(pos[2]>self.initial_height+.09)
                if not self.lift_verified:self.fail('Product slipped or did not lift.');return result
            if self.index==7:
                x,y=self.trays[self.destination]
                if abs(pos[0]-x)<.08 and abs(pos[1]-y)<.07 and TABLE<pos[2]<TABLE+.12:
                    self.state='completed';self.message='Placed in '+self.destination+' bin. Physical lift and placement verified.'
                else:self.fail('Placement failed: product is outside the selected bin.')
                return result
            self.index+=1;self.elapsed=0.;self.start_q=stage.target.copy();self.message=self.stages[self.index].label
        return result
