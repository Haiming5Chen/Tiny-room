"""Registered-arm experiments/programming, without component construction."""
from little_world.assets.robot_models import MODELS
from little_world.factory.scene import robot_blueprint
from little_world.construction.editor import AssemblyEditor
from little_world.programming.program import Program,Block

class RealLab:
    @property
    def joint_lab(self):return self.experiment in ('Joint lab','Teach positions')
    @property
    def program_path(self):return self.recipe_path.with_name(self.robot_asset+'.program.json')

    def choose_robot(self):
        labels={title:asset for asset,(_,_,title) in MODELS.items()}
        self.choose('Choose a real robot',tuple(labels),lambda label:self.select_robot(labels[label]))

    def select_robot(self,asset):
        if asset not in MODELS:raise ValueError('Unknown robot')
        program=self._robot_programs.get(asset,Program())
        path=self.recipe_path.with_name(asset+'.program.json')
        if asset not in self._robot_programs and path.exists():program=Program.from_json(path.read_text())
        self._robot_programs[self.robot_asset]=self.program
        if not self.building:self.state=self.world.reset()
        self.runner.stop();self.program_keys.clear();self.program_drive=None;self.clear_keys()
        self.robot_asset=asset;self.experiment='Joint lab'
        self.editor=AssemblyEditor(robot_blueprint(asset));self.guided=False
        self.program=program
        self.program_past=[];self.program_future=[];self.program_selected=0;self.program_offset=0
        self.control_panel=True;self.panel_mode='keys';self.paused=False;self.rebuild()
        self.status='Ready: '+MODELS[asset][2]+'. Operate joints or build a program.'

    def select_experiment(self,name):
        if name=='Pick and place' and self.robot_asset!='franka_panda':raise ValueError('The pick-and-place experiment currently requires Panda and its gripper.')
        if name=='Teach positions' and self.robot_asset!='franka_panda':raise ValueError('Visual teaching currently supports Panda.')
        if name not in ('Joint lab','Pick and place','Teach positions'):raise ValueError('Unknown experiment')
        if name==self.experiment:return
        if not self.building:self.state=self.world.reset()
        self.runner.stop();self.program_keys.clear();self.program_drive=None;self.clear_keys()
        self.experiment=name;self.guided=False;self.paused=False
        self.control_panel=self.joint_lab and not self.teaching;self.panel_mode='keys';self.bind_runtime()
        self.status='Experiment ready.'

    def joint_example(self):
        spec=self.joint_control.specs[0]
        angle=self.joint_control.display_position(spec.actuators[0])[0]
        self.program_edit(Program((Block('move',spec.id,angle+10,5),Block(duration=.5),Block('move',spec.id,angle,5))))
        self.panel_mode='program';self.control_panel=True

    def draw_real_header(self,ui,button,text,ww,wh):
        ui.rect(0,0,ww,56,(.045,.065,.085));ui.rect(0,56,self.PANEL,wh-88,(.075,.099,.125))
        ui.rect(0,wh-32,ww,32,(.055,.077,.097))
        text('little world',18,17,19);self.draw_mode_switch(button)
        button('Factory layout',322,12,136,lambda:self.switch_real_view('Layout'),h=32)
        button('Robot: '+MODELS[self.robot_asset][2],ww-304,12,288,self.choose_robot,self.building,h=32)

    def draw_joint_lab(self,ui,button,text,ww,wh,fw,fh):
        import textwrap
        self.draw_real_header(ui,button,text,ww,wh)
        text('EXPERIMENT',18,80,12)
        button('Joint lab',18,106,126,lambda:self.select_experiment('Joint lab'),active=True)
        button('Pick and place',152,106,134,lambda:self.select_experiment('Pick and place'),self.robot_asset=='franka_panda')
        text(MODELS[self.robot_asset][2],18,166,16,max_width=270)
        for i,line in enumerate(textwrap.wrap('Use a complete robot. Test its motion or program a sequence; no part assembly is needed.',38)):
            text(line,18,201+i*19,12,(.66,.77,.79),270)
        button('Operate robot',18,286,268,lambda:(setattr(self,'panel_mode','keys'),setattr(self,'control_panel',True)),active=self.panel_mode=='keys',h=36)
        button('Program sequence',18,330,268,lambda:(setattr(self,'panel_mode','program'),setattr(self,'control_panel',True)),active=self.panel_mode=='program',h=36)
        button('Load joint motion example',18,380,268,self.joint_example,self.runner.state not in ('running','paused'),h=32)
        button('Teach positions',18,425,268,lambda:self.select_experiment('Teach positions'),self.robot_asset=='franka_panda',h=32)
        text('Original meshes, joints and servos.',18,475,11,(.66,.77,.79),270)
        if self.robot_asset!='franka_panda':
            text('Arm-only model: no gripper.',18,498,11,(.9,.72,.4),270)
            text('Pick-and-place is validated for Panda.',18,521,11,(.66,.77,.79),270)
        button('Reset experiment',18,wh-110,268,self.reset_cell,h=34)
        text(self.status,18,wh-24,11,(.66,.77,.79),ww-36)
        self.draw_control_panel(ui,button,text,ww,wh,fw,fh)
        self.draw_dialog(ui,button,text,ww,wh)
        ui.flush(ww,wh,fw,fh)
