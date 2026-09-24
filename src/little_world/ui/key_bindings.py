"""Saved keyboard action editor and native address binding for position control."""
from math import degrees
import glfw
from little_world.core.component import Motor,RobotServo
from little_world.control.keyboard import KeyboardPositionControl
from .inspector import numbers


class KeyBindings:
    def init_key_bindings(self):
        self.control_panel=False
        self.control_selection=None
        self.control_offset=0
        self.jog_step=5
        self.gripper_index=0
        self.joint_control=KeyboardPositionControl()
        self.joint_channels={}

    def bind_joint_runtime(self):
        from little_world.control.mujoco_keyboard import MujocoKeyboardControl
        self.joint_control=MujocoKeyboardControl(self.backend,self.editor.blueprint,'machine')
        self.joint_channels=self.joint_control.channels

    def joint_commands(self):
        held=self.joint_control.held
        self.joint_control.held=held | self.program_keys
        try:return self.joint_control.step_commands(self.world.timestep)
        finally:self.joint_control.held=held

    def operate_robot(self):
        if self.bench_open:
            self.camera.lookat[:]=self.bench_camera.lookat
            self.camera.distance=self.bench_camera.distance
        self.close_bench();self.control_panel=True;self.panel_mode='keys'
        self.status='Click a movement button to start. Small steps help with precise positioning.'

    def jog_action(self,spec_id,direction):
        if self.building:self.simulate()
        self.runner.stop();self.program_keys.clear();self.clear_keys();self.paused=False
        spec=next(s for s in self.joint_control.specs if s.id==spec_id)
        for name in spec.actuators:
            gripper=name in self.joint_control.servos and self.joint_control.servos[name][1]==7
            self.joint_control.nudge(name,direction*(10 if gripper else self.jog_step))
        self.control_selection=spec.id
        self.status=(spec.label or spec.id)+' target adjusted. Pause freezes the scene; Stop restores the design.'

    def binding_form(self,controller=None):
        if controller is None:
            if self.editor.selected is None:
                self.status='Select a powered component first.'
                return
            own=self.editor.selected_motors()
            included=self.editor.subtree_ids()
            names={c.id for c in own} if own else {c.id for c in self.editor.blueprint.components if isinstance(c,(Motor,RobotServo)) and c.id in included}
            choices=[c for c in self.editor.blueprint.controllers if c.kind=='keyboard_position' and set(c.actuators)<=names]
            if any(isinstance(c,RobotServo) and c.id in names for c in self.editor.blueprint.components) and choices:
                labels={c.label+' ['+c.positive_key+'/'+c.negative_key+']':c for c in choices}
                self.choose('Choose robot action',tuple(labels),lambda label:self.binding_form(labels[label]));return
            controller=next((c for c in choices if set(c.actuators)==names),None)
        def apply(values):
            speed=numbers(values[3],1)[0]
            kp,kd=numbers(values[4],2)
            self.edit(lambda:self.editor.bind_keys(values[0],values[1],values[2],speed,kp,kd,controller.id if controller else None))
        servos={c.id:c for c in self.editor.blueprint.components if isinstance(c,RobotServo)}
        native=controller is not None and any(a in servos for a in controller.actuators)
        gripper=native and any(servos[a].channel==7 for a in controller.actuators)
        fields=[
            ('Action name',controller.label if controller else 'New action'),
            ('Increase / close key',controller.positive_key if controller else 'R'),
            ('Decrease / open key',controller.negative_key if controller else 'V'),
            ('Target speed (% closure / second)' if gripper else 'Target speed (degrees / second)',str(controller.speed if controller else 30)),
            ('Position gain, damping gain',f'{controller.kp}, {controller.kd}' if controller else '12, 0.8')]
        if native:
            fields=fields[:4]
            original_apply=apply
            apply=lambda values:original_apply([*values,f'{controller.kp}, {controller.kd}'])
        self.form('Keyboard action',fields,apply,
            'Original robot servo gains and force limits are retained.' if native else 'Own motor, or all motors inside an unpowered housing. Hinges need limits.',text_input=True)

    def over_controls(self,x,y):
        width,height=glfw.get_window_size(self.window)
        return self.control_panel and width-338<x<width-12 and 104<y<height-42

    def draw_control_panel(self,ui,button,text,ww,wh,fw,fh):
        if not self.control_panel:
            return
        ui.flush(ww,wh,fw,fh)
        ui.begin()
        x=ww-338
        self.buttons=[b for b in self.buttons if b.x+b.width<x or b.y+b.height<104 or b.y>wh-42]
        ui.rect(x,104,326,wh-146,(.065,.095,.12))
        text({'keys':'ROBOT CONTROLS','program':'PROGRAM EDITOR','test':'LIVE MEASUREMENTS'}[self.panel_mode],x+16,119,11,(.6,.74,.77))
        button('Close',x+244,112,66,lambda:setattr(self,'control_panel',False),h=26)
        if self.panel_mode=='test':
            self.draw_test(ui,button,text,ww,wh);return
        if self.panel_mode=='program':
            self.draw_program(ui,button,text,ww,wh);return
        text('Click to move, or hold the shown keys.',x+16,151,11,(.6,.74,.77),294)
        for i,(label,step) in enumerate((('Fine 1 deg',1),('5 deg',5),('15 deg',15))):
            button(label,x+16+i*100,173,94,lambda n=step:setattr(self,'jog_step',n),active=self.jog_step==step,h=26)
        grippers=[s for s in self.joint_control.specs if any(a in self.joint_control.servos and self.joint_control.servos[a][1]==7 for a in s.actuators)]
        specs=tuple(s for s in self.joint_control.specs if s not in grippers)
        rows=max(1,int((wh-458)/57))
        self.control_offset=min(self.control_offset,max(0,len(specs)-rows))
        for i,spec in enumerate(specs[self.control_offset:self.control_offset+rows]):
            y=211+i*57
            label=f'{spec.positive_key} / {spec.negative_key}   '+(spec.label or spec.id)
            def select(spec=spec):
                self.control_selection=spec.id
            gripper=any(a in self.joint_control.servos and self.joint_control.servos[a][1]==7 for a in spec.actuators)
            button(label,x+16,y,174,select,active=self.control_selection==spec.id,h=30)
            button('Open' if gripper else '-',x+196,y,54,lambda sid=spec.id:self.jog_action(sid,-1),h=30)
            button('Close' if gripper else '+',x+256,y,54,lambda sid=spec.id:self.jog_action(sid,1),h=30)
            values=[self.joint_control.display_position(name) for name in spec.actuators]
            text(' / '.join(f'{v:.1f} {unit}' for v,unit in values),x+24,y+33,11,(.6,.74,.77),276)
        if not specs:
            text('No joint keys assigned yet.',x+16,204,13)
            text('Select a motor or powered component,',x+16,235,11,(.6,.74,.77))
            text('then choose Bind selected.',x+16,253,11,(.6,.74,.77))
        page_y=wh-238
        button('<',x+16,page_y,40,lambda:setattr(self,'control_offset',max(0,self.control_offset-rows)),self.control_offset>0,h=26)
        button('Resume' if self.paused else 'Pause',x+64,page_y,198,lambda:setattr(self,'paused',not self.paused),not self.building,h=26)
        button('>',x+270,page_y,40,lambda:setattr(self,'control_offset',self.control_offset+rows),self.control_offset+rows<len(specs),h=26)
        selected=next((c for c in self.joint_control.specs if c.id==self.control_selection),None)
        button('Edit action',x+16,wh-200,142,lambda:self.binding_form(selected),self.building and selected is not None)
        button('Remove',x+168,wh-200,142,lambda:self.edit(lambda:self.editor.remove_binding(selected.id)),self.building and selected is not None)
        if grippers:
            self.gripper_index%=len(grippers);grip=grippers[self.gripper_index]
            label='Gripper' if len(grippers)==1 else f'Gripper {self.gripper_index+1}/{len(grippers)}'
            def select_gripper():
                if len(grippers)>1:self.gripper_index=(self.gripper_index+1)%len(grippers)
                self.control_selection=grippers[self.gripper_index].id
            button(label+' / 10%',x+16,wh-159,132,select_gripper)
            button('Open',x+156,wh-159,73,lambda sid=grip.id:self.jog_action(sid,-1))
            button('Close',x+237,wh-159,73,lambda sid=grip.id:self.jog_action(sid,1))
        else:
            button('Bind selected',x+16,wh-159,294,self.binding_form,self.building and self.editor.selected is not None)
        def simulate():
            self.close_bench()
            self.simulate()
        button('Start simulation' if self.building else 'Stop simulation',x+16,wh-116,294,simulate,active=True)
        text('WASD: drive / Space: release keys / P: pause',x+16,wh-70,10,(.6,.74,.77),294)
