"""Real robot experiments hosted in the shared application window."""
from pathlib import Path
import time
import glfw
import mujoco as mj
import numpy as np
from .workshop import Workshop
from .real_lab import RealLab
from .cell_changes import CellChanges
from .teaching_workspace import TeachingWorkspace
from .factory_authoring import FactoryAuthoring,tray_label
from dataclasses import replace
from little_world.factory.recipe import TRAYS
from little_world.core.entity import Entity
from little_world.factory.scene import factory_scene,robot_blueprint,PRODUCTS,BINS,TABLE
from little_world.factory.controller import FactoryCycle

class FactoryWorkshop(CellChanges,TeachingWorkspace,RealLab,FactoryAuthoring,Workshop):
    PANEL=304
    def __init__(self,recipe_path=None):
        self.init_authoring(recipe_path);self.init_cell_changes();self.factory_mode=True
        self.robot_asset='franka_panda';self.experiment='Pick and place';self._robot_programs={}
        self.single_stage=False;self.show_path=True;self.factory_commands={}
        super().__init__(Path.home()/'.little-world-factory-unused.json',robot_blueprint())
        self.initial_camera=((.3,0,.9),2.6)
        self.library_open=False
        self.init_teaching()

    def _scene(self):
        return factory_scene(Entity('machine',self.editor.blueprint),recipe=self.recipe)

    def bind_runtime(self):
        super().bind_runtime();self.cycle=None if self.joint_lab else FactoryCycle(self.backend,source=self.recipe.source);self.factory_commands={}
        self.bind_teaching()

    def save(self):
        return self.save_program() if self.joint_lab else self.save_cell()

    def reset_cell(self):
        self.runner.stop();self.program_keys.clear();self.program_drive=None
        if not self.building:self.state=self.world.reset()
        self.paused=False;self.tray_drag=None;self.pending_source=None;self.clear_keys();self.bind_runtime()
        self.status='Cell reset. Choose a product and destination.'

    def select_product(self,name):
        self.apply_recipe(replace(self.recipe,product=name))

    def select_destination(self,name):
        self.apply_recipe(replace(self.recipe,destination=name))

    def preview_cycle(self):
        self.cycle.plan(self.destination);self.status=self.cycle.message

    def start_cycle(self,single=False):
        if self.cycle.state=='running':
            self.single_stage=single;self.paused=False;return
        if self.cycle.state=='idle':self.preview_cycle()
        if self.cycle.state!='planned':raise ValueError('Reset the cell to run another product.')
        if self.building:self.state=self.world.start()
        self.cycle.start();self.single_stage=single;self.paused=False

    def tick_program(self):
        if self.teaching:
            self.factory_commands=self.teach_motion.commands(self.world.timestep)
            if self.teach_motion.state in ('reached','failed'):self.paused=True
            return
        if self.joint_lab:return super().tick_program()
        old=self.cycle.index
        self.factory_commands=self.cycle.commands(self.world.timestep)
        if self.single_stage and self.cycle.index!=old:self.paused=True
        if self.cycle.state in ('failed','completed'):self.paused=True
        self.status=self.cycle.message

    def joint_commands(self):return super().joint_commands() if self.joint_lab and not self.teaching else self.factory_commands
    def selection_outline(self,scene=None):pass
    def pick(self,x,y):pass
    def character(self,*args):
        if self.dialog is not None or self.joint_lab:return super().character(*args)
    def key(self,win,key,scancode,action,mods):
        if self.dialog is not None or self.joint_lab:return super().key(win,key,scancode,action,mods)
        self.last_input=time.monotonic()
        if action!=glfw.PRESS:return
        if key in (glfw.KEY_SPACE,glfw.KEY_P) and not self.building:self.paused=not self.paused
        elif key==glfw.KEY_ESCAPE:
            if self.tray_drag or self.pending_source:self.tray_drag=None;self.pending_source=None;self.authoring_note='Edit cancelled.'
            elif self.guided:self.guided=False
            else:glfw.set_window_should_close(win,True)
        elif key==glfw.KEY_C:self.camera_toggle()

    def decorate_scene(self):
        if self.teaching:self.draw_teaching_target();return
        if self.joint_lab:return
        self.draw_tray_ghost()
        if not self.show_path or not self.cycle.stages:return
        points=self.cycle.preview_points
        for a,b in zip(points,points[1:]):
            if self.render_scene.ngeom>=self.render_scene.maxgeom:break
            geom=self.render_scene.geoms[self.render_scene.ngeom]
            mj.mjv_initGeom(geom,mj.mjtGeom.mjGEOM_CAPSULE,np.zeros(3),np.zeros(3),np.eye(3).ravel(),np.array((.2,.9,.75,.85),dtype=np.float32))
            mj.mjv_connector(geom,mj.mjtGeom.mjGEOM_CAPSULE,.0018,a,b)
            geom.category=mj.mjtCatBit.mjCAT_DECOR;self.render_scene.ngeom+=1

    def draw_factory(self,ui,button,text,ww,wh,fw,fh):
        import textwrap
        glfw.set_window_title(self.window,'Little World | Real experiments')
        if self.teaching:
            self.draw_teaching(ui,button,text,ww,wh,fw,fh);return
        if self.joint_lab:
            self.draw_joint_lab(ui,button,text,ww,wh,fw,fh);return
        self.draw_real_header(ui,button,text,ww,wh)
        button('Undo',ww-454,12,66,self.undo_recipe,self.building and not self.guided and bool(self.recipe_history),h=32)
        button('Save cell',ww-382,12,72,self.save_cell,self.pending_source is None and self.tray_drag is None,h=32)
        editable=self.building and not self.guided
        text('PICK-AND-PLACE EXPERIMENT',18,78,11)
        button('Joint lab',ww-130,72,114,lambda:self.select_experiment('Joint lab'),self.building,h=30)
        for i,mode in enumerate(('Arrange','Set task')):
            button(mode,18+i*89,104,83,lambda m=mode:self.choose_mode(m),editable,active=self.edit_mode==mode,h=32)
        button('Changes',196,104,90,self.open_cell_changes,editable,h=32)
        for i,line in enumerate(textwrap.wrap(self.authoring_note,41)[:2]):text(line,18,148+i*17,11,(.65,.82,.8),268)
        text('PRODUCT',18,193,11)
        for i,name in enumerate(PRODUCTS):button(name,18+i*138,214,130,lambda n=name:self.select_product(n),editable,active=self.product==name)
        text('From: '+tray_label(self.pending_source or self.recipe.source),18,266,13)
        text('To: '+tray_label(self.destination),18,290,13)
        button('Preview path',18,321,268,self.preview_cycle,self.building,h=34)
        text('TASK SEQUENCE',18,374,12)
        labels=['Locate known product','Approach','Lower to grasp','Close gripper','Lift + verify','Transfer to '+tray_label(self.destination),'Lower into tray','Release','Retract + verify']
        step=min(26,(wh-160-398)/9)
        for i,label in enumerate(labels):
            y=398+i*step;active=self.cycle.state!='idle' and i==self.cycle.index+1
            if active:ui.rect(14,y-3,276,step-1,(.13,.32,.28))
            text(str(i+1)+'. '+label,22,y,11,(.8,.95,.9) if active else (.59,.70,.76),258)
        text('Physics contact / editable trays / fixed robot',18,wh-136,10,(.6,.74,.77),270)
        can_run=self.cycle.state in ('idle','planned') or self.paused and self.cycle.state=='running'
        button('Run cycle' if self.cycle.state!='running' else 'Resume',18,wh-110,130,lambda:self.start_cycle(False),can_run,h=34,tone='primary')
        button('Next step' if self.guided else 'One stage',156,wh-110,130,lambda:self.start_cycle(True),can_run,h=34,tone='primary' if self.guided else None)
        button('Pause',18,wh-68,130,lambda:setattr(self,'paused',True),self.cycle.state=='running' and not self.paused,h=28)
        button('Replay' if self.guided else 'Reset cell',156,wh-68,130,self.reset_cell,h=28)
        button('Camera view',self.PANEL+18,72,130,self.camera_toggle,h=30)
        button('Path: on' if self.show_path else 'Path: off',self.PANEL+156,72,110,lambda:setattr(self,'show_path',not self.show_path),h=30)
        button('Try it yourself' if self.guided else 'How picking works',self.PANEL+274,72,164,self.try_yourself if self.guided else self.enter_guide,h=30,tone='primary')
        state='PAUSED' if self.paused and self.cycle.state=='running' else self.cycle.state.upper()
        text(f'{state} / {self.cycle.total:.1f}s simulation time',self.PANEL+18,116,13,(.4,.85,.72),ww-self.PANEL-40)
        text(self.status if self.status.startswith('Could not') else self.cycle.message,self.PANEL+18,140,12,(.8,.87,.9),ww-self.PANEL-40)
        if self.guided:
            title,caption=self.guide_caption();width=min(540,ww-self.PANEL-36);top=wh-162
            ui.rect(self.PANEL+18,top,width,114,(.07,.14,.17))
            text(title,self.PANEL+32,top+14,16,(.4,.9,.74),width-28)
            for i,line in enumerate(textwrap.wrap(caption,max(35,int((width-28)/7)))):text(line,self.PANEL+32,top+43+i*19,12,(.82,.89,.90),width-28)
        for name in TRAYS:
            point=self.project_table((*self.recipe.point(name),TABLE+.06))
            if point and self.PANEL+10<point[0]<ww-80 and 294<point[1]<wh-60:
                label=tray_label(name)+(' / FROM' if name==(self.pending_source or self.recipe.source) else ' / TO' if name==self.destination else '')
                text(label,point[0]-45,point[1],11,(.5,1.,.83) if name==self.selected_tray else (.9,.94,.96),170)
        text('Arrange: drag trays. Set task: click source then destination. Escape cancels. Drag empty space to orbit.',18,wh-24,11,(.65,.75,.77),ww-36)
        self.draw_dialog(ui,button,text,ww,wh)
        ui.flush(ww,wh,fw,fh)


def main():FactoryWorkshop().run()
if __name__=='__main__':main()
