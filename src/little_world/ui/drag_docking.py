"""Drag/drop interaction and socket previews, committed only on release."""
import glfw
import numpy as np
import mujoco as mj
from little_world.assets.catalog import BY_ID
from little_world.construction.docking import sockets, dock, poses, catalog_id, prepare_base
from little_world.construction.connections import rotate


from .spatial_drag import SpatialDrag


class DragDocking(SpatialDrag):
    def init_docking(self):
        self.drag_preview=None
        self.part_drag=None;self.catalog_rows=[];self.socket_regions=[];self.socket_anchors=[]
        self.socket_cache={};self.socket_revision=None;self.drag_candidate=None

    def available_sockets(self,item,target,moving=None):
        if self.socket_revision is not self.editor.blueprint:
            self.socket_cache={};self.socket_revision=self.editor.blueprint
        key=(item,target,moving)
        if key not in self.socket_cache:self.socket_cache[key]=sockets(self.editor.blueprint,item,target,moving)
        return self.socket_cache[key]

    def pick_bench_body(self,x,y):
        if not self.bench_contains(x,y) or not self.bench_cache:return None
        _,model,data,scene=self.bench_cache
        px,py,w,h=self.bench_rect
        ids=[np.zeros(1,dtype=np.int32) for _ in range(3)]
        idx=mj.mjv_select(model,data,self.bench_option,w/h,(x-px)/w,1-(y-py)/h,scene,np.zeros(3),*ids)
        if idx>0:
            name=model.body(idx).name
            if name.startswith('machine/'):return self.backend.robot_owners.get(name,name).split('/',1)[1]
        return None

    def suggest_free_mount(self):
        if BY_ID[self.catalog_selection].mount=='Floor':return
        if not self.bench_target:return
        choices=self.available_sockets(self.catalog_selection,self.bench_target)
        current=BY_ID[self.catalog_selection].mount if self.catalog_mount=='Default' else self.catalog_mount
        if current in choices and choices[current].valid:return
        free=next((s.face for s in choices.values() if s.valid),None)
        if free:self.catalog_mount=free

    def select_card(self,item):
        self.catalog_selection=item;self.catalog_mount='Default'
        self.suggest_free_mount()

    def socket_at(self,x,y):
        for s,rx,ry,rw,rh in self.socket_regions:
            if rx<=x<=rx+rw and ry<=y<=ry+rh:return s
        nearby=[((x-cx)**2+(y-cy)**2,s) for s,cx,cy in self.socket_anchors
                if (x-cx)**2+(y-cy)**2<=28**2]
        return min(nearby,key=lambda entry:entry[0])[1] if nearby else None

    def compatible_target(self,name,item,moving):
        bodies={b.id:b for b in self.editor.bodies}
        # Walk through wheels, covers and small details to their supporting body.
        # Crossing an incompatible part must not destroy the current mount set.
        while name in bodies:
            body=bodies[name]
            named=any(a.id in ('tool','output','arm_mount') for a in body.attachments)
            candidate=name if named else self.bench_module(name)
            if any(s.valid for s in self.available_sockets(item,candidate,moving).values()):return candidate
            name=body.parent
        return self.bench_target

    def docking_mouse(self,x,y,action):
        if not self.bench_open or self.dialog is not None:return False
        if action==glfw.RELEASE and self.part_drag is not None:
            drag=self.part_drag
            self.drag_candidate=self.socket_at(x,y)
            self.update_drag_pose(x,y)
            preview=getattr(self,'drag_preview',None)
            pose=preview['pose'] if preview else None
            floor=bool(preview and preview.get('floor') and preview['valid'] and pose)
            self.part_drag=None
            self.free_drag_preview()
            if not drag['moved']:return True
            if floor:
                def place():
                    self.edit(lambda:self.commit_floor_drag(drag['item'],pose,drag['moving']))
                    self.bench_target=self.editor.selection
                    self.status='Placed '+BY_ID[drag['item']].title+'. Undo restores the previous build.'
                self.events.append(place);self.drag_candidate=None;return True
            choice=self.socket_at(x,y)
            if choice is None:
                self.status='Drop cancelled. Release over a green named socket to connect.'
            elif not choice.valid:self.status=choice.reason
            else:
                item=drag['item'];moving=drag['moving']
                def commit():
                    self.edit(lambda:dock(self.editor,item,choice.body,choice.face,moving))
                    self.bench_target=choice.body
                    self.catalog_mount=choice.face if choice.face in ('Top','Bottom','Left','Right','Front','Back','Left front','Right front','Left rear','Right rear') else 'Default'
                    if BY_ID[item].variant in ('drive','wheel','hw_tread'):self.suggest_free_mount()
                    self.status='Connected to '+choice.body+' / '+choice.face+'. '+self.wheel_hint(item)
                self.events.append(commit)
            self.drag_candidate=None
            return True
        if action!=glfw.PRESS:return False
        for item,rx,ry,rw,rh in self.catalog_rows:
            if rx<=x<=rx+rw and ry<=y<=ry+rh:
                self.select_card(item)
                self.part_drag=dict(item=item,moving=None,start=(x,y),moved=False)
                return True
        # Clicking a visible socket also supports a precise, non-drag workflow.
        for choice,rx,ry,rw,rh in self.socket_regions:
            if rx<=x<=rx+rw and ry<=y<=ry+rh:
                if choice.valid:
                    self.bench_target=choice.body;self.catalog_mount=choice.face
                    self.status='Ready: '+choice.face+'. Click Add component or drag a part here.'
                else:self.status=choice.reason
                return True
        name=self.pick_bench_body(x,y)
        if name:
            selected=self.bench_module(name) if self.bench_module_pick else name
            self.select(selected)
            item=catalog_id(selected,self.editor.blueprint)
            if item and (self.editor.selected.parent or BY_ID[item].mount=='Floor'):
                self.bench_target=self.editor.selected.parent or selected
                self.part_drag=dict(item=item,moving=selected,start=(x,y),moved=False)
                return True
            self.bench_target=selected
        return False

    def docking_move(self,x,y):
        if self.part_drag is None:return False
        drag=self.part_drag
        drag['moved']|=(x-drag['start'][0])**2+(y-drag['start'][1])**2>36
        if not drag['moved']:return True
        self.prepare_drag_preview()
        self.drag_candidate=self.socket_at(x,y)
        if self.drag_candidate is None:
            name=self.pick_bench_body(x,y)
            if name and name!=drag['moving']:
                self.bench_target=self.compatible_target(name,drag['item'],drag['moving'])
        self.update_drag_pose(x,y)
        return True

    def wheel_hint(self,item):
        variant=BY_ID[item].variant
        if variant=='drive':
            paired=any(c.kind=='differential_torque' for c in self.editor.blueprint.controllers)
            return 'Base is mobile and clear of the floor. '+('WASD drive is ready.' if paired else 'Add the opposite powered wheel for WASD drive.')
        if variant in ('wheel','hw_tread'):return 'Passive wheel: needs a motor/output shaft to drive. Base is mobile.'
        return 'Undo restores the previous assembly.'

    def base_ready(self,mobile):
        target=self.bench_target or self.editor.selection
        if target:
            self.edit(lambda:prepare_base(self.editor,target,mobile))
            self.status='Base '+('released' if mobile else 'anchored')+' and placed clear of the floor. '+('WASD drive is ready.' if any(c.kind=='differential_torque' for c in self.editor.blueprint.controllers) and mobile else 'Passive wheels need motors to drive.' if mobile else 'Anchored bases cannot drive.')

    def project_socket(self,point):
        scene=self.bench_cache[3];a,b=scene.camera
        pos=(a.pos+b.pos)/2;forward=(a.forward+b.forward)/2;up=(a.up+b.up)/2
        right=np.cross(forward,up);v=np.asarray(point)-pos;depth=np.dot(v,forward)
        if depth<=.001:return None
        x,y,w,h=self.bench_rect
        half=(a.frustum_top-a.frustum_bottom)/2
        scale=a.frustum_near/(2*half*depth)
        return (x+w/2+np.dot(v,right)*scale*h,y+h/2-np.dot(v,up)*scale*h)

    def draw_docking(self,ui,text,ww,wh):
        self.socket_regions=[];self.socket_anchors=[]
        if not self.bench_details and not self.part_drag and not self.bench_sockets:return
        target=self.bench_target
        if not self.bench_cache:return
        drag=self.part_drag
        item=drag['item'] if drag else self.catalog_selection
        moving=drag['moving'] if drag else None
        if target not in {b.id for b in self.editor.bodies}:
            return
        choices=self.available_sockets(item,target,moving)
        transforms=poses(self.editor.blueprint)
        offsets={'Top':(0,-55),'Bottom':(0,55),'Left':(-95,-15),'Right':(95,-15),'Front':(-95,25),'Back':(95,25),'tool':(0,-90),'arm_mount':(0,-90),'output':(0,-90)}
        px,py,pw,ph=self.bench_rect
        used=[]
        for face,s in choices.items():
            if BY_ID[item].mount=='Floor' and not s.valid:continue
            t=transforms[s.body]
            point=tuple(a+b for a,b in zip(t.position,rotate(t.quaternion,s.point)))
            projected=self.project_socket(point)
            if projected is None:continue
            cx,cy=projected
            self.socket_anchors.append((s,cx,cy))
            if not px<=cx<=px+pw or not py<=cy<=py+ph:continue
            ox,oy=offsets.get(face,(-100 if face.startswith('Left') else 100, -65 if face.endswith('front') else 65));x=max(px+4,min(px+pw-86,cx+ox-40));y=max(py+8,min(py+ph-32,cy+oy-12))
            while any(abs(y-v)<25 and abs(x-u)<84 for u,v in used) and y+50<py+ph:y+=26
            used.append((x,y))
            color=(.21,.72,.56) if s.valid else (.92,.48,.49)
            ui.line(cx,cy,x+40,y+12,1,color)
            ui.rect(cx-3,cy-3,6,6,color)
            ui.rect(x,y,80,24,(.09,.24,.20) if s.valid else (.22,.12,.14))
            text(face,x+5,y+5,10,color,72)
            self.socket_regions.append((s,x,y,80,24))
        text('Release on the ground, or a green mounting socket.' if BY_ID[item].mount=='Floor' else 'Drop on green markers or labels. Red: unavailable',px+8,py+8,10,(.74,.85,.8),pw-16)
        if drag and drag['moved']:
            text('Placing: '+BY_ID[item].title,px+8,py+ph-43,12,(.75,.96,.84),pw-16)
            hint='Release to place here, or move to a green mounting socket.' if BY_ID[item].mount=='Floor' else self.drag_candidate.reason if self.drag_candidate else 'Move over the target, then release on a green socket.'
            text(hint,px+8,py+ph-22,11,(.8,.9,.85),pw-16)

    def cancel_docking(self):
        self.free_drag_preview()
        self.part_drag=None;self.drag_candidate=None
        self.preview_drag=False;self.press_mouse=None

