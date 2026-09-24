"""Optional native binding for the portable keyboard controller."""
from .keyboard import KeyboardPositionControl


class MujocoKeyboardControl(KeyboardPositionControl):
    def __init__(self,backend,blueprint,entity_id='machine'):
        super().__init__(blueprint.controllers)
        self.backend=backend
        self.prefix=entity_id+'/'
        self.channels={}
        self.servos={}
        model=backend.model
        for spec in self.specs:
            for name in spec.actuators:
                if self.prefix+name in backend.servo_info:
                    actuator,channel=backend.servo_info[self.prefix+name]
                    joint_name=backend.servo_joint_names[self.prefix+name]
                    joint=model.joint(joint_name).id
                    self.servos[name]=(actuator,channel)
                    self.channels[name]=(int(model.jnt_qposadr[joint]),int(model.jnt_dofadr[joint]),0,0,0)
                    continue
                actuator=model.actuator(self.prefix+name).id
                idx=int(model.actuator_trnid[actuator,0])
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
                rate=radians(spec.speed) if channel<7 else -255*spec.speed/100
                target=self.targets.get(name,float(data.ctrl[idx]))+direction*rate*dt
                lo,hi=self.backend.model.actuator_ctrlrange[idx] if self.backend.model.actuator_ctrllimited[idx] else (-6.283185307,6.283185307)
                self.targets[name]=result[name]=max(float(lo),min(float(hi),target))
        return {self.prefix+name:value for name,value in result.items()}

    def display_position(self,name):
        from math import degrees
        q=self.channels[name][0]
        if name in self.servos and self.servos[name][1]==7:
            return max(0.,min(100.,100*(1-float(self.backend.data.qpos[q])/.04))), '% closed'
        return degrees(float(self.backend.data.qpos[q])), 'deg'

    def set_position_target(self,name,value):
        from math import radians
        if name in self.servos and self.servos[name][1]==7:self.targets[name]=255*(1-value/100)
        else:self.targets[name]=radians(value)

    def nudge(self,name,amount):
        """Increment a held target in displayed degrees or percentage closure."""
        from math import radians
        if name in self.servos:
            idx,channel=self.servos[name]
            current=self.targets.get(name,float(self.backend.data.ctrl[idx]))
            if channel==7:
                self.targets[name]=max(0.,min(255.,current-amount*255/100))
            else:
                lo,hi=self.backend.model.actuator_ctrlrange[idx] if self.backend.model.actuator_ctrllimited[idx] else (-6.283185307,6.283185307)
                self.targets[name]=max(float(lo),min(float(hi),current+radians(amount)))
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
