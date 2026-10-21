"""Same-window station layout authoring using the portable factory document."""
from dataclasses import replace
from pathlib import Path
import time
import glfw
import mujoco as mj
import numpy as np
from little_world.core.blueprint import Blueprint
from little_world.core.component import Transform,Body,Geometry
from little_world.core.entity import Entity
from little_world.core.scene import Scene
from little_world.materials import METAL
from little_world.factory.document import FactoryDocument,MachineAsset,Station,ProcessLink
from little_world.factory.document_editor import FactoryEditor
from little_world.assets.catalog import BY_ID,CATALOG,items as catalog_items
from little_world.construction.connections import euler_quaternion,rotate,module_bounds
from .workshop import Workshop
from .inspector import numbers,rotation_degrees


def starter_layout():
    return FactoryDocument((MachineAsset('bench',BY_ID['lab_workbench'].blueprint()),MachineAsset('rollers',BY_ID['lab_roller_table'].blueprint())),
        (Station('work','bench','Work station'),Station('feed','rollers','Passive feed rollers',Transform((-1.5,0,0)))))


class LayoutWorkshop(Workshop):
    PANEL=304
    def __init__(self,path):
        self.layout_mode=True;self.factory_mode=True;self.layout=FactoryEditor(starter_layout())
        self.pending_compile=None;self.selected_station='work';self.station_drag=None
        notice='Drag a station; drag empty space to orbit.'
        if Path(path).exists():
            try:self.layout=FactoryEditor(FactoryDocument.from_json(Path(path).read_text()))
            except (ValueError,OSError):notice='Saved layout could not be loaded; starter shown. Original file preserved.'
        super().__init__(path,Blueprint((),()))
        self.library_open=False;self.control_panel=False;self.initial_camera=((0,0,.5),6.)
        self.status=notice
        if not any(s.id==self.selected_station for s in self.layout.document.stations):self.selected_station=None

    def _scene(self):
        doc=self.pending_compile or self.layout.document
        if any(s.id=='_layout_ground' for s in doc.stations):raise ValueError('_layout_ground is reserved for the editor floor.')
        floor=Blueprint((Body('floor',Geometry('box',(15,12,.1)),METAL.id,Transform((0,0,-.05))),),(METAL,))
        return Scene((Entity('_layout_ground',floor),)+doc.to_scene().entities)

    @property
    def station(self):return next((s for s in self.layout.document.stations if s.id==self.selected_station),None)

    def install_editor(self,editor):
        self.pending_compile=editor.document
        try:self.rebuild()
        except Exception:
            self.pending_compile=None;self.rebuild();raise
        self.pending_compile=None;self.layout=editor;self.station_drag=None
        if self.station is None:self.selected_station=None
        self.status=f'Layout updated / revision {self.layout.revision}. Undo restores the previous layout.'

    def apply_document(self,document):
        editor=self.layout.clone();editor.apply(self.layout.preview(document))
        if editor.revision!=self.layout.revision:self.install_editor(editor)

    def undo_layout(self):
        editor=self.layout.clone();editor.undo();self.install_editor(editor)
    def redo_layout(self):
        editor=self.layout.clone();editor.redo();self.install_editor(editor)

    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary=self.path.with_suffix('.json.tmp');temporary.write_text(self.layout.document.to_json());temporary.replace(self.path)
        self.status='Factory layout saved.'

    def open_layout(self):
        self.form('Open factory layout',[('Factory JSON path',str(self.path))],
            lambda v:self.apply_document(FactoryDocument.from_json(Path(v[0]).expanduser().read_text())),
            'Replaces this layout as one undoable edit. Save writes to the workspace file.',text_input=True)

    def next_id(self,prefix):
        ids={s.id for s in self.layout.document.stations}|{a.id for a in self.layout.document.assets}
        n=1
        while f'{prefix}_{n}' in ids or f'{prefix}_{n}_asset' in ids:n+=1
        return f'{prefix}_{n}'

    def add_machine(self,blueprint,label):
        id=self.next_id('station');asset=id+'_asset'
        # Capture the authored Blueprint as a value; later builder edits do not replace it.
        doc=self.layout.document.with_asset(MachineAsset(asset,blueprint))
        self.apply_document(doc.with_station(Station(id,asset,label,Transform((0,-1.5,0)))))
        self.selected_station=id
        self.status='Machine added. Drag it into place; clearance and reach are not checked.'

    def add_catalog(self):
        choices={p.title+' ['+p.id+']':p for p in catalog_items() if p.variant.startswith('lab_') or p.variant=='real_robot'}
        self.choose('Add a station / search equipment',tuple(choices),lambda name:self.add_machine(choices[name].blueprint(),choices[name].title))

    def builder(self):return getattr(self.workspace_host,'_workspaces',{}).get('Anime')
    def use_builder(self):
        builder=self.builder()
        if builder is None or not builder.editor.bodies:raise ValueError('Create a machine in Anime first.')
        self.add_machine(builder.editor.blueprint,'Machine from builder')

    def import_machine(self):
        self.form('Import saved machine',[('Blueprint JSON path','')],
            lambda v:self.add_machine(Blueprint.from_json(Path(v[0]).expanduser().read_text()),Path(v[0]).stem[:80]),
            'Imports a copy of the machine design. Its file is unchanged.',text_input=True)

    def select_station(self,id):self.selected_station=id
    def choose_station(self):
        values={s.label+' ['+s.id+']':s.id for s in self.layout.document.stations}
        self.choose('Select station',tuple(values),lambda name:self.select_station(values[name]))

    def exact_station(self):
        station=self.station;revision=self.layout.revision
        def apply(values):
            if self.layout.revision!=revision:raise ValueError('Layout changed; reopen the position form.')
            pose=Transform(numbers(values[0],3),euler_quaternion(numbers(values[1],3)))
            self.apply_document(self.layout.document.move_station(station.id,pose))
        self.form('Position / '+station.label,[('World X, Y, Z (metres)',', '.join(str(x) for x in station.transform.position)),
            ('Rotation X, Y, Z (degrees)',', '.join(str(x) for x in rotation_degrees(station.transform.quaternion)))],apply,
            'Moves this instance only. Shared machine geometry stays unchanged.')

    def delete_station(self):
        station=self.station;revision=self.layout.revision
        links=[l for l in self.layout.document.links if station.id in (l.source,l.destination)]
        def remove(_):
            if revision!=self.layout.revision:raise ValueError('Layout changed; review station deletion again.')
            self.apply_document(self.layout.document.remove_station(station.id,remove_links=True))
        if links:
            self.choose('Delete '+station.label,('Remove station and '+str(len(links))+' connected links',),remove)
        else:self.apply_document(self.layout.document.remove_station(station.id))

    def connect_station(self):
        source=self.station.id;revision=self.layout.revision
        choices={s.label+' ['+s.id+']':s.id for s in self.layout.document.stations if s.id!=source}
        def connect(name):
            if revision!=self.layout.revision:raise ValueError('Layout changed; choose stations again.')
            used={l.id for l in self.layout.document.links};n=1
            while 'flow_'+str(n) in used:n+=1
            self.apply_document(self.layout.document.with_link(ProcessLink('flow_'+str(n),source,choices[name])))
        self.choose('Intended flow: choose destination',tuple(choices),connect)

    def remove_link(self):
        links={l.id+': '+l.source+' -> '+l.destination:l.id for l in self.layout.document.links}
        self.choose('Remove intended flow',tuple(links),lambda name:self.apply_document(self.layout.document.remove_link(links[name])))

    def station_at(self,x,y):
        ww,wh=glfw.get_window_size(self.window)
        if not self.PANEL<x<ww or not 56<y<wh-32:return None
        point=np.zeros(3);ids=[np.zeros(1,dtype=np.int32) for _ in range(3)]
        body=mj.mjv_select(self.model,self.data,self.option,(ww-self.PANEL)/(wh-88),
            (x-self.PANEL)/(ww-self.PANEL),1-(y-56)/(wh-88),self.render_scene,point,*ids)
        if body<0:return None
        id=self.model.body(body).name.split('/')[0]
        return id if any(s.id==id for s in self.layout.document.stations) else None

    def plane_cursor(self,x,y,z):
        ww,wh=glfw.get_window_size(self.window)
        if not self.PANEL<x<ww or not 56<y<wh-32:return None
        a,b=self.render_scene.camera;origin=(a.pos+b.pos)/2;forward=(a.forward+b.forward)/2;up=(a.up+b.up)/2
        ratio=(a.frustum_top-a.frustum_bottom)/(2*a.frustum_near);h=wh-88;w=ww-self.PANEL
        ray=forward+np.cross(forward,up)*((x-self.PANEL-w/2)/(h/2))*ratio-up*((y-56-h/2)/(h/2))*ratio
        if abs(ray[2])<1e-6:return None
        distance=(z-origin[2])/ray[2]
        return origin+ray*distance if distance>0 else None

    def pick(self,x,y):self.selected_station=self.station_at(x,y)
    def mouse(self,win,button,action,mods):
        x,y=glfw.get_cursor_pos(win)
        if self.dialog is not None:return super().mouse(win,button,action,mods)
        if button==glfw.MOUSE_BUTTON_LEFT:
            if action==glfw.RELEASE and self.station_drag:
                drag=self.station_drag;self.station_drag=None
                if drag['moved']:
                    self.events.append(lambda d=drag:self.finish_drag(d))
                return
            if action==glfw.PRESS and not any(b.x<=x<=b.x+b.width and b.y<=y<=b.y+b.height for b in self.buttons):
                id=self.station_at(x,y)
                if id:
                    self.selected_station=id;pose=self.station.transform;start=self.plane_cursor(x,y,pose.position[2])
                    if start is not None:self.station_drag=dict(id=id,pose=pose,start=start,point=np.array(pose.position),moved=False,revision=self.layout.revision)
                    return
        super().mouse(win,button,action,mods)

    def finish_drag(self,drag):
        if drag['revision']!=self.layout.revision:raise ValueError('Layout changed during drag; move the station again.')
        self.apply_document(self.layout.document.move_station(drag['id'],replace(drag['pose'],position=tuple(drag['point']))))

    def mouse_move(self,win,x,y):
        if self.station_drag:
            self.last_input=time.monotonic();self.last_mouse=(x,y);drag=self.station_drag
            point=self.plane_cursor(x,y,drag['pose'].position[2])
            if point is not None:
                drag['point']=np.round((np.asarray(drag['pose'].position)+point-drag['start'])/.01)*.01
                drag['moved']=np.linalg.norm(drag['point']-drag['pose'].position)>.001
            return
        super().mouse_move(win,x,y)

    def key(self,win,key,scancode,action,mods):
        if self.dialog is not None:return super().key(win,key,scancode,action,mods)
        if action!=glfw.PRESS:return
        if key==glfw.KEY_ESCAPE:self.station_drag=None
        elif mods & (glfw.MOD_CONTROL|glfw.MOD_SUPER):
            if key==glfw.KEY_S:self.events.append(self.save)
            elif key==glfw.KEY_Z:self.events.append(self.redo_layout if mods & glfw.MOD_SHIFT else self.undo_layout)

    def decorate_scene(self):
        drag=self.station_drag
        if drag:
            delta=drag['point']-drag['pose'].position
            for i in range(self.render_scene.ngeom):
                geom=self.render_scene.geoms[i]
                if geom.objtype==mj.mjtObj.mjOBJ_GEOM and geom.objid>=0:
                    body=self.model.geom_bodyid[geom.objid]
                    if self.model.body(body).name.startswith(drag['id']+'/'):
                        geom.pos+=delta;geom.rgba[3]=.65
        if self.station:
            asset=next(a for a in self.layout.document.assets if a.id==self.station.asset)
            lower,upper=module_bounds(asset.blueprint)
            origin=drag['point'] if drag else self.station.transform.position
            corners=[np.asarray(origin)+rotate(self.station.transform.quaternion,(x,y,z)) for x in (lower[0],upper[0]) for y in (lower[1],upper[1]) for z in (lower[2],upper[2])]
            for i in range(8):
                for bit in (1,2,4):
                    j=i^bit
                    if j<=i or self.render_scene.ngeom>=self.render_scene.maxgeom:continue
                    geom=self.render_scene.geoms[self.render_scene.ngeom]
                    mj.mjv_initGeom(geom,mj.mjtGeom.mjGEOM_CAPSULE,np.zeros(3),np.zeros(3),np.eye(3).ravel(),np.array((.3,.95,.7,.85),dtype=np.float32))
                    mj.mjv_connector(geom,mj.mjtGeom.mjGEOM_CAPSULE,.006,corners[i],corners[j]);geom.category=mj.mjtCatBit.mjCAT_DECOR;self.render_scene.ngeom+=1
        positions={s.id:np.asarray(s.transform.position)+np.array((0,0,.12)) for s in self.layout.document.stations}
        if drag:positions[drag['id']]=drag['point']+np.array((0,0,.12))
        for link in self.layout.document.links:
            if self.render_scene.ngeom>=self.render_scene.maxgeom:break
            geom=self.render_scene.geoms[self.render_scene.ngeom]
            mj.mjv_initGeom(geom,mj.mjtGeom.mjGEOM_CAPSULE,np.zeros(3),np.zeros(3),np.eye(3).ravel(),np.array((.3,.8,.8,1.),dtype=np.float32))
            mj.mjv_connector(geom,mj.mjtGeom.mjGEOM_CAPSULE,.01,positions[link.source],positions[link.destination]);geom.category=mj.mjtCatBit.mjCAT_DECOR;self.render_scene.ngeom+=1

    def draw_factory(self,ui,button,text,ww,wh,fw,fh):
        ui.rect(0,0,ww,56,(.045,.065,.085));ui.rect(0,56,self.PANEL,wh-88,(.075,.099,.125));ui.rect(0,wh-32,ww,32,(.055,.077,.097))
        text('little world',18,17,19);self.draw_mode_switch(button)
        button('Robot lab',322,12,116,lambda:self.switch_real_view('Real'),h=32)
        text('FACTORY LAYOUT',454,21,11,(.4,.85,.72))
        button('Undo',ww-354,12,70,self.undo_layout,self.layout.can_undo,h=32)
        button('Redo',ww-278,12,70,self.redo_layout,self.layout.can_redo,h=32)
        button('Open',ww-202,12,80,self.open_layout,h=32)
        button('Save layout',ww-116,12,100,self.save,h=32,tone='primary')
        text('STATIONS / '+str(len(self.layout.document.stations)),18,80,12)
        button('Select station',18,105,268,self.choose_station,bool(self.layout.document.stations))
        button('Add equipment',18,153,268,self.add_catalog,h=36,tone='primary')
        builder=self.builder()
        button('Use current Anime machine',18,198,268,self.use_builder,builder is not None and bool(builder.editor.bodies))
        button('Import saved machine',18,239,268,self.import_machine)
        button('Exact position',18,297,268,self.exact_station,self.station is not None)
        button('Connect intended flow',18,338,268,self.connect_station,self.station is not None and len(self.layout.document.stations)>1)
        button('Remove flow',18,379,268,self.remove_link,bool(self.layout.document.links))
        button('Delete station',18,420,268,self.delete_station,self.station is not None)
        if self.station:
            text(self.station.label,18,480,15,max_width=268)
            text('ID: '+self.station.id,18,508,11,max_width=268)
            point=self.station_drag['point'] if self.station_drag else self.station.transform.position
            text('XYZ m: '+', '.join(f'{v:.2f}' for v in point),18,532,11,max_width=268)
            text('Asset: '+self.station.asset,18,556,11,max_width=268)
        text('Drag stations to move / 1 cm snapping',self.PANEL+18,78,12,max_width=ww-self.PANEL-36)
        text('Flow lines show intent. No process execution or clearance checks.',self.PANEL+18,103,11,(.95,.74,.4),ww-self.PANEL-36)
        text('Escape cancels a drag. Empty space orbits.',18,wh-60,10,max_width=270)
        text(self.status,18,wh-24,11,max_width=ww-36)
        self.draw_dialog(ui,button,text,ww,wh);ui.flush(ww,wh,fw,fh)
