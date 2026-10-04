"""Single-window workspace switching with separate authoring/runtime state."""
import glfw

class AppModes:
    @property
    def workspace_host(self):return getattr(self,'_workspace_host',self)
    @property
    def active_workspace(self):return getattr(self.workspace_host,'_active_workspace',self.workspace_host)
    @property
    def app_mode(self):return 'Real' if getattr(self,'factory_mode',False) else 'Anime'

    def switch_workspace(self,mode):
        if mode not in ('Real','Anime'):raise ValueError('Unknown workspace mode')
        host=self.workspace_host;old=host.active_workspace
        if mode==old.app_mode:return
        old.clear_keys();old.cancel_docking();old.events.clear()
        if old.runner.state=='running':old.pause_program()
        if not old.building:old.paused=True
        if hasattr(old,'teach_drag'):old.teach_drag=False
        if hasattr(old,'tray_drag'):old.tray_drag=None;old.pending_source=None
        if not hasattr(host,'_workspaces'):host._workspaces={old.app_mode:old}
        target=host._workspaces.get(mode)
        if target is None:
            if mode=='Real':
                from .factory_workspace import FactoryWorkshop
                target=FactoryWorkshop(getattr(host,'factory_recipe_path',None))
            else:
                from .workshop import Workshop
                from little_world.construction.editor import starter_blueprint
                from pathlib import Path
                target=Workshop(Path.home()/'Library/Application Support/Little World/kit.json',starter_blueprint())
                target.open_bench()
            target._workspace_host=host;target.window=host.window
            try:
                target.rebuild();target.home(True)
                if target.initial_camera is not None:target.camera.lookat[:],target.camera.distance=target.initial_camera
            except Exception:
                target.close_resources();raise
            host._workspaces[mode]=target
        host._active_workspace=target
        glfw.set_window_title(host.window,'Little World | '+mode)
        target.status=mode+' workspace'+(' / simulation paused' if not target.building else '')

    def draw_mode_switch(self,button):
        for label,x,width in (('Real',164,64),('Anime',234,70)):
            button(label,x,10,width,lambda m=label:self.switch_workspace(m),active=self.app_mode==label,h=36)
