"""Bind portable drive assistance to native wheel speed and base velocity."""
import mujoco as mj
import numpy as np
from little_world.core.component import Body
from little_world.assets.catalog import BY_ID
from little_world.construction.docking import subtree
from .drive_assist import DriveAssist


class MujocoDrive:
    def __init__(self,backend,bp,prefix='machine/'):
        self.backend=backend;self.assist=DriveAssist();self.channels=[];self.groups={}
        parts={c.id:c for c in bp.components};model,data=backend.model,backend.data
        for spec in bp.controllers:
            if spec.kind!='differential_torque':continue
            sides=spec.drive_sides or tuple(i%2 for i in range(len(spec.actuators)))
            for name,side in zip(spec.actuators,sides):
                motor=parts[name];joint=parts[motor.joint];body=parts[joint.body];base=body
                while base.parent:base=parts[base.parent]
                rid=model.body(prefix+base.id).id
                idx=model.actuator(prefix+name).id;jid=int(model.actuator_trnid[idx,0]);dof=int(model.jnt_dofadr[jid])
                radius=.085
                for candidate in bp.components:
                    if isinstance(candidate,Body) and candidate.id in subtree(bp,body.id) and candidate.catalog_part in BY_ID:
                        item=BY_ID[candidate.catalog_part]
                        if item.variant in ('drive','wheel','hw_tread'):
                            radius=candidate.geometry.size[0] if item.variant in ('drive','wheel') else item.dimensions[0]/2
                            break
                bid=model.body(prefix+body.id).id
                offset=data.xmat[rid].reshape(3,3).T@(data.xpos[bid]-data.xpos[rid])
                entry=(prefix+name,dof,float(model.actuator_ctrlrange[idx,1]),radius,side,rid,float(offset[1]))
                self.channels.append(entry);self.groups.setdefault(spec.drive_settings,[]).append(entry)

    def step_commands(self,targets,dt,angular=False):
        model,data=self.backend.model,self.backend.data;velocities={};result={}
        for settings,channels in self.groups.items():
            goals={};observations={}
            for name,dof,limit,radius,side,rid,y in channels:
                if rid not in velocities:
                    v=np.zeros(6);mj.mj_objectVelocity(model,data,mj.mjtObj.mjOBJ_BODY,rid,v,1);velocities[rid]=v
                v=velocities[rid]
                goal=targets[side]*radius if angular else targets[side]/5*settings.max_speed
                goals[name]=max(-settings.max_speed,min(settings.max_speed,goal))
                observations[name]=(float(data.qvel[dof]),radius,limit,float(v[3]-v[2]*y))
            result.update(self.assist.commands(goals,observations,dt,settings))
        return result
