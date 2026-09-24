"""Temporary native model for mesh-correct, cursor-following placement previews."""
from dataclasses import replace
import numpy as np
import mujoco as mj
from little_world.core.component import Body,Transform
from little_world.core.entity import Entity
from little_world.core.scene import Scene
from little_world.assets.catalog import BY_ID
from little_world.construction.connections import rotate,multiply,module_bounds
from little_world.construction.docking import poses


class SpatialDrag:
    def free_drag_preview(self):
        preview=getattr(self,'drag_preview',None)
        if preview:
            preview['context'].free();preview['backend'].close()
        self.drag_preview=None

    def prepare_drag_preview(self):
        if getattr(self,'drag_preview',None) or not self.part_drag:return
        from little_world.physics.mujoco_backend import MujocoBackend
        moving=self.part_drag['moving']
        if moving:
            from little_world.construction.editor import AssemblyEditor
            from little_world.core.blueprint import Blueprint
            editor=AssemblyEditor(self.editor.blueprint);editor.select(moving);included=editor.subtree_ids()
            bp=Blueprint(tuple(replace(c,parent=None) if c.id==moving else c for c in editor.blueprint.components if c.id in included),
                editor.blueprint.materials,tuple(c for c in editor.blueprint.controllers if set(c.actuators)<=included))
        else:bp=BY_ID[self.part_drag['item']].blueprint()
        root=next(b for b in bp.components if isinstance(b,Body) and b.parent is None)
        bp=replace(bp,components=tuple(replace(b,dynamic=False,transform=Transform()) if b.id==root.id else b for b in bp.components))
        backend=MujocoBackend()
        backend.compile(Scene((Entity('machine',self.editor.blueprint),Entity('ghost',bp))),.002)
        model=backend.model
        ids=np.array([i for i in range(model.ngeom) if model.geom(i).name.startswith('ghost/') and model.geom_rgba[i,3]>0],dtype=int)
        moving=self.part_drag['moving']
        if moving:
            from little_world.construction.docking import subtree
            hidden={'machine/'+name for name in subtree(self.editor.blueprint,moving)}
            for i in range(model.ngeom):
                name=model.body(int(model.geom_bodyid[i])).name
                owner=backend.robot_owners.get(name,name)
                if owner in hidden:model.geom_rgba[i,3]=0
        # The preview model has no room; use its own mesh context and original colors.
        scene=mj.MjvScene(model,maxgeom=10000)
        lower,upper=module_bounds(bp)
        self.bench_camera.distance=max(self.bench_camera.distance,float(np.linalg.norm(np.array(upper)-lower))*1.35)
        self.drag_preview=dict(backend=backend,scene=scene,context=mj.MjrContext(model,150),root=model.body('ghost/'+root.id).id,
            ids=ids,rgba=model.geom_rgba[ids].copy(),bounds=module_bounds(bp),pose=None,valid=False)

    def ground_cursor(self,x,y):
        if not self.bench_cache or not self.bench_contains(x,y):return None
        a,b=self.bench_cache[3].camera
        origin=(a.pos+b.pos)/2;forward=(a.forward+b.forward)/2;up=(a.up+b.up)/2
        right=np.cross(forward,up);px,py,w,h=self.bench_rect
        ratio=(a.frustum_top-a.frustum_bottom)/(2*a.frustum_near)
        direction=forward+right*((x-px-w/2)/(h/2))*ratio-up*((y-py-h/2)/(h/2))*ratio
        if direction[2]>=-1e-6:return None
        distance=-origin[2]/direction[2]
        if distance<=0 or distance>20:return None
        return origin+direction*distance

    def update_drag_pose(self,x,y):
        preview=getattr(self,'drag_preview',None)
        if preview is None:return
        choice=self.drag_candidate
        if choice is not None:
            parent=poses(self.editor.blueprint)[choice.body]
            preview['pose']=Transform(tuple(np.array(parent.position)+rotate(parent.quaternion,choice.transform.position)),multiply(parent.quaternion,choice.transform.quaternion))
            preview['valid']=choice.valid
            preview['floor']=False
        else:
            point=self.ground_cursor(x,y)
            if point is None:preview['pose']=None;return
            preview['pose']=Transform((float(point[0]),float(point[1]),-preview['bounds'][0][2]+.002))
            preview['valid']=BY_ID[self.part_drag['item']].mount=='Floor'
            preview['floor']=True

    def spatial_drag_scene(self,scene):
        preview=getattr(self,'drag_preview',None)
        if not self.part_drag or not self.part_drag['moved'] or not preview:return scene,self.context
        self.update_drag_pose(*self.last_mouse)
        pose=preview['pose']
        if pose is None:return scene,self.context
        backend=preview['backend'];model,data=backend.model,backend.data
        model.body_pos[preview['root']]=pose.position
        model.body_quat[preview['root']]=pose.quaternion
        mj.mj_forward(model,data)
        ids=preview['ids'];colors=preview['rgba'].copy()
        tint=np.array((.3,1.,.7) if preview['valid'] else (1.,.25,.2))
        colors[:,:3]=colors[:,:3]*.65+tint*.35;colors[:,3]=.60
        model.geom_rgba[ids]=colors
        option=mj.MjvOption()
        mj.mjv_updateScene(model,data,option,None,self.bench_camera,mj.mjtCatBit.mjCAT_ALL,preview['scene'])
        self.build_stage(preview['scene'])
        preview['scene'].flags[mj.mjtRndFlag.mjRND_SHADOW]=False
        return preview['scene'],preview['context']

    def commit_floor_drag(self,item,pose,moving=None):
        """One undo revision; the committed transform equals the displayed ghost."""
        from little_world.construction.editor import AssemblyEditor
        trial=AssemblyEditor(self.editor.blueprint)
        if moving:
            trial.select(moving)
            trial._replace(replace(trial.selected,parent=None,transform=pose))
        else:
            trial.add_catalog(item,'Floor')
            trial._replace(replace(trial.selected,transform=pose))
        self.editor._commit(trial.blueprint,trial.selection)
