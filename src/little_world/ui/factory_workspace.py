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
from little_world.factory.scene import factory_scene,conveyor_line,robot_blueprint,PRODUCTS,TABLE
from little_world.factory.controller import FactoryCycle,camera_eye

class FactoryWorkshop(CellChanges,TeachingWorkspace,RealLab,FactoryAuthoring,Workshop):
    PANEL=304
    def __init__(self,recipe_path=None):
        self.init_authoring(recipe_path);self.init_cell_changes();self.factory_mode=True
        self.robot_asset='franka_panda';self.experiment='Pick and place';self._robot_programs={}
        self.single_stage=False;self.show_path=True;self.factory_commands={}
        self.feeder='hand'  # how parts reach the source: by hand, or on the roller conveyor (ADR 0068)
        self.sensing='known'    # how the cell finds a part: the state ('known'), or its camera ('camera', ADR 0069)
        super().__init__(Path.home()/'.little-world-factory-unused.json',robot_blueprint())
        self.initial_camera=((.3,0,.9),2.6)
        self.library_open=False
        self.init_teaching()

    RUN=6   # parts in a production run: the input tray's and the five on the stock shelf

    def _scene(self):
        return factory_scene(Entity('machine',self.editor.blueprint),recipe=self.recipe,stock=self.RUN-1,feeder=self.feeder)

    def line(self):
        """The roller conveyor feeding the source, when it does (ADR 0068), else None."""
        return conveyor_line(self.recipe) if self.feeder=='conveyor' else None

    def bind_runtime(self):
        super().bind_runtime()
        eye=camera_eye(self.backend,self.world.scene) if self.sensing=='camera' and not self.joint_lab else None
        self.cycle=None if self.joint_lab else FactoryCycle(self.backend,source=self.recipe.source,line=self.line(),eye=eye);self.factory_commands={}
        self.bind_teaching()

    def save(self):
        return self.save_program() if self.joint_lab else self.save_cell()

    def reset_cell(self):
        self.runner.stop();self.program_keys.clear();self.program_drive=None
        if not self.building:self.state=self.world.reset()
        self.paused=False;self.tray_drag=None;self.pending_source=None;self.clear_keys();self.bind_runtime()
        self.status='Cell reset. Choose a product and destination.'

    def select_feeder(self,name):
        """Feed the source by hand or with the roller conveyor (ADR 0068): the cell rebuilt, its
        layout as it was; a conveyor that does not fit there leaves the cell unchanged."""
        if not self.building:raise ValueError('Reset the cell before changing its feeder.')
        old=self.feeder
        if name==old:return
        self.feeder=name
        try:self.rebuild()
        except Exception:
            self.feeder=old;self.rebuild();raise
        self.authoring_note=('Parts ride pallets on the roller conveyor to its stop; each empty pallet goes back for the next part.'
                             if name=='conveyor' else 'Parts are put on the input tray by hand.')

    def select_sensing(self,name):
        """Find each part by the simulator's state or with the cell's overhead depth camera (ADR 0069)."""
        if not self.building:raise ValueError('Reset the cell before changing how it finds its parts.')
        if name not in ('known','camera'):raise ValueError('Unknown sensing')
        self.sensing=name;self.bind_runtime()
        self.authoring_note=('The overhead depth camera finds each part; the arm first clears its view.' if name=='camera'
                             else 'Each part is found from the simulation state, not a camera.')

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

    def start_run(self):
        """Place every part in turn: the input tray's first, then the stock shelf's, each
        fed to the input tray when the one before is placed (ADR 0019)."""
        from little_world.factory.scene import stock_name
        if self.cycle.state=='running':raise ValueError('A cycle is running: pause or reset first.')
        if self.cycle.state!='idle':raise ValueError('Reset the cell to start a production run.')
        if self.building:self.state=self.world.start()
        self.cycle.production(['objects/'+stock_name(i) for i in range(self.RUN)],self.destination)
        self.single_stage=False;self.paused=False

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

    def draw_cell_camera(self,ui,text,wh):
        """The cell camera's last depth picture - the region round the source - in the corner of
        the view, the part's pixels green, and where it saw the part (ADR 0069)."""
        eye=getattr(self.cycle,'eye',None) if self.cycle is not None else None
        picture=getattr(eye,'last',None)
        if picture is None or not picture.depth.size or self.building or self.guided:return
        rows,cols=picture.depth.shape
        scale=min(200/cols,200/rows);w,h=cols*scale,rows*scale
        x,top=self.PANEL+14,wh-74-h
        ui.pixels('cell_look',picture.colours(),x,top,w,h,version=eye.pictures)
        for rx,ry,rw,rh in ((x-2,top-2,w+4,2),(x-2,top+h,w+4,2),(x-2,top,2,h),(x+w,top,2,h)):ui.rect(rx,ry,rw,rh,(.37,.83,.69))
        ui.rect(x-2,top-38,max(w+4,220),36,(.045,.065,.085,.9))
        text('CELL CAMERA / DEPTH',x+6,top-34,10,(.68,.82,.84))
        seen=self.cycle.sightings[-1] if self.cycle.sightings else None
        if seen:
            px,py=self.cycle.trays[self.cycle.source]
            off=1000*((seen[1][0]-px)**2+(seen[1][1]-py)**2)**.5
            line=f'{seen[0].split("/")[-1]}: {off:.1f} mm from its place, {seen[3]:+.1f} deg'
        else:line='near warm, far cool, the part green'
        text(line,x+6,top-19,10,(.6,.74,.77),max(w,212)-8)

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
        source=self.pending_source or self.recipe.source
        text('From: '+('the conveyor' if self.feeder=='conveyor' and source==self.recipe.source else tray_label(source)),18,266,13)
        button('Conveyor: on' if self.feeder=='conveyor' else 'Conveyor: off',176,252,110,
               lambda:self.select_feeder('hand' if self.feeder=='conveyor' else 'conveyor'),editable,active=self.feeder=='conveyor',h=26)
        text('To: '+tray_label(self.destination),18,290,13)
        button('Locate: camera' if self.sensing=='camera' else 'Locate: known',176,280,110,
               lambda:self.select_sensing('known' if self.sensing=='camera' else 'camera'),editable,active=self.sensing=='camera',h=26)
        button('Preview path',18,321,130,self.preview_cycle,self.building,h=34)
        button(f'Run {self.RUN} parts',156,321,130,self.start_run,self.cycle.state=='idle',h=34,tone='primary')
        text('TASK SEQUENCE',18,374,12)
        labels=['Locate product with camera' if self.sensing=='camera' else 'Locate known product','Approach','Lower to grasp','Close gripper','Lift + verify','Transfer to '+tray_label(self.destination),'Lower into tray','Release','Retract + verify']
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
        run=self.cycle.run
        clock=(f'part {min(run["done"]+1,self.RUN)} of {self.RUN} / {float(self.data.time)-run["started"]:.1f}s run time' if run is not None
               else f'{self.cycle.total:.1f}s simulation time')
        text(f'{state} / {clock}',self.PANEL+18,116,13,(.4,.85,.72),ww-self.PANEL-40)
        text(self.status if self.status.startswith('Could not') else self.cycle.message,self.PANEL+18,140,12,(.8,.87,.9),ww-self.PANEL-40)
        summary=self.cycle.run_summary()
        if summary is not None:
            placed,failed,per,rate=summary
            line=f'PRODUCTION RUN  {placed} of {self.RUN} placed  /  {failed} failed'
            if per is not None:line+=f'  /  {per:.1f} s per part'
            if rate is not None:line+=f'  /  {rate:.1f} parts per minute'
            text(line,self.PANEL+18,162,12,(.96,.72,.38) if failed else (.4,.85,.72),ww-self.PANEL-40)
            arrivals=self.cycle.run.get('arrivals')
            if arrivals:
                # Where each part came to the conveyor's stop on its pallet, against its place there (ADR 0068).
                worst=max((x*x+y*y)**.5 for x,y,_ in arrivals);slowest=max(w for _,_,w in arrivals)
                n=len(arrivals)
                text(f'CONVEYOR  {n} part{"s" if n!=1 else ""} arrived at the stop  /  the worst {worst:.1f} mm from its place  /  the longest wait {slowest:.1f} s',
                     self.PANEL+18,206,12,(.4,.85,.72),ww-self.PANEL-40)
            if self.cycle.run.get('placements'):
                # Where each part landed against the room its slot gives it, and how long it took (ADR 0056).
                from little_world.factory.process import judge,line as window_line,slot_room
                from little_world.factory.controller import SLOTS
                zx,zy,turn=slot_room(SLOTS,1000*PRODUCTS[self.product][0])
                window=judge(self.cycle.run['placements'],(zx,zy),turn)
                text(window_line(window,(zx,zy)),self.PANEL+18,184,12,(.4,.85,.72) if window.inside==window.n else (.96,.72,.38),ww-self.PANEL-40)
        self.draw_cell_camera(ui,text,wh)
        if self.guided:
            title,caption=self.guide_caption();width=min(540,ww-self.PANEL-36);top=wh-162
            ui.rect(self.PANEL+18,top,width,114,(.07,.14,.17))
            text(title,self.PANEL+32,top+14,16,(.4,.9,.74),width-28)
            for i,line in enumerate(textwrap.wrap(caption,max(35,int((width-28)/7)))):text(line,self.PANEL+32,top+43+i*19,12,(.82,.89,.90),width-28)
        for name in TRAYS:
            point=self.project_table((*self.recipe.point(name),TABLE+.06))
            if point and self.PANEL+10<point[0]<ww-80 and 294<point[1]<wh-60:
                shown='Conveyor' if self.feeder=='conveyor' and name==self.recipe.source else tray_label(name)
                label=shown+(' / FROM' if name==(self.pending_source or self.recipe.source) else ' / TO' if name==self.destination else '')
                text(label,point[0]-45,point[1],11,(.5,1.,.83) if name==self.selected_tray else (.9,.94,.96),170)
        text('Arrange: drag trays. Set task: click source then destination. Escape cancels. Drag empty space to orbit.',18,wh-24,11,(.65,.75,.77),ww-36)
        self.draw_dialog(ui,button,text,ww,wh)
        ui.flush(ww,wh,fw,fh)


def main():FactoryWorkshop().run()
if __name__=='__main__':main()
