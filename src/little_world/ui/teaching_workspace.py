"""Direct target manipulation and named positions in the Real workspace."""
import time
import glfw
import numpy as np
import mujoco as mj
from little_world.factory.teaching import TeachingBook,TaughtPosition
from little_world.factory.teaching_native import TeachingMotion

class TeachingWorkspace:
    @property
    def teaching(self):return self.experiment=='Teach positions'
    @property
    def teaching_path(self):return self.recipe_path.with_name('panda-positions.json')

    def init_teaching(self):
        self.teach_point=np.array((.4,0,1.02));self.teach_drag=False;self.teach_name=''
        self.teach_book=TeachingBook();self.teach_note='Drag the target on its horizontal plane.'
        if self.teaching_path.exists():
            try:self.teach_book=TeachingBook.from_json(self.teaching_path.read_text())
            except (ValueError,TypeError,KeyError,OSError):self.teach_note='Saved positions could not be loaded. Original file preserved.'

    def bind_teaching(self):
        self.teach_motion=TeachingMotion(self.backend) if self.robot_asset=='franka_panda' else None
        self.teach_drag=False

    def change_target(self,point):
        self.teach_point=np.asarray(point,dtype=float);self.teach_name=''
        self.teach_motion.target=None;self.teach_motion.state='idle'
        self.teach_note='Target changed. Preview reach before moving.'

    def preview_teaching(self):
        try:self.teach_motion.preview(self.teach_point)
        except ValueError:pass
        self.teach_note=self.teach_motion.message

    def move_teaching(self):
        if self.teach_motion.target is None:raise ValueError('Preview a reachable target first.')
        if self.building:self.state=self.world.start()
        self.clear_keys();self.runner.stop();self.program_keys.clear()
        self.teach_motion.start();self.paused=False

    def save_taught(self,name):
        if self.teach_motion.target is None:raise ValueError('Preview a reachable position before saving.')
        book=self.teach_book.saved(TaughtPosition(name,self.teach_point))
        self.write_teaching(book);self.teach_name=name.strip();self.teach_note='Position saved. Use Recall position to reuse it.'

    def write_teaching(self,book):
        self.teaching_path.parent.mkdir(parents=True,exist_ok=True)
        temp=self.teaching_path.with_suffix('.json.tmp');temp.write_text(book.to_json());temp.replace(self.teaching_path)
        self.teach_book=book

    def name_teaching(self):
        self.form('Save taught position',[('Name',self.teach_name or 'Position '+str(len(self.teach_book.positions)+1))],lambda values:self.save_taught(values[0]),'An existing name replaces that saved position.',text_input=True)

    def recall_teaching(self):
        def recall(name):
            p=next(p for p in self.teach_book.positions if p.name==name)
            self.change_target(p.point);self.teach_name=name;self.preview_teaching()
        self.choose('Recall position',tuple(p.name for p in self.teach_book.positions),recall)

    def delete_teaching(self):
        self.write_teaching(self.teach_book.removed(self.teach_name));self.teach_name='';self.teach_note='Saved position deleted.'

    def teach_cursor(self,x,y):
        ww,wh=glfw.get_window_size(self.window)
        if not (self.PANEL<x<ww and 56<y<wh-32):return None
        a,b=self.render_scene.camera;origin=(a.pos+b.pos)/2;forward=(a.forward+b.forward)/2;up=(a.up+b.up)/2
        ratio=(a.frustum_top-a.frustum_bottom)/(2*a.frustum_near);h=wh-88;w=ww-self.PANEL
        ray=forward+np.cross(forward,up)*((x-self.PANEL-w/2)/(h/2))*ratio-up*((y-56-h/2)/(h/2))*ratio
        if abs(ray[2])<1e-6:return None
        distance=(self.teach_point[2]-origin[2])/ray[2]
        return origin+ray*distance if distance>0 else None

    def key(self,win,key,scancode,action,mods):
        if not self.teaching or self.dialog is not None:return super().key(win,key,scancode,action,mods)
        self.last_input=time.monotonic()
        if action==glfw.PRESS:
            if key in (glfw.KEY_SPACE,glfw.KEY_P) and not self.building:self.paused=not self.paused
            elif key==glfw.KEY_ESCAPE:self.teach_drag=False

    def mouse(self,win,button,action,mods):
        if self.teaching and self.dialog is None and button==glfw.MOUSE_BUTTON_LEFT:
            if action==glfw.RELEASE and self.teach_drag:
                self.teach_drag=False;self.events.append(self.preview_teaching);return
            x,y=glfw.get_cursor_pos(win)
            if action==glfw.PRESS and not any(b.x<=x<=b.x+b.width and b.y<=y<=b.y+b.height for b in self.buttons):
                point=self.project_table(self.teach_point)
                if point and np.linalg.norm(np.asarray(point)-(x,y))<25 and self.teach_motion.state!='moving':
                    self.teach_drag=True;self.teach_offset=self.teach_point.copy();self.teach_start=self.teach_cursor(x,y)
                    self.last_input=time.monotonic();return
        super().mouse(win,button,action,mods)

    def mouse_move(self,win,x,y):
        if self.teaching and self.teach_drag:
            self.last_input=time.monotonic();self.last_mouse=(x,y);point=self.teach_cursor(x,y)
            if point is not None and self.teach_start is not None:
                self.change_target(self.teach_offset+point-self.teach_start)
            return
        super().mouse_move(win,x,y)

    def draw_teaching_target(self):
        color=(.2,.85,.55,.8) if self.teach_motion.target is not None else ((1.,.25,.2,.8) if self.teach_motion.state=='unreachable' else (1.,.75,.2,.8))
        if self.render_scene.ngeom>=self.render_scene.maxgeom:return
        geom=self.render_scene.geoms[self.render_scene.ngeom]
        mj.mjv_initGeom(geom,mj.mjtGeom.mjGEOM_SPHERE,np.array((.025,)*3),self.teach_point,np.eye(3).ravel(),np.array(color,dtype=np.float32))
        geom.category=mj.mjtCatBit.mjCAT_DECOR;self.render_scene.ngeom+=1

    def draw_teaching(self,ui,button,text,ww,wh,fw,fh):
        self.draw_real_header(ui,button,text,ww,wh)
        text('TEACH POSITIONS / PANDA',18,80,13)
        button('Back to joint lab',18,108,268,lambda:self.select_experiment('Joint lab'),h=32)
        text('Drag the sphere to position the hand.',18,164,11,max_width=270)
        text('Hand orientation: pointing down.',18,188,11,max_width=270)
        text('Height: '+str(round(self.teach_point[2]*1000))+' mm',18,225,13)
        editable=self.teach_motion.state!='moving'
        button('Lower 2 cm',18,253,130,lambda:self.change_target(self.teach_point+(0,0,-.02)),editable)
        button('Raise 2 cm',156,253,130,lambda:self.change_target(self.teach_point+(0,0,.02)),editable)
        text('XYZ (m): '+', '.join(f'{v:.3f}' for v in self.teach_point),18,303,11,max_width=270)
        button('Preview reach',18,337,268,self.preview_teaching,editable,h=34)
        button('Move to target',18,379,268,self.move_teaching,editable and self.teach_motion.target is not None,h=36,tone='primary')
        button('Resume' if self.paused else 'Pause',18,423,130,lambda:setattr(self,'paused',not self.paused),not self.building)
        button('Reset',156,423,130,self.reset_cell)
        button('Save position',18,470,268,self.name_teaching,editable and self.teach_motion.target is not None)
        button('Recall position',18,511,268,self.recall_teaching,editable and bool(self.teach_book.positions))
        button('Delete saved position',18,552,268,self.delete_teaching,editable and bool(self.teach_name))
        text('Saved: '+(self.teach_name or str(len(self.teach_book.positions))+' positions'),18,600,11,max_width=270)
        text('Reach check only. No obstacle avoidance.',18,wh-60,10,(.95,.74,.4),270)
        text(self.teach_motion.message if self.teach_motion.state in ('moving','reached','failed') else self.teach_note,self.PANEL+18,80,12,max_width=ww-self.PANEL-36)
        text('Gold: unchecked   Green: reachable   Red: unreachable',self.PANEL+18,104,11,max_width=ww-self.PANEL-36)
        text(self.status if self.status.startswith('Could not') else 'Drag empty space to orbit. Preview never moves the robot.',18,wh-24,11,max_width=ww-36)
        self.draw_dialog(ui,button,text,ww,wh);ui.flush(ww,wh,fw,fh)
