"""Build / simulate workshop; all construction edits go through AssemblyEditor."""
from dataclasses import dataclass
from pathlib import Path
import os
import sys
import time
import glfw
import mujoco as mj
import numpy as np
from little_world import Blueprint, Entity, World
from little_world.core.component import Motor
from little_world.core.world import Mode
from little_world.construction.editor import AssemblyEditor, starter_blueprint
from little_world.physics.mujoco_backend import MujocoBackend
from little_world.robots.two_wheel import two_wheel_blueprint
from little_world.scenes.workshop import workshop_scene
from .controls import DriveInput
from .canvas import Canvas
from .inspector import PrecisionInspector
from .build_workspace import BuildWorkspace
from .key_bindings import KeyBindings


@dataclass
class Button:
    label: str
    x: float
    y: float
    width: float
    height: float
    action: object
    enabled: bool = True
    active: bool = False


from .program_workspace import ProgramWorkspace
from .guided_build import GuidedBuild
from .test_workspace import TestWorkspace
from .inventory_workspace import InventoryWorkspace


from .python_workspace import PythonWorkspace


from .app_modes import AppModes


class Workshop(AppModes, PythonWorkspace, PrecisionInspector, BuildWorkspace, KeyBindings, ProgramWorkspace, GuidedBuild, TestWorkspace, InventoryWorkspace):
    PANEL = 288

    def __init__(self, path, blueprint=None):
        self.path = Path(path)
        self.editor = AssemblyEditor(blueprint or two_wheel_blueprint())
        self.backend = MujocoBackend()
        self.world = World(self.backend, self._scene())
        self.camera = mj.MjvCamera()
        self.option = mj.MjvOption()
        self.context = None
        self.window = None
        self.buttons = []
        self.events = []
        self.controls = DriveInput()
        self.held_codes = set()
        self.last_mouse = (0, 0)
        self.press_mouse = None
        self.status = 'Select a part in the scene or in the part list.'
        self.follow = False
        self.initial_camera = None
        self.part_offset = 0
        self.channels = []
        self.state = None
        self.paused = False
        self.active_tab = "Edit"
        self.library_open = True
        self.catalog_category = 'All'
        self.catalog_offset = 0
        self.catalog_selection = 'chassis_plate'
        self.catalog_mount = 'Default'
        self.preview_cache = {}
        self.preview_drag = False
        self.canvas = None
        self.last_input = time.monotonic()
        self.init_inspector()
        self.init_build_workspace()
        self.init_key_bindings()
        self.init_program()
        self.init_inventory()
        self.init_python()

    def _scene(self):
        return workshop_scene(Entity('machine', self.editor.blueprint))

    @property
    def building(self):
        return self.world.mode == Mode.BUILD

    def clear_keys(self):
        self.held_codes.clear()
        self.controls.clear()
        self.joint_control.clear()
        self.motor_test = None

    def rebuild(self):
        """Only called with an active GL context and World in BUILD."""
        self.world.set_scene(self._scene())
        self.state = self.world.preview()
        self.bind_runtime()

    def bind_runtime(self):
        self.model, self.data = self.backend.model, self.backend.data
        from little_world.programming.observations import Observations
        self.observations=Observations(self.model,self.data)
        self.grip_history={};self.possible_slips=set()
        if not hasattr(self, 'render_scene'):
            self.render_scene = mj.MjvScene(self.model, maxgeom=10000)
        ratio = glfw.get_framebuffer_size(self.window)[0] / max(1, glfw.get_window_size(self.window)[0])
        # Primitive geometry and the fixed texture registry let fonts/FBOs
        # remain alive across model edits without re-uploading assets.
        if self.context is not None and getattr(self,'_render_model',None) is not self.model and (self.model.nmesh or getattr(self,'_had_meshes',False)):
            self.context.free();self.context=None
        self._render_model=self.model;self._had_meshes=bool(self.model.nmesh)
        if self.context is None:
            self.context = mj.MjrContext(self.model, 150)
            if self.canvas is None:self.canvas = Canvas(ratio)
        self.channels = []
        self.root_id = -1
        self.bind_joint_runtime()
        from little_world.control.mujoco_drive import MujocoDrive
        self.drive_control=MujocoDrive(self.backend,self.editor.blueprint)
        self.channels=[c[:3] for c in self.drive_control.channels]
        root = next((b for b in self.editor.bodies if b.parent is None), None)
        if root:
            self.root_id = self.model.body('machine/' + root.id).id
        if self.camera.type == mj.mjtCamera.mjCAMERA_FIXED and not self.model.ncam:
            self.camera.type = mj.mjtCamera.mjCAMERA_FREE
        self.highlight()

    def highlight(self):
        # Preserve the actual surface. Selection is a visual-only edge cage.
        for b in self.editor.bodies:
            if b.robot_asset:continue
            geom=self.model.geom('machine/'+b.id+'_geom').id
            mat=next(m for m in self.editor.blueprint.materials if m.id==b.material)
            self.model.geom_rgba[geom]=mat.rgba

    def selection_outline(self, scene=None):
        scene = self.render_scene if scene is None else scene
        if not self.building or self.editor.selected is None:
            return
        body=self.editor.selected
        idx=self.model.geom('machine/'+body.id+'_geom').id
        size=self.model.geom_size[idx].copy()
        if body.geometry.shape=='cylinder':
            size=np.array((size[0],size[0],size[1]))
        elif body.geometry.shape=='sphere':
            size[:]=size[0]
        size+=.002
        corners=np.array([(x,y,z) for x in (-size[0],size[0]) for y in (-size[1],size[1]) for z in (-size[2],size[2])])
        corners=corners@self.data.geom_xmat[idx].reshape(3,3).T+self.data.geom_xpos[idx]
        for i in range(8):
            for bit in (1,2,4):
                j=i^bit
                if j<=i or scene.ngeom>=scene.maxgeom:
                    continue
                geom=scene.geoms[scene.ngeom]
                mj.mjv_initGeom(geom,mj.mjtGeom.mjGEOM_CAPSULE,np.zeros(3),np.zeros(3),np.eye(3).ravel(),np.array((.3,.95,.72,1),dtype=np.float32))
                mj.mjv_connector(geom,mj.mjtGeom.mjGEOM_CAPSULE,.0007,corners[i],corners[j])
                geom.category=mj.mjtCatBit.mjCAT_DECOR
                scene.ngeom+=1

    def home(self, room=False):
        self.camera.type = mj.mjtCamera.mjCAMERA_FREE
        self.camera.lookat[:] = (.1, .45, .3) if room else (0, 0, .15)
        self.camera.distance = 5.4 if room else 2.
        self.camera.azimuth, self.camera.elevation = 125, -32
        self.follow = False

    def edit(self, operation):
        if not self.building:
            self.status = 'Stop simulation before changing the design.'
            return
        old = (self.editor.blueprint, self.editor.selection, list(self.editor.past), list(self.editor.future))
        try:
            operation()
            if self.editor.blueprint != old[0]:
                self.rebuild()
            self.status = 'Design updated. Simulate to test the result.'
        except Exception:
            self.editor.blueprint, self.editor.selection, self.editor.past, self.editor.future = old
            self.rebuild()
            raise

    def simulate(self):
        self.runner.stop()
        self.program_keys.clear()
        self.clear_keys()
        self.paused = False
        if self.building:
            self.state = self.world.start()
            self.bind_runtime()
            from little_world.construction.docking import catalog_id
            wheels=[b for b in self.editor.bodies if catalog_id(b.id) in ('drive_left','drive_right','wheel_small','wheel_large','tread_wheel')]
            if wheels and not any(b.dynamic for b in self.editor.bodies):
                self.status='Base is anchored. Return to Build and click Free base + ground to enable movement.'
            elif wheels and not self.channels:
                self.status='No paired drive control. Passive wheels need motors; add left and right powered wheel modules for WASD.'
            else:self.status = 'Physics is running. Hold WASD to drive; release to brake.' if self.channels else 'Physics is running. Stop to return to the saved design.'
        else:
            self.state = self.world.reset()
            self.joint_control.reset()
            self.highlight()
            self.status = 'Back in BUILD. The design is restored; simulation changes are discarded.'

    def export_parts(self):
        from little_world.construction.build_report import build_report
        path=self.path.with_suffix('.parts.csv')
        path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_suffix(path.suffix+'.tmp')
        temporary.write_text(build_report(self.editor.blueprint))
        temporary.replace(path)
        self.status='Exported candidate motors + custom parts: '+str(path)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + '.tmp')
        temporary.write_text(self.editor.blueprint.to_json() + '\n')
        temporary.replace(self.path)
        self.save_program()
        self.status = 'Saved design and program: ' + str(self.path.name)

    def load(self):
        from little_world.programming.program import Program
        if not self.building:raise ValueError('Stop simulation before loading')
        blueprint = Blueprint.from_json(self.path.read_text())
        program=Program.from_json(self.program_path.read_text()) if self.program_path.exists() else Program()
        self.edit(lambda: self.editor.load(blueprint))
        self.program_edit(program)
        self.status = 'Loaded: ' + str(self.path.name)

    def select(self, name):
        self.editor.select(name)
        self.connect_parent = None
        self.highlight()

    def camera_toggle(self):
        if not self.model.ncam:
            self.status = 'Attach a camera to a selected part first.'
        else:
            self.camera.type = (mj.mjtCamera.mjCAMERA_FREE if self.camera.type == mj.mjtCamera.mjCAMERA_FIXED
                                else mj.mjtCamera.mjCAMERA_FIXED)
            self.camera.fixedcamid = 0

    def key(self, win, key, scancode, action, mods):
        self.last_input = time.monotonic()
        if self.dialog is not None:
            self.dialog_key(key,action,mods)
            return
        if self.script_key(key,action,mods):return
        if self.parts_key(key,action,mods):return
        if self.part_drag is not None and action==glfw.PRESS and key==glfw.KEY_ESCAPE:
            self.cancel_docking();self.status='Drag cancelled.';return
        if self.inventory_open:
            if action==glfw.PRESS and key==glfw.KEY_ESCAPE:self.inventory_open=False
            return
        if action==glfw.PRESS and key==getattr(glfw,'KEY_'+self.program.trigger):
            self.events.append(self.start_program);return
        if self.runner.state in ('running','paused') and action==glfw.PRESS:
            if key==glfw.KEY_SPACE:self.stop_program();return
            if key==glfw.KEY_P:self.pause_program();return
            if key in range(32,127) or key in (glfw.KEY_UP,glfw.KEY_DOWN,glfw.KEY_LEFT,glfw.KEY_RIGHT):return
        if self.control_panel and action == glfw.PRESS and key == glfw.KEY_ESCAPE:
            self.control_panel=False
            return
        if not self.building:
            mapped={k for c in self.joint_control.specs for k in (c.positive_key,c.negative_key)}
            letter=chr(key) if 0<=key<128 else ''
            if letter in mapped:
                if action==glfw.RELEASE:
                    self.joint_control.release(letter)
                elif action==glfw.PRESS and not mods & (glfw.MOD_CONTROL | glfw.MOD_SUPER):
                    self.joint_control.press(letter)
                return
        if self.bench_open:
            if action == glfw.PRESS and key == glfw.KEY_ESCAPE:
                self.close_bench()
            elif action == glfw.PRESS and key == glfw.KEY_S and mods & (glfw.MOD_CONTROL | glfw.MOD_SUPER):
                self.events.append(self.save)
            elif action == glfw.PRESS and key == glfw.KEY_Z and mods & (glfw.MOD_CONTROL | glfw.MOD_SUPER):
                operation=self.editor.redo if mods & glfw.MOD_SHIFT else self.editor.undo
                self.events.append(lambda:self.edit(operation))
            elif action == glfw.PRESS and key == glfw.KEY_D and mods & (glfw.MOD_CONTROL | glfw.MOD_SUPER):
                if self.editor.selected:
                    self.events.append(self.duplicate_form)
            elif action == glfw.PRESS and key == glfw.KEY_F:
                self.events.append(self.focus_bench)
            return
        aliases = {glfw.KEY_W:'W', glfw.KEY_UP:'W', glfw.KEY_S:'S', glfw.KEY_DOWN:'S',
                   glfw.KEY_A:'A', glfw.KEY_LEFT:'A', glfw.KEY_D:'D', glfw.KEY_RIGHT:'D'}
        command = bool(mods & (glfw.MOD_CONTROL | glfw.MOD_SUPER))
        if key in aliases and not self.building:
            if action == glfw.PRESS and not command:
                self.held_codes.add(key)
            elif action == glfw.RELEASE:
                self.held_codes.discard(key)
            self.controls.clear()
            for code in self.held_codes:
                self.controls.press(aliases[code])
        if action != glfw.PRESS:
            return
        command = bool(mods & (glfw.MOD_CONTROL | glfw.MOD_SUPER))
        if command and key == glfw.KEY_S:
            self.events.append(self.save)
        elif command and key == glfw.KEY_Z:
            self.events.append(lambda: self.edit(self.editor.undo))
        elif key == glfw.KEY_ENTER:
            self.events.append(self.simulate)
        elif key == glfw.KEY_SPACE:
            self.clear_keys()
        elif key == glfw.KEY_P and not self.building:
            self.paused = not self.paused
            self.clear_keys()
        elif key == glfw.KEY_HOME:
            self.home()
        elif key == glfw.KEY_F:
            self.follow = not self.follow
            self.camera.type = mj.mjtCamera.mjCAMERA_FREE
        elif key == glfw.KEY_C:
            self.events.append(self.camera_toggle)
        elif key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(win, True)

    def mouse(self, win, button, action, mods):
        self.last_input = time.monotonic()
        x, y = glfw.get_cursor_pos(win)
        if button != glfw.MOUSE_BUTTON_LEFT:
            return
        if self.script_mouse(x,y,action):return
        if self.inventory_open:
            if action==glfw.PRESS:
                for item in self.buttons:
                    if item.x<=x<=item.x+item.width and item.y<=y<=item.y+item.height:
                        if item.enabled:self.events.append(item.action)
                        return
            return
        if self.parts_mouse(x,y,action):return
        if self.docking_mouse(x,y,action):return
        if self.program_mouse(x,y,action):return
        if action == glfw.RELEASE and self.preview_drag:
            self.preview_drag=False
            return
        if self.bench_open and self.dialog is None and not self.over_controls(x,y) and self.bench_contains(x,y):
            if action == glfw.PRESS:
                self.press_mouse=(x,y)
            elif action == glfw.RELEASE and self.press_mouse:
                px,py=self.press_mouse
                self.press_mouse=None
                if abs(x-px)+abs(y-py)<5:
                    self.events.append(lambda:self.bench_pick(x,y))
            return
        if self.dialog is None and action == glfw.PRESS and self.over_preview(x,y):
            self.preview_drag=True
            return
        if action == glfw.PRESS:
            self.press_mouse = None if self.dialog is not None or self.over_controls(x,y) else (x, y)
            for item in self.buttons:
                if item.x <= x <= item.x+item.width and item.y <= y <= item.y+item.height:
                    self.press_mouse = None
                    if item.enabled:
                        self.events.append(item.action)
                    return
        elif not self.bench_open and self.dialog is None and action == glfw.RELEASE and self.press_mouse:
            px, py = self.press_mouse
            self.press_mouse = None
            if px >= self.PANEL and 56 < py < glfw.get_window_size(win)[1]-32 and abs(x-px)+abs(y-py) < 5 and self.building:
                self.events.append(lambda: self.pick(x, y))

    def pick(self, x, y):
        width, height = glfw.get_window_size(self.window)
        point = np.zeros(3)
        ids = [np.zeros(1, dtype=np.int32) for _ in range(3)]
        body = mj.mjv_select(self.model, self.data, self.option, (width-self.PANEL-(338 if self.control_panel else 0))/(height-88),
                            (x-self.PANEL)/(width-self.PANEL-(338 if self.control_panel else 0)), 1-(y-56)/(height-88),
                            self.render_scene, point, *ids)
        if body >= 0:
            name = self.model.body(body).name
            if name.startswith('machine/'):
                self.select(self.backend.robot_owners.get(name,name).split('/',1)[1])
                return
        self.status = 'Select a machine part. Room objects are not part of this design.'

    def mouse_move(self, win, x, y):
        if self.script_open:return
        if self.inventory_open:return
        self.last_input = time.monotonic()
        dx, dy = x-self.last_mouse[0], y-self.last_mouse[1]
        self.last_mouse = x, y
        if self.parts_move(y):return
        if self.part_drag is not None and self.docking_move(x,y):return
        if self.dialog is not None or self.over_controls(x,y):
            return
        if self.preview_drag and self.catalog_selection in self.preview_cache:
            camera=self.preview_cache[self.catalog_selection][3]
            camera.azimuth+=dx*.5
            camera.elevation=max(-85,min(85,camera.elevation+dy*.5))
            return
        if self.bench_open:
            if self.bench_contains(x,y) and self.bench_cache is not None:
                _,model,data,scene=self.bench_cache
                right=glfw.get_mouse_button(win,glfw.MOUSE_BUTTON_RIGHT)==glfw.PRESS
                left=glfw.get_mouse_button(win,glfw.MOUSE_BUTTON_LEFT)==glfw.PRESS
                if right or (left and self.press_mouse is not None):
                    mj.mjv_moveCamera(model,mj.mjtMouse.mjMOUSE_MOVE_V if right else mj.mjtMouse.mjMOUSE_ROTATE_V,
                                     dx/self.bench_rect[3],dy/self.bench_rect[3],scene,self.bench_camera)
            return
        if x < self.PANEL or not 56 < y < glfw.get_window_size(win)[1]-32 or self.camera.type == mj.mjtCamera.mjCAMERA_FIXED:
            return
        height = max(glfw.get_window_size(win)[1], 1)
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS:
            action = mj.mjtMouse.mjMOUSE_MOVE_V
            self.follow = False
        elif glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
            if self.press_mouse is None or self.press_mouse[0] < self.PANEL:
                return
            action = mj.mjtMouse.mjMOUSE_ROTATE_V
        else:
            return
        mj.mjv_moveCamera(self.model, action, dx/height, dy/height, self.render_scene, self.camera)

    def scroll(self, win, xoffset, yoffset):
        if self.script_open and self.dialog is None:
            self.script_scroll=max(0,self.script_scroll-int(yoffset*3));return
        if self.inventory_open:return
        self.last_input = time.monotonic()
        x, y = glfw.get_cursor_pos(win)
        if self.dialog is None and self.bench_open and (self.bench_parts or self.bench_details) and self.bench_tab=='Library' and 16<=x<=290 and 215<=y<=glfw.get_window_size(win)[1]-100:
            self.parts_set_scroll(self.parts_scroll-yoffset*38)
            return
        if self.dialog is not None or self.over_controls(x,y):
            return
        if self.over_preview(x,y) and self.catalog_selection in self.preview_cache:
            camera=self.preview_cache[self.catalog_selection][3]
            camera.distance=max(.05,min(3,camera.distance*(.9**yoffset)))
        elif self.bench_open:
            if self.bench_contains(x,y):
                self.bench_camera.distance=max(.04,min(10,self.bench_camera.distance*(.9**yoffset)))
            elif x<290:
                if self.bench_tab=='Assembly':
                    self.bench_tree_offset=max(0,self.bench_tree_offset-int(yoffset))
                else:
                    self.bench_offset=max(0,self.bench_offset-int(yoffset))
        elif x < self.PANEL:
            if self.active_tab == 'Edit' and 143 <= y <= 286:
                self.part_offset = max(0, min(max(0, len(self.editor.bodies)-4), self.part_offset-int(yoffset)))
        elif 56 < y < glfw.get_window_size(win)[1]-32 and self.camera.type != mj.mjtCamera.mjCAMERA_FIXED:
            mj.mjv_moveCamera(self.model, mj.mjtMouse.mjMOUSE_ZOOM, 0, -.05*yoffset, self.render_scene, self.camera)
            self.camera.distance = max(.4, min(15, self.camera.distance))

    def navigate_workspace(self, destination):
        """Switch workspaces without losing the authored design or program."""
        self.inventory_open=False
        self.script_open=False
        self.clear_keys()
        if destination=='Python':self.show_python()
        elif destination=='Build':
            if not self.building:self.simulate()
            self.control_panel=False
            self.open_bench()
        elif destination=='Program':self.show_program()
        elif destination=='Test':self.show_test()
        elif destination=='Inventory':self.show_inventory()

    def open_factory(self):
        self.switch_workspace('Real')

    def draw_navigation(self,ui,button,text,ww):
        ui.rect(0,0,ww,56,(.045,.065,.085))
        ui.rect(0,55,ww,1,(.18,.25,.29))
        text('little world',18,16,19,(.91,.95,.94))
        current=('Python' if self.script_open else 'Inventory' if self.inventory_open else 'Build' if self.bench_open else
                 self.panel_mode.title() if self.control_panel else '')
        self.draw_mode_switch(button)
        x=316
        for label,destination,width in (('Build','Build',80),('Program','Program',76),('Test','Test',52),('Inventory','Inventory',80)):
            button(label,x,10,width,lambda d=destination:self.navigate_workspace(d),active=current==destination,h=36)
            x+=width+6
        button('Python',628,10,62,lambda:self.navigate_workspace('Python'),active=self.script_open,h=36)
        button('Save',ww-328,10,92,self.save,h=36,tone='primary')
        if self.inventory_open:
            button('Save current version',ww-226,10,210,self.save_inventory_form,h=36,tone='primary')
        else:
            def simulate():
                self.script_open=False
                self.close_bench()
                self.simulate()
            button('SIMULATE  >' if self.building else 'STOP / RETURN TO BUILD',
                   ww-226,10,210,simulate,h=36,tone='primary' if self.building else 'danger')

    def draw(self):
        self.script_poll()
        ww,wh=glfw.get_window_size(self.window)
        fw,fh=glfw.get_framebuffer_size(self.window)
        if not fw or not fh:
            return
        sx,sy=fw/ww,fh/wh
        viewport=mj.MjrRect(int(self.PANEL*sx),int(32*sy),int((ww-self.PANEL-(338 if self.control_panel else 0))*sx),int((wh-88)*sy))
        if self.follow and self.root_id>=0 and self.camera.type!=mj.mjtCamera.mjCAMERA_FIXED:
            self.camera.lookat[:]=self.data.xpos[self.root_id]
        if not self.bench_open and not self.inventory_open and not self.script_open:
            mj.mjv_updateScene(self.model,self.data,self.option,None,self.camera,mj.mjtCatBit.mjCAT_ALL,self.render_scene)
            self.selection_outline()
            self.connection_overlay()
            if getattr(self,'factory_mode',False):self.decorate_scene()
            mj.mjr_render(viewport,self.render_scene,self.context)
        ui=self.canvas
        ui.begin()
        self.buttons=[]
        mouse=glfw.get_cursor_pos(self.window)
        muted=(.49,.57,.63)
        accent=(.37,.83,.69)

        def text(label,x,y,size=14,color=(.86,.90,.93),max_width=None):
            ui.text(label,x,y,color,size,max_width)

        def button(label,x,y,w,operation,enabled=True,active=False,h=32,tone=None):
            self.buttons.append(Button(label,x,y,w,h,operation,enabled,active))
            hover=enabled and x<=mouse[0]<=x+w and y<=mouse[1]<=y+h
            bg=(.13,.32,.28) if active else ((.20,.26,.31) if hover else (.13,.17,.21))
            if tone=='primary':bg=(.22,.68,.55) if hover else (.16,.55,.44)
            if tone=='danger':bg=(.40,.19,.20) if hover else (.27,.14,.16)
            if not enabled:
                bg=(.095,.12,.15)
            ui.rect(x,y,w,h,bg)
            if active:
                ui.rect(x,y,2,h,accent)
            label_width=ui.width(label,13)
            text(label,x+max(8,(w-label_width)/2),y+(h-16)/2,13,
                 (.9,.95,.96) if enabled else (.34,.40,.45),w-12)

        def section(label,y):
            text(label,16,y,11,muted)

        if getattr(self,'factory_mode',False):
            self.draw_factory(ui,button,text,ww,wh,fw,fh);return
        if self.script_open:
            self.draw_python(ui,button,text,ww,wh,fw,fh);return
        if self.inventory_open:
            self.draw_inventory(ui,button,text,ww,wh,fw,fh)
            ui.flush(ww,wh,fw,fh)
            return
        if self.bench_open:
            self.draw_bench(ui,button,text,section,ww,wh,fw,fh)
            self.draw_control_panel(ui,button,text,ww,wh,fw,fh)
            self.draw_dialog(ui,button,text,ww,wh)
            ui.flush(ww,wh,fw,fh)
            return

        if self.control_panel:
            ui.rect(ww-338,56,338,wh-88,(.055,.077,.097))
        ui.rect(0,0,ww,56,(.055,.077,.097))
        ui.rect(0,56,self.PANEL,wh-88,(.075,.099,.125))
        ui.rect(0,wh-32,ww,32,(.055,.077,.097))
        ui.rect(self.PANEL-1,56,1,wh-88,(.16,.21,.25))
        self.draw_navigation(ui,button,text,ww)
        tab_x=12
        for tab,tab_width in zip(('Edit','Add','Connect','Files'),(56,52,82,56)):
            button(tab,tab_x,70,tab_width,lambda t=tab:setattr(self,'active_tab',t),active=self.active_tab==tab)
            tab_x+=tab_width+6
        selected=self.editor.selected
        enable=self.building and selected is not None
        if self.active_tab=='Edit':
            section('PARTS  /  click in the room to select',120)
            for i,body in enumerate(self.editor.bodies[self.part_offset:self.part_offset+4]):
                button(body.id,12,143+i*29,264,lambda n=body.id:self.select(n),self.building,
                       body.id==self.editor.selection,h=26)
            if not self.editor.bodies:
                text('Add a part to start your design.',16,148,13,muted)
            section(f'{len(self.editor.bodies)} parts  |  Scroll here for more',268)
            ui.rect(12,294,264,1,(.16,.21,.25))
            text(selected.id if selected else 'Nothing selected',16,308,16,max_width=252)
            if selected:
                text(selected.geometry.shape+'  /  '+selected.material,16,334,12,muted)
                position='  '.join(f'{axis} {v:.2f}' for axis,v in zip('XYZ',selected.transform.position))
            button('Exact dimensions & pose',12,353,264,self.exact_form,enable,h=25)
            section('MOVE  /  5 cm per click',386)
            for i,axis in enumerate('XYZ'):
                delta=tuple(.05 if j==i else 0 for j in range(3))
                button(axis+' -',12+i*90,405,40,lambda d=delta:self.edit(lambda:self.editor.move(tuple(-v for v in d))),enable)
                button(axis+' +',56+i*90,405,40,lambda d=delta:self.edit(lambda:self.editor.move(d)),enable)
            button('Rotate -15',12,449,128,lambda:self.edit(lambda:self.editor.rotate(-15)),enable)
            button('Rotate +15',148,449,128,lambda:self.edit(lambda:self.editor.rotate(15)),enable)
            button('Size -10%',12,489,128,lambda:self.edit(lambda:self.editor.scale(.9)),enable)
            button('Size +10%',148,489,128,lambda:self.edit(lambda:self.editor.scale(1.1)),enable)
            section('MATERIAL',537)
            for i,material in enumerate(('metal','wood','rubber','plastic')):
                button(material.title(),12+i*68,557,64,lambda n=material:self.edit(lambda:self.editor.material(n)),enable,
                       selected is not None and selected.material==material)
            motors=self.editor.selected_motors() if selected else ()
            if self.editor.gripper_root():
                button('Configure gripper',12,605,264,self.gripper_form,enable,h=32)
            elif motors:
                section(f'MOTOR LIMIT  /  {motors[0].max_torque:.2f} Nm',605)
                button('Torque -',12,625,128,lambda:self.edit(lambda:self.editor.motor_strength(.8)),enable)
                button('Torque +',148,625,128,lambda:self.edit(lambda:self.editor.motor_strength(1.25)),enable)
            elif selected:
                text('Size: '+' x '.join(f'{v:.2f}' for v in selected.geometry.size)+' m',16,607,12,muted)
            button('Delete subtree',12,wh-78,264,lambda:self.edit(self.editor.delete),enable,tone='danger')
        elif self.active_tab=='Connect':
            self.draw_connections(ui,button,text,section,ww,wh)
        elif self.active_tab=='Add':
            if self.library_open:
                self.draw_catalog(ui,button,text,section,ww,wh)
            else:
                section('ATTACH TO',122)
                text(selected.id if selected else 'Select a part in the scene',16,146,16,max_width=260)
                text('New parts use preset mounting positions.',16,177,12,muted)
                button('Loose box',12,218,264,lambda:self.edit(self.editor.add_box),self.building,h=40)
                text('Independent wooden block on the floor',20,269,12,muted)
                mount=enable and selected.geometry.shape=='box'
                button('Attach beam',12,311,264,lambda:self.edit(self.editor.attach_beam),mount,h=40)
                text('Fixed beam on top of the selected box',20,362,12,muted)
                button('Left wheel + motor',12,404,264,lambda:self.edit(lambda:self.editor.attach_wheel(1)),mount,h=40)
                button('Right wheel + motor',12,454,264,lambda:self.edit(lambda:self.editor.attach_wheel(-1)),mount,h=40)
                text('Each wheel includes a hinge and motor.',20,507,12,muted)
                text('Reselect the base before adding the other.',20,528,12,muted)
                button('Attach camera',12,576,264,lambda:self.edit(self.editor.attach_camera),enable,h=40)
                button('Back to properties',12,wh-78,264,lambda:setattr(self,'active_tab','Edit'))
                button('Parts library',12,wh-118,264,lambda:setattr(self,'library_open',True))
        elif self.active_tab=='Guide':
            self.draw_guide(ui,button,text,section,ww,wh)
        else:
            section('YOUR BLUEPRINT',122)
            text(self.path.name,16,149,16,max_width=260)
            text('Save the design, not the simulation state.',16,181,12,muted)
            button('Save',12,223,128,self.save,h=38)
            button('Load',148,223,128,self.load,self.building and self.path.exists(),h=38)
            button('Export parts / assumptions',12,269,264,self.export_parts,h=28)
            section('STARTING POINTS',302)
            button('Start with block',12,331,264,lambda:self.edit(lambda:self.editor.load(starter_blueprint())),self.building,h=40)
            text('One ordinary body. Build up from there.',20,382,12,muted)
            button('Robot example',12,424,264,lambda:self.edit(lambda:self.editor.load(two_wheel_blueprint())),self.building,h=40)
            text('Two wheels, motors, supports and camera.',20,475,12,muted)
            from little_world.robots.mobile_platform import mobile_platform_blueprint
            button('Hardware mobile base',12,522,264,lambda:self.edit(lambda:self.editor.load(mobile_platform_blueprint())),self.building,h=40)
            text('Gearmotors, open chassis and swivel casters.',16,577,12,muted)
            from little_world.robots.arm_lab import arm_lab_blueprint
            button('Arm & gripper lab',12,600,264,lambda:self.edit(lambda:self.editor.load(arm_lab_blueprint())),self.building,h=32)
            from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
            button('Arm on moving cart',12,640,264,lambda:self.edit(lambda:self.editor.load(mobile_manipulator_blueprint())),self.building,h=32)
        button('Focus',self.PANEL+16,72,65,self.home)
        button('Camera',self.PANEL+87,72,70,self.camera_toggle)
        button('Follow',self.PANEL+163,72,70,self.toggle_follow,active=self.follow)
        button('Operate',self.PANEL+239,72,85,self.operate_robot)
        button('Guide',self.PANEL+330,72,64,self.show_guide)
        button('Undo',ww-166,72,68,lambda:self.edit(self.editor.undo),self.building and bool(self.editor.past),h=26)
        button('Redo',ww-92,72,68,lambda:self.edit(self.editor.redo),self.building and bool(self.editor.future),h=26)
        help_text=('Click a part to select. Drag to orbit. Right-drag to pan. Scroll to zoom.' if self.building else
                   'Hold WASD to drive. Release to brake. P pauses. Enter returns to build.')
        if self.control_panel:help_text='Drag to orbit. Right-drag to pan. Scroll to zoom.'
        text(help_text,self.PANEL+18,wh-57,12,(.8,.86,.86),ww-self.PANEL-35-(338 if self.control_panel else 0))
        text(self.status,16,wh-24,12,(.61,.70,.73),ww-32)
        if self.active_tab=='Add' and self.library_open:
            self.render_catalog_preview(ww,wh,fw,fh)
            text('PREVIEW / drag to rotate',ww-224,112,11,muted)
            text(self.catalog_selection.replace('_',' '),ww-224,321,12,max_width=212)
        self.draw_control_panel(ui,button,text,ww,wh,fw,fh)
        self.draw_dialog(ui,button,text,ww,wh)
        ui.flush(ww,wh,fw,fh)

    def over_preview(self,x,y):
        if self.over_controls(x,y):
            return False
        if self.bench_open and self.bench_part_rect:
            px,py,w,h=self.bench_part_rect
            return px<x<px+w and py<y<py+h
        width,_=glfw.get_window_size(self.window)
        return self.active_tab=='Add' and self.library_open and width-236<x<width-16 and 136<y<316

    def render_catalog_preview(self,ww,wh,fw,fh,rect=None):
        from little_world.assets.catalog import BY_ID
        from little_world.core.scene import Scene
        item=BY_ID[self.catalog_selection]
        if item.id not in self.preview_cache:
            backend=MujocoBackend()
            backend.compile(Scene((Entity('preview',item.blueprint()),)),.002)
            model,data=backend.model,backend.data
            model.vis.headlight.ambient[:]=(.4,.4,.4)
            scene=mj.MjvScene(model,maxgeom=200)
            camera=mj.MjvCamera()
            camera.lookat[:]=model.stat.center
            camera.distance=max(.06,model.stat.extent*1.7)
            camera.azimuth,camera.elevation=130,-28
            context=mj.MjrContext(model,150) if model.nmesh else None
            self.preview_cache[item.id]=(model,data,scene,camera,context)
            backend.close()
        model,data,scene,camera,context=self.preview_cache[item.id]
        mj.mjv_updateScene(model,data,self.option,None,camera,mj.mjtCatBit.mjCAT_ALL,scene)
        scene.flags[mj.mjtRndFlag.mjRND_SHADOW]=False
        x,y,w,h=rect or (ww-236,136,220,180)
        viewport=mj.MjrRect(int(x*fw/ww),int((wh-y-h)*fh/wh),int(w*fw/ww),int(h*fh/wh))
        mj.mjr_render(viewport,scene,context or self.context)

    def choose_category(self,category):
        self.catalog_category=category
        self.catalog_offset=0

    def cycle_mount(self):
        faces=('Default','Top','Bottom','Left','Right','Front','Back','Floor')
        self.catalog_mount=faces[(faces.index(self.catalog_mount)+1)%len(faces)] if self.catalog_mount in faces else 'Default'

    def insert_catalog(self):
        mount=None if self.catalog_mount=='Default' else self.catalog_mount
        self.edit(lambda:self.editor.add_catalog(self.catalog_selection,mount))
        self.status='Part added. Select its subparts to edit geometry, material or motor strength.'

    def draw_catalog(self,ui,button,text,section,ww,wh):
        from little_world.assets.catalog import CATALOG,BY_ID
        import textwrap
        button('Quick tools',12,120,264,lambda:setattr(self,'library_open',False))
        for i,category in enumerate(('All','Structure','Motion','Sensors','Housing')):
            button(category,12+(i%3)*90,167+(i//3)*34,84,lambda c=category:self.choose_category(c),active=self.catalog_category==category,h=28)
        items=[p for p in CATALOG if self.catalog_category=='All' or p.category==self.catalog_category]
        self.catalog_offset=min(self.catalog_offset,max(0,len(items)-4))
        for i,item in enumerate(items[self.catalog_offset:self.catalog_offset+4]):
            y=244+i*61
            button(item.title,12,y,264,lambda k=item.id:setattr(self,'catalog_selection',k),active=item.id==self.catalog_selection,h=34)
            text(item.capability,20,y+36,11,(.53,.65,.66))
        button('< Previous',12,492,128,lambda:setattr(self,'catalog_offset',max(0,self.catalog_offset-4)),self.catalog_offset>0,h=28)
        button('Next >',148,492,128,lambda:setattr(self,'catalog_offset',min(max(0,len(items)-4),self.catalog_offset+4)),self.catalog_offset+4<len(items),h=28)
        item=BY_ID[self.catalog_selection]
        section(f'{len(CATALOG)} PARTS  /  '+item.category.upper(),539)
        text(item.title,16,560,15,max_width=252)
        for i,line in enumerate(textwrap.wrap(item.description,42)[:2]):
            text(line,16,584+i*17,11,(.6,.69,.73),256)
        mount=item.mount if self.catalog_mount=='Default' else self.catalog_mount
        target='Floor' if mount=='Floor' else (self.editor.selection or 'select a parent')
        button('Mount: '+mount,12,628,128,self.cycle_mount,self.building,h=28)
        text(target,148,632,11,(.6,.69,.73),124)
        button('Add selected part',12,wh-76,264,self.insert_catalog,
               self.building and (mount=='Floor' or self.editor.selected is not None),active=True,h=34)


    def toggle_follow(self):
        self.follow=not self.follow
        self.camera.type=mj.mjtCamera.mjCAMERA_FREE

    def run(self, seconds=None, screenshot=None, *, visible=True):
        if sys.platform=='darwin':
            from mujoco import viewer
            if viewer._MJPYTHON is not None:
                os.execv(sys.executable,[sys.executable,*sys.argv])
        if not glfw.init():
            raise RuntimeError('Could not initialize GLFW')
        try:
            glfw.window_hint(glfw.VISIBLE,glfw.TRUE if visible else glfw.FALSE)
            self.window = glfw.create_window(1200,780,'Little World | Workshop',None,None)
            if not self.window:
                raise RuntimeError('Could not open workshop window')
            glfw.set_window_size_limits(self.window,1040,740,glfw.DONT_CARE,glfw.DONT_CARE)
            glfw.make_context_current(self.window)
            glfw.swap_interval(1 if visible else 0)
            self.rebuild()
            self.home(True)
            if self.initial_camera is not None:
                self.camera.lookat[:],self.camera.distance = self.initial_camera
            glfw.set_key_callback(self.window,lambda *args:self.active_workspace.key(*args))
            glfw.set_char_callback(self.window,lambda *args:self.active_workspace.character(*args))
            glfw.set_mouse_button_callback(self.window,lambda *args:self.active_workspace.mouse(*args))
            glfw.set_cursor_pos_callback(self.window,lambda *args:self.active_workspace.mouse_move(*args))
            glfw.set_scroll_callback(self.window,lambda *args:self.active_workspace.scroll(*args))
            def focus_changed(window,focused):
                active=self.active_workspace
                if not focused:
                    active.cancel_docking()
                    if active.runner.state=='running':active.pause_program()
                    else:active.clear_keys()
            glfw.set_window_focus_callback(self.window,focus_changed)
            if getattr(self,'start_mode',self.app_mode)!=self.app_mode:self.switch_workspace(self.start_mode)
            started = previous = time.monotonic()
            accumulator = 0
            captured = False
            while not glfw.window_should_close(self.window):
                now=time.monotonic()
                if seconds is not None and now-started>=seconds:
                    break
                elapsed=min(.1,now-previous)
                previous=now
                glfw.poll_events()
                active=self.active_workspace
                while active.events:
                    event=active.events.pop(0)
                    try:
                        event()
                        active=self.active_workspace
                    except (ValueError,KeyError,TypeError,OSError) as error:
                        active.status='Could not apply change: '+str(error)
                if glfw.get_window_attrib(active.window,glfw.ICONIFIED):
                    active.clear_keys()
                    accumulator=0
                    time.sleep(.02)
                    continue
                if active.building or active.paused:
                    accumulator=0
                else:
                    accumulator+=elapsed
                    while accumulator>=active.world.timestep:
                        active.tick_program()
                        commands={}
                        commands.update(active.drive_control.step_commands(active.program_drive if active.program_drive is not None else active.controls.targets(),active.world.timestep,angular=active.program_drive is not None))
                        commands.update(active.joint_commands())
                        if active.motor_test is not None:
                            name,torque,until=active.motor_test
                            if active.state.time < until:
                                commands[name]=torque
                            else:
                                active.motor_test=None
                        active.state=active.world.step(commands)
                        accumulator-=active.world.timestep
                        if active.paused:break
                active.draw()
                if screenshot and not captured and now-started>.4:
                    width,height=glfw.get_framebuffer_size(self.window)
                    rgb=np.zeros((height,width,3),dtype=np.uint8)
                    mj.mjr_readPixels(rgb,None,mj.MjrRect(0,0,width,height),active.context)
                    Path(screenshot).write_bytes(f'P6\n{width} {height}\n255\n'.encode()+rgb[::-1].tobytes())
                    captured=True
                glfw.swap_buffers(self.window)
                target = 1/60 if (not active.building and not active.paused) or now-active.last_input < .3 else 1/15
                glfw.wait_events_timeout(max(.0001, target-(time.monotonic()-now)))
        finally:
            for workspace in getattr(self,'_workspaces',{'initial':self}).values():workspace.close_resources()
            if self.window:glfw.destroy_window(self.window)
            glfw.terminate()

    def close_resources(self):
        if self.script_process is not None:self.script_cancel()
        if self.script_pool is not None:self.script_pool.shutdown(wait=False,cancel_futures=True)
        self.free_drag_preview()
        for backend,scene,camera in self.inventory_previews.values():backend.close()
        for preview in self.preview_cache.values():
            if preview[4] is not None:preview[4].free()
        if self.comparison_executor:self.comparison_executor.shutdown(wait=False)
        if self.canvas:self.canvas.close()
        if self.context:self.context.free()
        self.world.close()
