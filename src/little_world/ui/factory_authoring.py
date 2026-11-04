"""Direct scene authoring and contextual teaching for the native factory cell."""
from dataclasses import replace
from pathlib import Path
import time
import glfw
import numpy as np
import mujoco as mj
from little_world.factory.recipe import CellRecipe,TRAYS
from little_world.factory.scene import TABLE

EXPLANATIONS=(
 ('Approach','The computer calculates joint positions that put the open hand above the source. You choose the job, not seven joint angles.'),
 ('Lower','The hand descends with its fingers open. The product position comes from known simulator state, not camera recognition.'),
 ('Grasp','The fingers close against the product. Both sides must make contact before the task continues.'),
 ('Lift','The robot lifts using friction and contact. We check whether the product actually rose; it is never glued to the hand.'),
 ('Transfer','The arm carries the product to the chosen destination. This simple planner does not route around arbitrary obstacles.'),
 ('Place','The hand lowers into the destination tray. Finite motor forces and contact determine the actual motion.'),
 ('Release','The fingers open and the product settles under gravity. Opening the hand does not guarantee a correct placement.'),
 ('Verify','The hand retracts, then the controller checks whether the product is inside the selected tray.'),
)

def tray_label(name):return 'Input tray' if name=='input' else name+' tray'

class FactoryAuthoring:
    def init_authoring(self,recipe_path):
        self.recipe_path=Path(recipe_path) if recipe_path else Path.home()/'Library/Application Support/Little World/factory-cell.json'
        self.recipe=CellRecipe();self.recipe_history=[];self.edit_mode='Arrange'
        self.pending_source=None;self.tray_drag=None;self.selected_tray='input';self.guided=False
        self.authoring_note='Drag a tray on the table. The robot and camera stay fixed.'
        if self.recipe_path.exists():
            try:self.recipe=CellRecipe.from_json(self.recipe_path.read_text())
            except (ValueError,TypeError,OSError):self.authoring_note='Saved cell could not be loaded. Using the starter layout.'

    @property
    def product(self):return self.recipe.product
    @property
    def destination(self):return self.recipe.destination

    def apply_recipe(self,recipe,remember=True):
        if not self.building:raise ValueError('Reset the cell before changing its layout or task.')
        old=self.recipe
        if old==recipe:return
        self.recipe=recipe
        try:self.rebuild()
        except Exception:
            self.recipe=old;self.rebuild();raise
        self.recipe_revision+=1
        if remember:
            self.recipe_history.append(old);self.recipe_future.clear()
        self.authoring_note='Cell updated. Preview checks the robot motion.'

    def undo_recipe(self):
        if self.recipe_history:
            previous=self.recipe_history[-1];current=self.recipe
            self.apply_recipe(previous,False);self.recipe_history.pop();self.recipe_future.append(current)
            self.authoring_note='Last cell edit undone.'

    def redo_recipe(self):
        if self.recipe_future:
            following=self.recipe_future[-1];current=self.recipe
            self.apply_recipe(following,False);self.recipe_future.pop();self.recipe_history.append(current)
            self.authoring_note='Cell edit restored.'

    def save_cell(self):
        self.recipe_path.parent.mkdir(parents=True,exist_ok=True)
        temp=self.recipe_path.with_suffix('.json.tmp');temp.write_text(self.recipe.to_json());temp.replace(self.recipe_path)
        self.authoring_note='Cell layout and task saved.'

    def choose_mode(self,mode):
        self.edit_mode=mode;self.pending_source=None;self.tray_drag=None
        self.authoring_note='Click the tray to pick FROM, then the tray to place INTO.' if mode=='Set task' else 'Drag a tray on the table. The robot and camera stay fixed.'

    def choose_task_tray(self,name):
        if not self.building:return
        if self.pending_source is None:
            self.pending_source=name;self.authoring_note='Source: '+tray_label(name)+'. Now click a different destination tray.'
        elif name==self.pending_source:self.authoring_note='Choose a different tray for the destination.'
        else:
            self.apply_recipe(replace(self.recipe,source=self.pending_source,destination=name))
            self.pending_source=None;self.authoring_note='Task connected. Preview the path, then Run cycle.'

    def enter_guide(self):
        self.reset_cell();self.guided=True
        self.authoring_note='A live physics demonstration. Next step runs one stage and pauses.'

    def guide_caption(self):
        if self.cycle.state=='failed':return 'What stopped the task',self.cycle.message
        if self.cycle.state=='completed':return 'Placement verified','The product lifted and reached the selected tray. Try it yourself: move a tray or change the source, then preview a new path.'
        if self.cycle.state in ('idle','planned'):return 'How picking works','Choose Next step to run each stage with real simulated contact. The demonstration pauses so you can inspect what happened.'
        return EXPLANATIONS[self.cycle.index]

    def try_yourself(self):
        self.reset_cell();self.guided=False;self.choose_mode('Arrange')

    def table_cursor(self,x,y):
        ww,wh=glfw.get_window_size(self.window)
        if not (self.PANEL<x<ww and 56<y<wh-32):return None
        a,b=self.render_scene.camera
        origin=(a.pos+b.pos)/2;forward=(a.forward+b.forward)/2;up=(a.up+b.up)/2
        ratio=(a.frustum_top-a.frustum_bottom)/(2*a.frustum_near)
        h=wh-88;w=ww-self.PANEL
        direction=forward+np.cross(forward,up)*((x-self.PANEL-w/2)/(h/2))*ratio-up*((y-56-h/2)/(h/2))*ratio
        if direction[2]>=-1e-6:return None
        distance=(TABLE+.025-origin[2])/direction[2]
        if distance<=0:return None
        return origin+direction*distance

    def project_table(self,point):
        ww,wh=glfw.get_window_size(self.window);a,b=self.render_scene.camera
        origin=(a.pos+b.pos)/2;forward=(a.forward+b.forward)/2;up=(a.up+b.up)/2
        p=np.asarray(point)-origin;depth=float(p@forward)
        if depth<=0:return None
        ratio=(a.frustum_top-a.frustum_bottom)/(2*a.frustum_near);scale=(wh-88)/2/(ratio*depth)
        return (self.PANEL+(ww-self.PANEL)/2+float(p@np.cross(forward,up))*scale,
                56+(wh-88)/2-float(p@up)*scale)

    def tray_at(self,x,y):
        p=self.table_cursor(x,y)
        if p is None:return None
        return next((name for name in TRAYS if abs(p[0]-self.recipe.point(name)[0])<=.10 and abs(p[1]-self.recipe.point(name)[1])<=.09),None)

    def mouse(self,win,button,action,mods):
        if self.dialog is not None or getattr(self,'joint_lab',False):return super().mouse(win,button,action,mods)
        self.last_input=time.monotonic();x,y=glfw.get_cursor_pos(win)
        if button==glfw.MOUSE_BUTTON_LEFT:
            if action==glfw.RELEASE and self.tray_drag:
                drag=self.tray_drag;self.tray_drag=None
                if drag['moved'] and drag['candidate'] is not None:self.events.append(lambda r=drag['candidate']:self.apply_recipe(r))
                return
            if action==glfw.PRESS:
                for item in self.buttons:
                    if item.x<=x<=item.x+item.width and item.y<=y<=item.y+item.height:
                        if item.enabled:self.events.append(item.action)
                        return
                name=self.tray_at(x,y) if self.building and not self.guided else None
                if name:
                    self.selected_tray=name
                    if self.edit_mode=='Set task':self.events.append(lambda n=name:self.choose_task_tray(n))
                    else:
                        p=self.table_cursor(x,y)
                        self.tray_drag=dict(name=name,start=(x,y),offset=p[:2]-self.recipe.point(name),point=self.recipe.point(name),candidate=self.recipe,moved=False)
                    return
        super().mouse(win,button,action,mods)

    def mouse_move(self,win,x,y):
        if getattr(self,'joint_lab',False):return super().mouse_move(win,x,y)
        if self.tray_drag:
            self.last_input=time.monotonic();self.last_mouse=(x,y);drag=self.tray_drag
            if abs(x-drag['start'][0])+abs(y-drag['start'][1])<4 and not drag['moved']:return
            drag['moved']=True;p=self.table_cursor(x,y);drag['candidate']=None
            if p is None:self.authoring_note='Keep the tray over the table.';return
            point=np.round((p[:2]-drag['offset'])/.01)*.01;drag['point']=tuple(point)
            try:
                candidate=self.recipe.moved(drag['name'],point)
                if getattr(self,'feeder','hand')=='conveyor':
                    from little_world.factory.scene import conveyor_line
                    conveyor_line(candidate)        # the conveyor follows the source; it must fit (ADR 0068)
                drag['candidate']=candidate
                self.authoring_note='Fits the table. Release to place; Preview checks reach.'
            except ValueError as error:self.authoring_note=str(error)
            return
        super().mouse_move(win,x,y)

    def draw_tray_ghost(self):
        if not self.tray_drag or not self.tray_drag['moved']:return
        x,y=self.tray_drag['point'];valid=self.tray_drag['candidate'] is not None
        color=np.array((.15,.9,.6,.65) if valid else (1.,.25,.2,.65),dtype=np.float32)
        shapes=[((.20,.18,.008),(x,y,TABLE+.007))]
        for sign in (-1,1):
            shapes.extend([((.008,.18,.035),(x+sign*.096,y,TABLE+.0285)),((.184,.008,.035),(x,y+sign*.086,TABLE+.0285))])
        for size,pos in shapes:
            geom=self.render_scene.geoms[self.render_scene.ngeom]
            mj.mjv_initGeom(geom,mj.mjtGeom.mjGEOM_BOX,np.asarray(size)/2,np.asarray(pos),np.eye(3).ravel(),color)
            geom.category=mj.mjtCatBit.mjCAT_DECOR;self.render_scene.ngeom+=1
