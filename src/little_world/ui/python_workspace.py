"""In-app multiline Python authoring with asynchronous, atomic build application."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
import glfw

TEMPLATES={
'Six-wheel rover':'''from little_world.scripting import RobotBuilder

robot = RobotBuilder.chassis(length=0.65, width=0.28, height=0.04)
# Coordinates are metres. Positions are freely adjustable.
for side in ("Left", "Right"):
    for x in (-0.21, 0.0, 0.21):
        robot.wheel("drive_100", side=side, x=x)

robot.drive(max_speed=0.5, acceleration=0.7, torque_fraction=0.8)
blueprint = robot.blueprint
''',
'Arm on a rover':'''from little_world.scripting import RobotBuilder

robot = RobotBuilder.chassis(length=0.65, width=0.30, height=0.04)
for side in ("Left", "Right"):
    for x in (-0.21, 0.21):
        robot.wheel("drive_130", side=side, x=x)
arm = robot.add("robot_arm_compact")
# The arm receives editable keyboard controls automatically.
blueprint = robot.blueprint
''',
'Edit current design':'''from little_world.construction.editor import AssemblyEditor

# current is a copy of the design at the moment you press Run build.
editor = AssemblyEditor(current)
# Use editor.select(id), editor.move((x, y, z)), editor.add_catalog(id), ...
print("Bodies:", [body.id for body in editor.bodies])
blueprint = editor.blueprint
'''}


class PythonWorkspace:
    def init_python(self):
        self.script_open=False;self.script_text=TEMPLATES['Six-wheel rover'];self.script_cursor=0
        self.script_scroll=0;self.script_select_all=False;self.script_history=[]
        self.script_future=None;self.script_process=None;self.script_pool=None
        self.script_output='Run build applies a valid result as one undoable change.'
        self.script_loaded=False;self.script_rect=None

    @property
    def script_path(self):return self.path.with_suffix('.build.py')

    def show_python(self):
        if not self.building:self.simulate()
        self.close_bench();self.control_panel=False;self.inventory_open=False;self.clear_keys()
        if not self.script_loaded:
            if self.script_path.exists():self.script_text=self.script_path.read_text()
            self.script_loaded=True
        self.script_open=True

    def script_save(self):
        self.script_path.parent.mkdir(parents=True,exist_ok=True)
        self.script_path.write_text(self.script_text)
        self.script_output='Saved '+self.script_path.name

    def script_replace(self,text):
        self.script_history.append((self.script_text,self.script_cursor));self.script_history=self.script_history[-100:]
        if self.script_select_all:self.script_text='';self.script_cursor=0
        self.script_text=self.script_text[:self.script_cursor]+text+self.script_text[self.script_cursor:]
        self.script_cursor+=len(text);self.script_select_all=False
        self.script_reveal()

    def script_reveal(self):
        row=self.script_text[:self.script_cursor].count('\n')
        visible=max(1,int((glfw.get_window_size(self.window)[1]-190)/20)) if self.window else 24
        self.script_scroll=max(0,min(self.script_scroll,row))
        if row>=self.script_scroll+visible:self.script_scroll=row-visible+1

    def script_template(self):
        def choose(name):
            self.script_select_all=True;self.script_replace(TEMPLATES[name]);self.script_cursor=0;self.script_scroll=0
        self.choose('Python build templates',tuple(TEMPLATES),choose)

    def script_key(self,key,action,mods):
        if not self.script_open:return False
        if action not in (glfw.PRESS,glfw.REPEAT):return True
        command=bool(mods&(glfw.MOD_SUPER|glfw.MOD_CONTROL))
        if command:
            if key==glfw.KEY_A:self.script_select_all=True
            elif key==glfw.KEY_S:self.script_save()
            elif key==glfw.KEY_ENTER:self.script_run()
            elif key==glfw.KEY_Z and self.script_history:
                self.script_text,self.script_cursor=self.script_history.pop();self.script_select_all=False;self.script_reveal()
            elif key in (glfw.KEY_C,glfw.KEY_X):
                if self.script_select_all:
                    glfw.set_clipboard_string(self.window,self.script_text)
                    if key==glfw.KEY_X:self.script_replace('')
            elif key==glfw.KEY_V:
                value=glfw.get_clipboard_string(self.window)
                if value:self.script_replace(value.decode() if isinstance(value,bytes) else value)
            return True
        if key==glfw.KEY_ESCAPE:self.script_open=False;self.open_bench();return True
        if key==glfw.KEY_ENTER:
            line=self.script_text[:self.script_cursor].split('\n')[-1]
            indent=len(line)-len(line.lstrip(' '))+(4 if line.rstrip().endswith(':') else 0)
            self.script_replace('\n'+' '*indent)
        elif key==glfw.KEY_TAB:self.script_replace('    ')
        elif key==glfw.KEY_BACKSPACE:
            if self.script_select_all:self.script_replace('')
            elif self.script_cursor:
                self.script_history.append((self.script_text,self.script_cursor))
                self.script_text=self.script_text[:self.script_cursor-1]+self.script_text[self.script_cursor:];self.script_cursor-=1
        elif key==glfw.KEY_DELETE:
            if self.script_select_all:self.script_replace('')
            else:
                self.script_history.append((self.script_text,self.script_cursor))
                self.script_text=self.script_text[:self.script_cursor]+self.script_text[self.script_cursor+1:]
        elif key in (glfw.KEY_LEFT,glfw.KEY_RIGHT):
            self.script_cursor=max(0,min(len(self.script_text),self.script_cursor+(-1 if key==glfw.KEY_LEFT else 1)));self.script_select_all=False
        elif key in (glfw.KEY_UP,glfw.KEY_DOWN,glfw.KEY_HOME,glfw.KEY_END):
            lines=self.script_text.split('\n');row=self.script_text[:self.script_cursor].count('\n')
            column=len(self.script_text[:self.script_cursor].split('\n')[-1])
            if key in (glfw.KEY_UP,glfw.KEY_DOWN):row=max(0,min(len(lines)-1,row+(-1 if key==glfw.KEY_UP else 1)))
            elif key==glfw.KEY_HOME:column=0
            else:column=len(lines[row])
            self.script_cursor=sum(len(s)+1 for s in lines[:row])+min(column,len(lines[row]));self.script_select_all=False
        self.script_reveal();return True

    def script_mouse(self,x,y,action):
        if not self.script_open or self.dialog is not None:return False
        if action==glfw.PRESS:
            for b in self.buttons:
                if b.x<=x<=b.x+b.width and b.y<=y<=b.y+b.height:
                    if b.enabled:self.events.append(b.action)
                    return True
            if self.script_rect:
                rx,ry,rw,rh=self.script_rect
                if rx<=x<=rx+rw and ry<=y<=ry+rh:
                    lines=self.script_text.split('\n');row=min(len(lines)-1,self.script_scroll+max(0,int((y-ry)/20)))
                    line=lines[row];column=min(range(len(line)+1),key=lambda i:abs(self.canvas.width(line[:i],13)-(x-rx-54)))
                    self.script_cursor=sum(len(s)+1 for s in lines[:row])+column;self.script_select_all=False
        return True

    def script_cancel(self):
        if self.script_process is not None:
            self.script_cancelled=True;self.script_process.kill()

    def script_run(self):
        if self.script_future is not None:return
        from little_world.scripting.runner import start_script
        self.script_cancelled=False
        self.script_base=self.editor.blueprint
        self.script_process=start_script(self.script_text,self.script_base)
        self.script_pool=self.script_pool or ThreadPoolExecutor(max_workers=1)
        process=self.script_process
        def collect():
            try:return process.communicate(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill();process.communicate();raise TimeoutError('Build exceeded 8 seconds; the previous design is unchanged.')
        self.script_future=self.script_pool.submit(collect);self.script_output='Building in a separate Python process...'

    def script_poll(self):
        if self.script_future is None or not self.script_future.done():return
        future=self.script_future;self.script_future=None;self.script_process=None
        if self.script_cancelled:
            self.script_output="Build cancelled. The design is unchanged.";return
        try:
            from little_world.scripting.runner import decode_result
            result,output=decode_result(*future.result())
            if not self.building or self.editor.blueprint!=self.script_base:raise ValueError('Design changed while Python was running. Run again to apply to the current design.')
            self.edit(lambda:self.editor._commit(result))
            self.script_output=f'Applied {len(self.editor.bodies)} bodies. Undo restores the previous design.\n'+output
            self.bench_cache=None
        except Exception as error:self.script_output=str(error)

    def draw_python(self,ui,button,text,ww,wh,fw,fh):
        ui.begin();self.buttons=[];ui.rect(0,0,ww,wh,(.055,.075,.095))
        self.draw_navigation(ui,button,text,ww)
        button('Run build',24,76,126,self.script_run,self.script_future is None,h=36,tone='primary')
        button('Save script',160,76,112,self.script_save,h=36)
        button('Templates',282,76,112,self.script_template,h=36)
        button('Undo build',404,76,112,lambda:self.edit(self.editor.undo),bool(self.editor.past) and self.script_future is None,h=36)
        button('Cancel build',526,76,120,self.script_cancel,self.script_future is not None,h=36)
        button('View build',ww-150,76,126,lambda:self.navigate_workspace('Build'),h=36)
        rw=ww-380;top=134;height=wh-186
        self.script_rect=(24,top,rw,height);ui.rect(24,top,rw,height,(.035,.055,.075))
        ui.clip=self.script_rect
        lines=self.script_text.split('\n');visible=max(1,int(height/20))
        self.script_scroll=min(max(0,self.script_scroll),max(0,len(lines)-visible))
        if self.script_select_all:ui.rect(72,top,rw-52,height,(.12,.26,.30))
        for i,line in enumerate(lines[self.script_scroll:self.script_scroll+visible+1]):
            y=top+3+i*20
            text(str(i+self.script_scroll+1),32,y,11,(.40,.54,.6),36)
            text(line,78,y,13,(.55,.70,.65) if line.lstrip().startswith('#') else (.84,.9,.95),rw-66)
        row=self.script_text[:self.script_cursor].count('\n');prefix=self.script_text[:self.script_cursor].split('\n')[-1]
        if not self.script_select_all and self.script_scroll<=row<self.script_scroll+visible:
            ui.rect(78+ui.width(prefix,13),top+(row-self.script_scroll)*20+2,1,16,(.4,.95,.75))
        ui.clip=None
        x=ww-330
        text('PYTHON BUILDER',x,140,14,(.4,.85,.7))
        import textwrap
        description='Run build executes local Python. Set blueprint to your finished design. A failed build keeps the current robot. Scripts are saved separately from robot JSON.'
        y=170
        for line in textwrap.wrap(description,38):text(line,x,y,12,max_width=300);y+=18
        y+=16
        for line in ('Cmd/Ctrl + Enter: run','Cmd/Ctrl + S: save script','Cmd/Ctrl + A, C, V: select / copy / paste','Tab: indent / arrows: move cursor','Escape: return to build'):
            text(line,x,y,11,(.6,.74,.78),306);y+=21
        y+=16;text('BUILD OUTPUT',x,y,11,(.4,.85,.7));y+=24
        remaining=max(1,int((wh-60-y)/17));output=[]
        for line in self.script_output.splitlines():output.extend(textwrap.wrap(line,44) or [''])
        for line in output[-remaining:]:text(line,x,y,11,max_width=306);y+=17
        text('Python edits the same design as the visual builder. '+self.script_path.name,24,wh-30,11,(.6,.74,.78),ww-48)
        self.draw_dialog(ui,button,text,ww,wh);ui.flush(ww,wh,fw,fh)
