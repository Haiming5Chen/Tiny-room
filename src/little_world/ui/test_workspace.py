"""Live ideal sensor readouts and bounded diagnostic observations."""
from math import degrees,acos
import json


class TestWorkspace:
    def show_test(self):
        self.close_bench();self.control_panel=True;self.panel_mode='test'

    def test_snapshot(self):
        parts={c.id:c for c in self.editor.blueprint.components}
        joints=[]
        for spec in self.joint_control.specs:
            for name in spec.actuators:
                q,v,lo,hi,cap=self.joint_channels[name]
                actual=float(self.data.qpos[q]);target=self.joint_control.targets.get(name,actual)
                if name in self.joint_control.servos:
                    idx,channel=self.joint_control.servos[name]
                    force=float(self.data.actuator_force[idx]);available=self.joint_control.force_limit(name)
                    if not self.model.actuator_forcelimited[idx] and not self.joint_control.gripper(name):
                        joint=self.model.joint(self.backend.servo_joint_names['machine/'+name]).id
                        force=float(self.data.qfrc_actuator[self.model.jnt_dofadr[joint]])
                    target=self.joint_control.targets.get(name,float(self.data.ctrl[idx]))
                    if self.joint_control.gripper(name) or self.joint_control.unit(name)=='mm':
                        value,unit=self.joint_control.display_position(name)
                        target=100*(1-target/255) if self.joint_control.gripper(name) else 1000*target
                        joints.append(dict(motor=name,label=spec.label,position=value,target=target,error=target-value,
                            unit=unit,force_N=force,available_N=available,limited=abs(force)>=available*.95,model='Menagerie position servo'))
                    else:
                        error=degrees(target-actual)
                        joints.append(dict(motor=name,label=spec.label,angle_deg=degrees(actual),target_deg=degrees(target),error_deg=error,
                            torque_Nm=force,available_Nm=available,limited=abs(error)>2 and abs(force)>=available*.95,model='Menagerie position servo'))
                    continue
                idx=self.model.actuator('machine/'+name).id
                torque=float(self.data.actuator_force[idx]);motor=parts[name]
                available=cap if motor.profile is None else abs(motor.profile.constrain(cap if target>=actual else -cap,float(self.data.qvel[v]),cap))
                error=degrees(target-actual)
                limited=abs(error)>2 and (available<1e-6 or abs(torque)>=available*.95)
                joints.append(dict(motor=name,label=spec.label,angle_deg=degrees(actual),target_deg=degrees(target),error_deg=error,
                    torque_Nm=torque,available_Nm=available,limited=limited,model='estimated' if motor.profile else 'ideal'))
        tilt=degrees(acos(max(-1,min(1,float(self.data.xmat[self.root_id,8]))))) if self.root_id>=0 else 0.
        grasp=sorted(self.observations.grasped())
        jaw_targets=[target for name,target in self.joint_control.targets.items() if '_finger_' in name]
        jaw_targets += [1-target/255 for name,target in self.joint_control.targets.items() if self.joint_control.gripper(name)]
        closure=sum(jaw_targets)/len(jaw_targets) if jaw_targets else 0.
        if float(self.data.time)==0:self.grip_history.clear();self.possible_slips.clear()
        for obj in grasp:self.grip_history[obj]=closure
        for obj,previous in self.grip_history.items():
            if obj not in grasp and closure>=previous-1e-3:self.possible_slips.add(obj)
        return dict(time_s=float(self.data.time),program_state=self.runner.state,program_message=self.runner.message,
                    root_tilt_deg=tilt,bilateral_contact=grasp,possible_slips=sorted(self.possible_slips),joints=joints,
                    evidence='Ideal simulation observations; contact does not prove secure grasp; tilt is not a payload rating')

    def export_test(self):
        path=self.path.with_suffix('.test.json');path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_suffix('.json.tmp');temporary.write_text(json.dumps(self.test_snapshot(),indent=2,allow_nan=False));temporary.replace(path)
        self.status='Test snapshot saved: '+str(path)

    def draw_test(self,ui,button,text,ww,wh):
        x=ww-338;snapshot=self.test_snapshot();names=tuple(self.observations.indices)
        if getattr(self,'probe_a',None) not in names:self.probe_a=next((n for n in names if n.endswith('finger_left_pad')),names[0])
        if getattr(self,'probe_b',None) not in names:self.probe_b=next((n for n in names if n=='objects/grasp_cube'),names[-1])
        text('TEST / IDEAL SENSORS',x+16,152,16)
        text(f'{snapshot["time_s"]:.2f}s / {snapshot["program_state"]}',x+16,180,11,(.6,.74,.77),294)
        button('A: '+self.probe_a,x+16,205,294,lambda:self.choose('Probe A',names,lambda n:setattr(self,'probe_a',n)),h=28)
        button('B: '+self.probe_b,x+16,241,294,lambda:self.choose('Probe B',names,lambda n:setattr(self,'probe_b',n)),h=28)
        distance=self.observations.distance(self.probe_a,self.probe_b)
        contact=frozenset((self.probe_a,self.probe_b)) in self.observations.contact_pairs()
        text(f'Centre distance {distance*100:.1f} cm / contact: {"yes" if contact else "no"}',x+16,281,12,(.6,.74,.77),294)
        text('Both jaws touching: '+('yes' if snapshot['bilateral_contact'] else 'no'),x+16,306,12,(.6,.74,.77),294)
        text(f'Base tilt: {snapshot["root_tilt_deg"]:.1f} deg'+(' / tipping risk' if snapshot['root_tilt_deg']>30 else ''),x+16,331,12,(.9,.7,.4),294)
        if snapshot['possible_slips']:text('Possible slip: grip contact was lost.',x+16,353,11,(1,.6,.35),294)
        text('JOINT TARGET / ACTUAL',x+16,377,11)
        rows=max(1,int((wh-565)/38))
        self.test_offset=min(getattr(self,'test_offset',0),max(0,len(snapshot['joints'])-rows))
        button('<',x+242,371,30,lambda:setattr(self,'test_offset',max(0,self.test_offset-rows)),h=22)
        button('>',x+280,371,30,lambda:setattr(self,'test_offset',min(max(0,len(snapshot['joints'])-rows),self.test_offset+rows)),h=22)
        y=399
        for joint in snapshot['joints'][self.test_offset:self.test_offset+rows]:
            color=(1,.6,.35) if joint['limited'] else (.6,.74,.77)
            text(joint['label']+(' / torque limited' if joint['limited'] else ''),x+16,y,11,color,294)
            detail=(f'{joint["target"]:.1f} / {joint["position"]:.1f}% closed / {joint["force_N"]:.2f} N' if 'unit' in joint else f'{joint["target_deg"]:.1f} / {joint["angle_deg"]:.1f} deg / {joint["torque_Nm"]:.2f} Nm')
            text(detail,x+16,y+17,11,color,294);y+=38
        button('Start / reset physics',x+16,wh-151,294,self.simulate,h=30)
        button('Export test snapshot',x+16,wh-113,294,self.export_test,h=30)
        text('Contact/tilt are observations, not certification.',x+16,wh-65,10,(.6,.74,.77),294)
