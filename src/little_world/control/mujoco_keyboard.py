"""Optional native binding for the portable keyboard controller."""
from math import isfinite

from .keyboard import KeyboardPositionControl


def pad_lever(model, data, actuator):
    """The moment arm, about its joint, of a push square to the face of the pad a jaw motor's
    joint carries, through the pad's centre (m) - None for a joint with no pad (FR-037)."""
    import numpy as np
    joint = int(model.actuator_trnid[actuator, 0])
    body = int(model.jnt_bodyid[joint])
    pads = [i for i in range(model.nbody) if int(model.body_parentid[i]) == body and model.body(i).name.endswith('_pad')]
    if not pads or not model.body_geomnum[pads[0]]:
        return None
    g = int(model.body_geomadr[pads[0]])
    normal = data.geom_xmat[g].reshape(3, 3)[:, int(np.argmin(model.geom_size[g]))]    # across its thinnest side
    arm = np.cross(data.geom_xpos[g] - data.xanchor[joint], normal)
    return abs(float(arm @ data.xaxis[joint]))


class MujocoKeyboardControl(KeyboardPositionControl):
    def __init__(self,backend,blueprint,entity_id='machine'):
        super().__init__(blueprint.controllers)
        self.backend=backend
        self.prefix=entity_id+'/'
        self.channels={}
        self.servos={}
        self.units={}   # a robot servo's: 'deg', 'mm' or '%' (a gripper, by its closure)
        self.grips={}   # a gripper servo's (control open, closed, joint position open, closed)
        self.levers={}  # a jaw motor's moment arm at its pad's centre, m (FR-037)
        model=backend.model
        for spec in self.specs:
            for name in spec.actuators:
                if self.prefix+name in backend.servo_info:
                    actuator,channel=backend.servo_info[self.prefix+name]
                    joint_name=backend.servo_joint_names[self.prefix+name]
                    joint=model.joint(joint_name).id
                    self.servos[name]=(actuator,channel)
                    self.units[name]=getattr(backend,'servo_units',{}).get(self.prefix+name,'%' if channel==7 else 'deg')
                    if self.units[name]=='%':
                        self.grips[name]=getattr(backend,'servo_grips',{}).get(self.prefix+name) or (255.,0.,.04,0.)
                    self.channels[name]=(int(model.jnt_qposadr[joint]),int(model.jnt_dofadr[joint]),0,0,0)
                    continue
                actuator=model.actuator(self.prefix+name).id
                idx=int(model.actuator_trnid[actuator,0])
                lever=pad_lever(model,backend.data,actuator)
                if lever:self.levers[name]=lever
                self.channels[name]=(int(model.jnt_qposadr[idx]),int(model.jnt_dofadr[idx]),
                                     float(model.jnt_range[idx,0]),float(model.jnt_range[idx,1]),
                                     float(model.actuator_ctrlrange[actuator,1]))

    def step_commands(self,dt):
        data=self.backend.data
        observations={name:(float(data.qpos[q]),float(data.qvel[v]),lo,hi,torque,float(data.qfrc_bias[v]))
                      for name,(q,v,lo,hi,torque) in self.channels.items() if name not in self.servos}
        from math import radians
        # Existing ideal torque joints retain their portable feedback controller.
        specs=self.specs
        self.specs=tuple(s for s in specs if not any(a in self.servos for a in s.actuators))
        try:result=self.commands(observations,dt)
        finally:self.specs=specs
        for spec in specs:
            direction=int(spec.positive_key in self.held)-int(spec.negative_key in self.held)
            for name in spec.actuators:
                if name not in self.servos:continue
                idx,channel=self.servos[name]
                unit=self.units[name]
                if unit=='%':
                    opened,closed=self.grips[name][:2]
                    rate=(closed-opened)*spec.speed/100
                else:rate=spec.speed/1000 if unit=='mm' else radians(spec.speed)
                target=self.targets.get(name,float(data.ctrl[idx]))+direction*rate*dt
                lo,hi=self.backend.model.actuator_ctrlrange[idx] if self.backend.model.actuator_ctrllimited[idx] else (-6.283185307,6.283185307)
                self.targets[name]=result[name]=max(float(lo),min(float(hi),target))
        return {self.prefix+name:value for name,value in result.items()}

    def squeeze(self,spec_id,newtons):
        """Let the jaws of the joint action `spec_id` push with at most `newtons` square to each
        pad at its centre - their servos' Goal Current, in current-based position control (FR-037)
        - or, with 0, with their motors' full torque. It holds until changed."""
        spec=next((s for s in self.specs if s.id==spec_id),None)
        if spec is None:raise ValueError(f'no joint action called {spec_id!r}')
        if not isfinite(newtons) or newtons<0:raise ValueError('a squeeze is a finite force, 0 or more newtons')
        if newtons and not all(name in self.levers for name in spec.actuators):
            raise ValueError(f'{spec.label or spec.id} has no jaw pads to squeeze with')
        for name in spec.actuators:
            if newtons:self.limits[name]=newtons*self.levers[name]
            else:self.limits.pop(name,None)

    def gripper(self,name):
        """Whether this action's actuator is a model's gripper servo, driven by its closure."""
        return self.units.get(name)=='%'

    def unit(self,name):
        return self.units.get(name,'deg')

    def closure(self,name,ctrl):
        """How closed a gripper servo's control `ctrl` sends it, 0 (open) to 1 (closed)."""
        opened,closed=self.grips[name][:2]
        return (ctrl-opened)/(closed-opened)

    def display_position(self,name):
        from math import degrees
        q=self.channels[name][0]
        if self.gripper(name):
            q_open,q_closed=self.grips[name][2:]
            return max(0.,min(100.,100*(float(self.backend.data.qpos[q])-q_open)/(q_closed-q_open))), '% closed'
        if self.unit(name)=='mm':
            return 1000*float(self.backend.data.qpos[q]), 'mm'
        return degrees(float(self.backend.data.qpos[q])), 'deg'

    def set_position_target(self,name,value):
        from math import radians
        if self.gripper(name):
            opened,closed=self.grips[name][:2]
            self.targets[name]=opened+(closed-opened)*value/100
        elif self.unit(name)=='mm':self.targets[name]=value/1000
        else:self.targets[name]=radians(value)

    def nudge(self,name,amount):
        """Increment a held target in displayed degrees, millimetres or percentage closure."""
        from math import radians
        if name in self.servos:
            idx,channel=self.servos[name]
            current=self.targets.get(name,float(self.backend.data.ctrl[idx]))
            if self.gripper(name):
                opened,closed=self.grips[name][:2]
                self.targets[name]=max(min(opened,closed),min(max(opened,closed),current+(closed-opened)*amount/100))
            else:
                lo,hi=self.backend.model.actuator_ctrlrange[idx] if self.backend.model.actuator_ctrllimited[idx] else (-6.283185307,6.283185307)
                step=amount/1000 if self.unit(name)=='mm' else radians(amount)
                self.targets[name]=max(float(lo),min(float(hi),current+step))
        else:
            q,_,lo,hi,_=self.channels[name]
            current=self.targets.get(name,float(self.backend.data.qpos[q]))
            self.targets[name]=max(lo,min(hi,current+radians(amount)))

    def force_limit(self,name):
        model=self.backend.model;idx,channel=self.servos[name]
        if model.actuator_forcelimited[idx]:return max(abs(float(x)) for x in model.actuator_forcerange[idx])
        joint=model.joint(self.backend.servo_joint_names[self.prefix+name]).id
        if model.jnt_actfrclimited[joint]:return max(abs(float(x)) for x in model.jnt_actfrcrange[joint])
        return float('inf')
