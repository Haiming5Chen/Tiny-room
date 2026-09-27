"""Focused build workspace sharing the workshop editor and graphics context."""
import glfw
import mujoco as mj
import numpy as np
from little_world.assets.catalog import CATALOG, BY_ID


from .drag_docking import DragDocking


class BuildWorkspace(DragDocking):
    def init_build_workspace(self):
        self.init_docking()
        self.bench_details=False
        self.bench_parts=True
        self.bench_sockets=False
        self.bench_open=False
        self.bench_hardware=True
        self.bench_style='Anime / kit'
        self.bench_tab='Library'
        self.bench_real_filter='All'
        self.bench_tree_offset=0
        self.bench_expanded={b.id for b in self.editor.bodies if b.parent is None}
        self.bench_module_pick=True
        self.assembly_view='Modules'   # the Assembly tab: modules and their roles, or every part
        self.module_offset=0
        self._structure=None
        self.bench_offset=0
        self.parts_scroll=0.;self.parts_synced_offset=0
        self.parts_query="";self.parts_focus=False;self.parts_select_all=False
        self.parts_track=None;self.parts_drag=None;self.parts_max_scroll=0.
        self.bench_target=None
        self.bench_cache=None
        self.bench_camera=mj.MjvCamera()
        self.bench_camera.azimuth=130
        self.bench_camera.elevation=-25
        self.bench_rect=None
        self.bench_drag=False
        self.bench_part_rect=None

    def open_bench(self):
        if not self.building:
            self.status='Return to build before opening the workbench.'
            return
        self.clear_keys()
        self.bench_open=True
        if self.bench_target not in {b.id for b in self.editor.bodies}:
            self.bench_target=self.editor.selection
        from little_world.assets.ready_assemblies import is_ready
        if self.bench_hardware and not is_ready(BY_ID[self.catalog_selection]):
            self.catalog_selection='drive_left'
        self.bench_cache=None

    def close_bench(self):
        self.free_drag_preview()
        self.bench_open=False
        self.parts_focus=False;self.parts_drag=None
        self.part_drag=None
        self.drag_candidate=None
        self.bench_drag=False
        self.preview_drag=False
        self.press_mouse=None

    def bench_contains(self,x,y):
        if not self.bench_open or self.bench_rect is None:
            return False
        px,py,w,h=self.bench_rect
        return px<x<px+w and py<y<py+h

    def bench_view(self,rect,ww,wh,fw,fh):
        bp=self.editor.blueprint
        if self.bench_cache is None or self.bench_cache[0]!=bp:
            first=self.bench_cache is None
            # The room already compiled this exact design transactionally. Hide
            # room geoms in a separate viewing option rather than compile again.
            model,data=self.model,self.data
            scene=mj.MjvScene(model,maxgeom=10000) if first else self.bench_cache[3]
            ids=np.array([i for i in range(model.ngeom) if model.geom(i).name.startswith('machine/')],dtype=int)
            model.geom_group[:]=1
            model.geom_group[ids]=0
            self.bench_option=mj.MjvOption()
            self.bench_option.geomgroup[:]=0
            self.bench_option.geomgroup[0]=1
            self.bench_cache=(bp,model,data,scene)
            if first and len(ids):
                half=model.geom_size[ids].copy()
                for i,idx in enumerate(ids):
                    if model.geom_type[idx]==mj.mjtGeom.mjGEOM_CYLINDER:
                        half[i]=(half[i,0],half[i,0],half[i,1])
                    elif model.geom_type[idx]==mj.mjtGeom.mjGEOM_SPHERE:
                        half[i,:]=half[i,0]
                extents=np.einsum('nij,nj->ni',np.abs(data.geom_xmat[ids].reshape(-1,3,3)),half)
                lower=(data.geom_xpos[ids]-extents).min(axis=0)
                upper=(data.geom_xpos[ids]+extents).max(axis=0)
                self.bench_camera.lookat[:]=(lower+upper)/2
                self.bench_camera.distance=max(.4,float(np.linalg.norm(upper-lower))*1.35)
        _,model,data,scene=self.bench_cache
        ambient=model.vis.headlight.ambient.copy()
        model.vis.headlight.ambient[:]=(.4,.4,.4)
        mj.mjv_updateScene(model,data,self.bench_option,None,self.bench_camera,mj.mjtCatBit.mjCAT_ALL,scene)
        model.vis.headlight.ambient[:]=ambient
        self.build_stage(scene)
        self.selection_outline(scene)
        scene.flags[mj.mjtRndFlag.mjRND_SHADOW]=False
        scene.flags[mj.mjtRndFlag.mjRND_SKYBOX]=False  # the stage keeps its own dark backdrop
        scene,context=self.spatial_drag_scene(scene)
        x,y,w,h=rect
        mj.mjr_render(mj.MjrRect(int(x*fw/ww),int((wh-y-h)*fh/wh),int(w*fw/ww),int(h*fh/wh)),scene,context)

    def bench_pick(self,x,y):
        if self.bench_cache is None:
            return
        _,model,data,scene=self.bench_cache
        px,py,w,h=self.bench_rect
        ids=[np.zeros(1,dtype=np.int32) for _ in range(3)]
        idx=mj.mjv_select(model,data,self.bench_option,w/h,(x-px)/w,1-(y-py)/h,scene,np.zeros(3),*ids)
        if idx>0:
            native_name=model.body(idx).name
            name=self.backend.robot_owners.get(native_name,native_name).split('/',1)[1]
            self.select(self.bench_module(name) if self.bench_module_pick else name)
            self.bench_target=self.editor.selection
            self.status='Selected '+self.editor.selection

    def bench_add(self):
        from little_world.construction.docking import dock
        item=self.catalog_selection
        mount=BY_ID[item].mount if self.catalog_mount=='Default' else self.catalog_mount
        if mount=='Floor':
            self.edit(lambda:self.editor.add_catalog(item,'Floor'))
        else:self.edit(lambda:dock(self.editor,item,self.bench_target,mount))
        if BY_ID[item].variant in ('drive','wheel','hw_tread'):self.suggest_free_mount()
        self.status=BY_ID[item].title+' added. '+self.wheel_hint(item)

    def choose_bench_mount(self):
        choices=self.available_sockets(self.catalog_selection,self.bench_target) if self.bench_target else {}
        labels={s.face+' - '+('available' if s.valid else s.reason):s.face for s in choices.values()}
        if BY_ID[self.catalog_selection].category=='Structure' or BY_ID[self.catalog_selection].mount=='Floor':labels['Floor - start a separate assembly']='Floor'
        self.choose('Choose a socket / kit compatibility',tuple(labels),lambda label:setattr(self,'catalog_mount',labels[label]))

    def bench_search(self):
        self.parts_focus=True
        self.clear_keys()

    def parts_items(self):
        from little_world.assets.ready_assemblies import is_ready
        words=self.parts_query.lower().split()
        items=[p for p in CATALOG if ((p.variant=='real_robot' or p.variant.startswith('lab_')) if self.bench_style=='Real robots' else p.variant!='real_robot') and (self.bench_style!='Real robots' or getattr(self,'bench_real_filter','All')=='All' or (p.variant=='real_robot')==(self.bench_real_filter=='Arms')) and (not self.bench_hardware or is_ready(p)) and
               all(w in (p.title+' '+p.id+' '+p.category+' '+p.capability).lower() for w in words)]
        if self.bench_hardware:
            order={'real_robot':-1,'ready_base':0,'ready_arm':1,'ready_fork':2,'ready_scoop':2,'ready_tray':2,'ready_camera':2}
            items.sort(key=lambda p:order.get(p.variant,3))
        return items

    def parts_set_scroll(self,value):
        self.parts_scroll=max(0.,min(self.parts_max_scroll,value))
        self.bench_offset=int(self.parts_scroll/136)
        self.parts_synced_offset=self.bench_offset

    def parts_input(self,value):
        self.parts_query=value[:80];self.parts_select_all=False
        self.parts_set_scroll(0)

    def parts_key(self,key,action,mods):
        if not (self.bench_open and (self.bench_parts or self.bench_details) and self.bench_tab=='Library' and self.parts_focus):return False
        if action in (glfw.PRESS,glfw.REPEAT):
            if key in (glfw.KEY_ESCAPE,glfw.KEY_ENTER,glfw.KEY_TAB):self.parts_focus=False
            elif key==glfw.KEY_A and mods&(glfw.MOD_SUPER|glfw.MOD_CONTROL):self.parts_select_all=True
            elif key==glfw.KEY_BACKSPACE:self.parts_input('' if self.parts_select_all else self.parts_query[:-1])
        return True

    def parts_mouse(self,x,y,action):
        if not self.bench_open or self.dialog is not None:return False
        if action==glfw.RELEASE and self.parts_drag is not None:
            self.parts_drag=None;return True
        if action!=glfw.PRESS:return False
        self.parts_focus=False
        if self.bench_tab!='Library' or not (self.bench_parts or self.bench_details):return False
        if 24<=x<=246 and 219<=y<=251:
            self.bench_search();return True
        if self.parts_track:
            tx,ty,tw,th,thumb_y,thumb_h=self.parts_track
            if tx<=x<=tx+tw and ty<=y<=ty+th:
                self.parts_drag=y-thumb_y if thumb_y<=y<=thumb_y+thumb_h else thumb_h/2
                self.parts_move(y);return True
        return False

    def parts_move(self,y):
        if self.parts_drag is None or self.parts_track is None:return False
        tx,ty,tw,th,thumb_y,thumb_h=self.parts_track
        self.parts_set_scroll((y-ty-self.parts_drag)/max(1,th-thumb_h)*self.parts_max_scroll)
        return True

    def wheel_position_form(self):
        from little_world.construction.docking import catalog_id,WHEELS,wheel_at
        selected=self.editor.selected
        own=catalog_id(selected.id,self.editor.blueprint) if selected else None
        moving=selected.id if own and BY_ID[own].variant in WHEELS and selected.parent else None
        item=own if moving else self.catalog_selection
        if BY_ID[item].variant not in WHEELS:
            self.choose_bench_mount();return
        target=selected.parent if moving else self.bench_target
        if not target:self.status='Select a chassis first.';return
        side='Right' if moving and selected.transform.position[1]<0 else 'Left'
        x=selected.transform.position[0] if moving else 0.
        def apply(values):
            self.edit(lambda:wheel_at(self.editor,item,target,values[0].strip().title(),float(values[1])/1000,moving,clearance=float(values[2])/1000))
            self.bench_target=target
        self.form('Wheel mount position',[('Side: Left / Right',side),('Along chassis (mm): negative rear, positive front',str(round(x*1000,3))),('Extra wheel clearance (mm, 0 to 50)','5')],apply,
                  'Any position along the frame; wheel spacing is checked before applying.',text_input=True)

    def drive_settings_form(self):
        from dataclasses import replace
        from little_world.core.drive_settings import DriveSettings
        specs=[c for c in self.editor.blueprint.controllers if c.kind=='differential_torque']
        if not specs:self.status='Add powered wheels on both sides to enable drive assistance.';return
        def apply_settings(settings):
            self.edit(lambda:self.editor._commit(replace(self.editor.blueprint,controllers=tuple(replace(c,drive_settings=settings) if c.kind=='differential_torque' else c for c in self.editor.blueprint.controllers))))
        def choose(value):
            presets={'Gentle':DriveSettings(.25,.35,.5),'Balanced':DriveSettings(),'Responsive':DriveSettings(.8,1.5,1.)}
            if value in presets:apply_settings(presets[value]);return
            old=specs[0].drive_settings
            def custom_apply(v):
                traction=v[4].strip().lower()
                if traction not in ('true','false'):raise ValueError('Traction must be true or false')
                apply_settings(DriveSettings(float(v[0]),float(v[1]),float(v[2]),float(v[3]),traction=='true'))
            self.form('Custom drive assistance',[
                ('Maximum speed (metres / second)',str(old.max_speed)),
                ('Acceleration (metres / second squared)',str(old.acceleration)),
                ('Motor torque fraction (0.05 to 1)',str(old.torque_fraction)),
                ('Wheel-speed feedback gain',str(old.gain)),
                ('Overspeed traction limiter: true / false',str(old.traction).lower())],
                custom_apply,
                'Applies to all drive motors. Each motor remains within its own torque cap.',text_input=True)
        self.choose('Drive assistance',('Gentle','Balanced','Responsive','Custom'),choose)

    def show_part_guide(self):
        self.form('Part guide',[],lambda values:None)
        self.dialog['part_info']=self.catalog_selection

    def replace_selected(self):
        from little_world.construction.component_changes import replacement_options,replace_component
        options={p.title+' / '+' x '.join(str(round(d*1000)) for d in p.dimensions)+' mm':p.id for p in replacement_options(self.editor)}
        if not options:self.status='No compatible replacements for this component.';return
        def apply(label):
            self.edit(lambda:replace_component(self.editor,options[label]))
        self.choose('Replace selected component',tuple(options),apply)

    def delete_selected(self):
        from little_world.construction.component_changes import deletion_impact,delete_component
        impact=deletion_impact(self.editor)
        if not impact['attachments']:
            self.edit(lambda:delete_component(self.editor));return
        label=f"Delete branch: {impact['bodies']} bodies, {len(impact['controls'])} bindings"
        def apply(value):
            if value==label:self.edit(lambda:delete_component(self.editor,True))
        self.choose('Delete '+impact['name']+'?',('Keep assembly',label),apply)
        self.dialog['hint']='Attached parts would also be removed. Undo restores the entire branch.'

    def bench_connect(self):
        self.close_bench()
        self.active_tab='Connect'

    def frame_assembly(self):
        from little_world.construction.docking import world_bounds
        if not self.editor.bodies:return
        lo,hi=world_bounds(self.editor.blueprint)
        self.bench_camera.lookat[:]=(np.array(lo)+hi)/2
        self.bench_camera.distance=max(.4,float(np.linalg.norm(np.array(hi)-lo))*1.35)

    def build_camera_menu(self):
        def choose(view):
            if view=='Anchor base':self.base_ready(False);return
            azimuth,elevation={'Perspective':(130,-25),'Front':(90,-10),'Side':(0,-10),'Top':(90,-89)}[view]
            self.bench_camera.azimuth=azimuth;self.bench_camera.elevation=elevation
            self.frame_assembly()
        self.choose('View your assembly',('Perspective','Front','Side','Top','Anchor base'),choose)

    def build_stage(self,scene):
        """Visual-only floor and metric grid; never touch native collision data."""
        from little_world.construction.docking import world_bounds
        if not self.editor.bodies:return
        if getattr(self,'stage_blueprint',None) is not self.editor.blueprint:
            lo,hi=world_bounds(self.editor.blueprint)
            self.stage_floor=min(0,lo[2])-.006
            self.stage_blueprint=self.editor.blueprint
        z=self.stage_floor
        def geom(kind,size,pos,color):
            if scene.ngeom>=scene.maxgeom:return None
            g=scene.geoms[scene.ngeom]
            mj.mjv_initGeom(g,kind,np.array(size),np.array(pos),np.eye(3).ravel(),np.array(color,dtype=np.float32))
            g.category=mj.mjtCatBit.mjCAT_DECOR;scene.ngeom+=1
            return g
        geom(mj.mjtGeom.mjGEOM_PLANE,(10,10,.1),(0,0,z),(.10,.11,.13,1) if self.bench_style=='Real robots' else (.075,.105,.13,1))
        cx,cy=(round(float(v)*10)/10 for v in self.bench_camera.lookat[:2])
        for i in range(-15,16):
            color=(.19,.26,.30,1) if i%5==0 else (.115,.16,.195,1)
            for a,b in (((cx+i*.1,cy-1.5,z+.001),(cx+i*.1,cy+1.5,z+.001)),
                        ((cx-1.5,cy+i*.1,z+.001),(cx+1.5,cy+i*.1,z+.001))):
                g=geom(mj.mjtGeom.mjGEOM_CAPSULE,(.0006,0,0),(0,0,0),color)
                if g is not None:mj.mjv_connector(g,mj.mjtGeom.mjGEOM_CAPSULE,.0006,np.array(a),np.array(b))

    def draw_immersive(self,ui,button,text,ww,wh,fw,fh):
        ui.begin();self.buttons=[];self.catalog_rows=[];self.bench_part_rect=None
        ui.rect(0,0,ww,wh,(.055,.075,.095))
        self.draw_navigation(ui,button,text,ww)
        button('Hide parts' if self.bench_parts else 'Parts',16,64,100,lambda:setattr(self,'bench_parts',not self.bench_parts),h=28)
        button('Details',124,64,92,lambda:setattr(self,'bench_details',True),h=28)
        button('Frame all',224,64,96,self.frame_assembly,h=28)
        button('View',328,64,80,self.build_camera_menu,h=28)
        button('Sockets',416,64,94,lambda:setattr(self,'bench_sockets',not self.bench_sockets),active=self.bench_sockets,h=28)
        button('Replace',518,64,96,self.replace_selected,self.editor.selected is not None,h=28)
        button('Delete',622,64,96,self.delete_selected,self.editor.selected is not None,h=28)
        button('Undo',ww-302,64,65,lambda:self.edit(self.editor.undo),bool(self.editor.past),h=28)
        button('Redo',ww-229,64,65,lambda:self.edit(self.editor.redo),bool(self.editor.future),h=28)
        button('Back to room',ww-156,64,132,self.close_bench,h=28)
        if self.bench_parts:
            ui.rect(16,100,274,wh-146,(.08,.11,.14))
            self.draw_parts_tray(ui,button,text,24,258,wh)
        left=306 if self.bench_parts else 16
        width=ww-left-16
        self.bench_rect=(left,104,width,wh-258)
        ui.rect(left,wh-142,width,96,(.075,.105,.13))
        item=BY_ID[self.catalog_selection]
        bodies={b.id:b for b in self.editor.bodies}
        if self.bench_target not in bodies:self.bench_target=next(iter(bodies),None)
        mount=item.mount if self.catalog_mount=='Default' else self.catalog_mount
        if not bodies and item.category=='Structure':mount='Floor';self.catalog_mount='Floor'
        choice=self.available_sockets(item.id,self.bench_target).get(mount) if bodies else None
        text(item.title,left+14,wh-127,15,max_width=width-310)
        hint=('Drop for an anchored arm. Arm controls shows the joint keys.' if item.variant=='real_robot' and mount=='Floor' else 'Drop in the build area to place this assembly.' if mount=='Floor' else mount+' of '+self.bench_target+' / '+item.capability if choice and choice.valid else choice.reason if choice else 'Select a target or start a separate structure')
        text(hint,left+14,wh-104,11,(.57,.74,.72),width-310)
        button('Part guide',ww-294,wh-132,108,self.show_part_guide,h=36)
        button('Add component',ww-178,wh-132,146,self.bench_add,(choice is not None and choice.valid) or mount=='Floor',h=36,tone='primary')
        button('Focus selected',left+12,wh-79,104,self.focus_bench,self.editor.selected is not None,h=26)
        button('Mount position',left+124,wh-79,120,self.wheel_position_form,self.editor.selected is not None,h=26)
        button('Free base + ground',left+252,wh-79,158,lambda:self.base_ready(True),bool(bodies),h=26)
        if self.joint_control.specs:
            button('Operate robot',left+418,wh-79,110,self.operate_robot,h=26,tone='primary')
        else:button('Drive assist',left+418,wh-79,110,self.drive_settings_form,bool(self.channels),h=26)
        button('Pick: component' if self.bench_module_pick else 'Pick: detail',left+536,wh-79,140,lambda:setattr(self,'bench_module_pick',not self.bench_module_pick),h=26)
        text(self.status,24,wh-27,11,(.65,.75,.77),ww-48)
        ui.flush(ww,wh,fw,fh)
        self.bench_view(self.bench_rect,ww,wh,fw,fh)
        ui.begin()
        state=('MOBILE' if any(b.dynamic for b in self.editor.bodies) else 'ANCHORED')+' / '+self.bench_style.upper()
        if not self.part_drag and not self.bench_sockets:
            text('BUILD STAGE / '+state,left+16,122,11,(.68,.82,.84),width-32)
            text('Selected: '+(self.editor.selection or 'none')+' / Replace or Delete above',left+16,143,11,(.52,.67,.72),width-32)
            text(self.structure_line(),left+16,164,11,(.52,.67,.72),width-32)
            found,stance,_=self.machine_modules()
            line=self.stance_words(found,stance)
            text(line[0].upper()+line[1:],left+16,185,11,(.96,.72,.38) if 'tips over' in line or 'rocks' in line else (.52,.67,.72),width-32)
            last=self.last_run_line()
            if last:text(last,left+16,206,11,(.96,.72,.38) if self.last_run_troubled() else (.52,.67,.72),width-32)
        text('10 cm grid',ww-106,wh-176,10,(.49,.64,.69))
        self.draw_docking(ui,text,ww,wh)

    def draw_parts_tray(self,ui,button,text,left,list_width,wh):
        button('Library',left,104,125,lambda:setattr(self,'bench_tab','Library'),active=self.bench_tab=='Library',h=26)
        button('Assembly',left+133,104,125,lambda:setattr(self,'bench_tab','Assembly'),active=self.bench_tab=='Assembly',h=26)
        self.catalog_rows=[]
        if self.bench_tab=='Library':
            text('COMPONENT LIBRARY',left+4,148,11,(.6,.74,.77),list_width)
            button('Ready to build',left,176,158,lambda:self.bench_filter(True),active=self.bench_hardware)
            button('Advanced',left+166,176,92,lambda:self.bench_filter(False),active=not self.bench_hardware)
            button('',left,219,list_width-36,self.bench_search,active=self.parts_focus)
            self.buttons[-1].label='Search parts'
            query=self.parts_query+('|' if self.parts_focus else '')
            text(query or 'Search parts...',left+10,227,13,max_width=list_width-56)
            button('X',left+list_width-30,219,30,lambda:self.parts_input(''),bool(self.parts_query))
            items=self.parts_items()
            top,bottom=268,wh-110;viewport=max(1,bottom-top)
            self.parts_max_scroll=max(0,len(items)*136-6-viewport)
            if self.bench_offset!=self.parts_synced_offset:self.parts_set_scroll(self.bench_offset*136)
            else:self.parts_set_scroll(self.parts_scroll)
            card_width=list_width-18
            ui.clip=(left,top,card_width,viewport)
            for i,item in enumerate(items):
                y=top+i*136-self.parts_scroll
                if y+130<=top or y>=bottom:continue
                hit_y=max(top,y);hit_h=min(bottom,y+130)-hit_y
                self.catalog_rows.append((item.id,left,hit_y,card_width,hit_h))
                button('',left,y,card_width,lambda k=item.id:self.select_card(k),active=item.id==self.catalog_selection,h=130)
                self.buttons[-1].label=item.title
                self.buttons[-1].y=hit_y;self.buttons[-1].height=hit_h
                text(item.title,left+12,y+10,13,max_width=card_width-24)
                from .part_cards import draw_part_card
                draw_part_card(ui,text,item,left,y,card_width)
            ui.clip=None
            tx=left+list_width-12
            thumb_h=min(viewport,max(36,viewport*viewport/max(viewport,len(items)*136-6)))
            thumb_y=top+(viewport-thumb_h)*self.parts_scroll/max(1,self.parts_max_scroll)
            self.parts_track=(tx,top,12,viewport,thumb_y,thumb_h)
            ui.rect(tx,top,12,viewport,(.12,.18,.22))
            ui.rect(tx+2,thumb_y,8,thumb_h,(.38,.65,.69))
            if not items:
                text('No matching parts',left+12,top+22,14)
                text('Try Advanced for raw components.',left+12,top+48,11)
            rows=max(1,int(viewport/136))
            button('<',left,wh-100,48,lambda:self.parts_set_scroll(self.parts_scroll-viewport),self.parts_scroll>0)
            button('>',left+list_width-48,wh-100,48,lambda:self.parts_set_scroll(self.parts_scroll+viewport),self.parts_scroll<self.parts_max_scroll)
            text(f'{len(items)} '+('matches' if self.parts_query else 'assemblies' if self.bench_hardware else 'parts'),left+63,wh-91,12,(.6,.73,.76))
        else:
            self.draw_assembly_tree(ui,button,text,left,list_width,wh)

    def draw_bench(self,ui,button,text,section,ww,wh,fw,fh):
        if not self.bench_details:
            self.draw_immersive(ui,button,text,ww,wh,fw,fh)
            return
        ui.begin()
        self.buttons=[]
        ui.rect(0,0,ww,wh,(.055,.075,.095))
        self.draw_navigation(ui,button,text,ww)
        text('BUILD / Precision details',24,69,12,(.61,.72,.77))
        button('Hide details',340,64,120,lambda:setattr(self,'bench_details',False),h=26)
        button('Keyboard',ww-410,64,100,lambda:(self.close_bench(),setattr(self,'panel_mode','keys'),setattr(self,'control_panel',True)),h=26)
        button('Undo',ww-302,64,65,lambda:self.edit(self.editor.undo),bool(self.editor.past),h=26)
        button('Redo',ww-229,64,65,lambda:self.edit(self.editor.redo),bool(self.editor.future),h=26)
        button('Back to room',ww-156,64,132,self.close_bench,h=26)
        left=24; list_width=258; right=ww-278
        ui.rect(left-8,94,list_width+16,wh-140,(.08,.11,.14))
        ui.rect(right-8,94,262,wh-140,(.08,.11,.14))
        self.draw_parts_tray(ui,button,text,left,list_width,wh)
        middle=306; middle_width=right-middle-18
        text('YOUR ASSEMBLY / '+('MOBILE' if any(b.dynamic for b in self.editor.bodies) else 'ANCHORED BASE'),middle+8,112,12,(.6,.73,.76),middle_width-16)
        button('Focus selected',middle+8,133,120,self.focus_bench,self.editor.selected is not None,h=24)
        button('Pick: component' if self.bench_module_pick else 'Pick: detail',middle+136,133,136,lambda:setattr(self,'bench_module_pick',not self.bench_module_pick),h=24)
        self.bench_rect=(middle,164,middle_width,wh-282)
        # The rectangle backdrop is omitted: the real 3D viewport is rendered
        # beneath the batched UI, which paints only the surrounding panels.
        ui.rect(middle,wh-108,middle_width,62,(.08,.11,.14))
        button('Free base + ground',middle+8,wh-100,160,lambda:self.base_ready(True),h=28)
        button('Anchor base',middle+176,wh-100,120,lambda:self.base_ready(False),h=28)
        text('Drag parts to connect / empty space to orbit / right-drag to pan',middle+8,wh-63,10,(.57,.7,.74),middle_width-16)
        item=BY_ID[self.catalog_selection]
        text(item.title,right+4,111,16,max_width=244)
        text(item.capability.upper(),right+4,140,10,(.35,.8,.67),244)
        self.bench_part_rect=(right,166,246,174)
        import textwrap
        for i,line in enumerate(textwrap.wrap(item.description,39)[:3]):
            text(line,right+4,353+i*17,11,(.64,.73,.77),238)
        mount=item.mount if self.catalog_mount=='Default' else self.catalog_mount
        bodies={b.id:b for b in self.editor.bodies}
        if self.bench_target not in bodies:
            self.bench_target=next(iter(bodies),None)
        button('Attach to: '+(self.bench_target or 'none'),right,414,246,
               lambda:self.choose('Choose assembly target',tuple(bodies),lambda v:setattr(self,'bench_target',v)),bool(bodies))
        if not bodies and item.category=='Structure':mount='Floor';self.catalog_mount='Floor'
        button('Mount: '+mount,right,454,246,self.choose_bench_mount,bool(bodies) or item.category=='Structure')
        choice=self.available_sockets(item.id,self.bench_target).get(mount) if bodies else None
        text(choice.reason if choice else 'Loose part on floor',right+4,488,10,(.58,.78,.7) if choice and choice.valid else (.85,.48,.45),238)
        button('Add component',right,500,246,self.bench_add,(choice is not None and choice.valid) or mount=='Floor',tone='primary',h=38)
        selected=self.editor.selected
        text('SELECTED IN ASSEMBLY',right+4,558,10,(.51,.64,.69))
        text(selected.id if selected else 'Nothing selected',right+4,579,12,max_width=238)
        button('Duplicate',right,649,119,self.duplicate_form,selected is not None,h=28)
        button('Delete subtree',right+127,649,119,lambda:self.edit(self.editor.delete),selected is not None,h=28,tone='danger')
        button('Gripper setup' if self.editor.gripper_root() else 'Dimensions',right,610,119,self.gripper_form if self.editor.gripper_root() else self.exact_form,selected is not None,h=28)
        button('Connections',right+127,610,119,self.bench_connect,selected is not None,h=28)
        text(self.status,24,wh-29,11,(.6,.73,.76),ww-48)
        # Flush panel backgrounds first, then draw the two live viewports. Their
        # independent cameras never affect the room camera or the saved Blueprint.
        ui.flush(ww,wh,fw,fh)
        self.bench_view(self.bench_rect,ww,wh,fw,fh)
        self.render_catalog_preview(ww,wh,fw,fh,rect=self.bench_part_rect)
        ui.begin()
        self.draw_docking(ui,text,ww,wh)

    def bench_module(self,name):
        bodies={b.id:b for b in self.editor.bodies}
        original=name
        while name in bodies:
            body=bodies[name]
            attachments={a.id for a in body.attachments}
            if body.id.endswith('_root') or {'assembly_top','mount'} <= attachments:
                return name
            if body.parent is None:
                return original
            name=body.parent
        return original

    def focus_bench(self):
        if self.editor.selected is None:
            return
        included=self.editor.subtree_ids()
        ids=[self.model.geom('machine/'+b.id+'_geom').id for b in self.editor.bodies if b.id in included]
        centres=self.data.geom_xpos[ids]
        radii=self.model.geom_rbound[ids,None]
        lower=(centres-radii).min(axis=0)
        upper=(centres+radii).max(axis=0)
        self.bench_camera.lookat[:]=(lower+upper)/2
        self.bench_camera.distance=max(.06,float(np.linalg.norm(upper-lower))*1.1)

    def duplicate_form(self):
        from .inspector import numbers
        def apply(values):
            offset=tuple(v/1000 for v in numbers(values[0],3))
            self.edit(lambda:self.editor.duplicate(offset))
            self.reveal_in_tree(self.editor.selection)
            self.bench_target=self.editor.selected.parent or self.editor.selection
            self.status='Component duplicated with its attached parts and internal joints.'
        self.form('Duplicate selected assembly', [('Offset X, Y, Z (mm)','50, 0, 0')],apply,
                  'Copies the selected part and its descendants. Offset is relative to parent.')

    def tree_rows(self):
        children={}
        for body in self.editor.bodies:
            children.setdefault(body.parent,[]).append(body)
        rows=[]
        def visit(parent,depth):
            for body in children.get(parent,()):
                rows.append((body,depth,body.id in children))
                if body.id in self.bench_expanded:
                    visit(body.id,depth+1)
        visit(None,0)
        return rows

    def reveal_in_tree(self,name):
        bodies={b.id:b for b in self.editor.bodies}
        parent=bodies[name].parent
        while parent is not None:
            self.bench_expanded.add(parent)
            parent=bodies[parent].parent
        self.bench_tab='Assembly'
        self.assembly_view='Parts'
        rows=self.tree_rows()
        self.bench_tree_offset=next(i for i,(b,_,_) in enumerate(rows) if b.id==name)

    def toggle_tree(self,name):
        if name in self.bench_expanded:
            self.bench_expanded.remove(name)
        else:
            self.bench_expanded.add(name)

    def tree_select(self,name):
        self.select(name)
        self.bench_target=name

    def machine_modules(self):
        """Modules and stance of the current design, computed once per revision."""
        bp=self.editor.blueprint
        if self._structure is None or self._structure[0] is not bp:
            from little_world.construction.structure import modules,standing,centre_of_mass
            self._structure=(bp,modules(bp),standing(bp),centre_of_mass(bp)[0])
        return self._structure[1:]

    def structure_line(self):
        """One line on the Build stage: what the machine is made of and how it stands."""
        found,_,mass=self.machine_modules()
        from collections import Counter
        counts=Counter(m.role for m in found if m.role in ('drive','support','arm','tool','sensor'))
        words={'drive':('drive','drives'),'support':('support','supports'),'arm':('arm','arms'),
               'tool':('tool','tools'),'sensor':('sensor','sensors')}
        parts=['base']+[f'{n} {words[r][n>1]}' if n>1 else words[r][0] for r,n in counts.items()]
        return ' + '.join(parts)+f' / {mass:.2f} kg'

    def stance_words(self,found,stance):
        """How the design settles on a level floor, in words (ADR 0015)."""
        if not any(b.dynamic for b in self.editor.bodies if b.parent is None):return 'anchored'
        if stance is None:return 'nothing to stand on'
        if stance.tips_over:return 'tips over: its centre of mass is outside anything it can stand on'
        from collections import Counter
        from little_world.construction.structure import module_roots
        owner=module_roots(self.editor.blueprint)
        roles={m.root:m for m in found}
        on=Counter()
        for root in {owner[b] for b in stance.touching}:
            m=roles.get(root)
            on[m.role if m and m.role in ('wheel','support','drive','base') else 'other']+=1
        names={'wheel':('wheel','wheels'),'support':('support','supports'),'drive':('drive','drives'),
               'base':('base','base'),'other':('other part','other parts')}
        order=('wheel','drive','support','base','other')
        feet=' and '.join(f'{on[r]} {names[r][on[r]>1]}' if r!='base' else 'its base' for r in order if on[r])
        tilt=f', tilted {stance.tilt:.1f} deg' if stance.tilt>=.1 else ''
        rock='  (rocks easily)' if stance.margin<.01 else ''
        # Static stability: the floor tilt each way that would tip it (ADR 0020).
        side=min((a for s,a in stance.tips if s in ('left','right')),default=None)
        ends=min((a for s,a in stance.tips if s in ('forward','back')),default=None)
        tips=f'; tips on a {side:.0f} deg side slope, {ends:.0f} deg end on' if side is not None and ends is not None else ''
        return f'rests on {feet}{tilt}; centre of mass {100*stance.margin:.1f} cm inside{rock}{tips}'

    def draw_assembly_tree(self,ui,button,text,left,width,wh):
        button('Modules',left,140,125,lambda:setattr(self,'assembly_view','Modules'),active=self.assembly_view=='Modules',h=30)
        button('Parts',left+133,140,125,lambda:setattr(self,'assembly_view','Parts'),active=self.assembly_view=='Parts',h=30)
        if self.assembly_view=='Modules':
            self.draw_module_list(ui,button,text,left,width,wh)
            return
        def search():
            def found(name):
                self.tree_select(name)
                self.reveal_in_tree(name)
            self.choose('Find part in assembly',tuple(b.id for b in self.editor.bodies),found)
        button('Find in assembly',left,180,width,search,h=28)
        button('Collapse all',left,214,125,lambda:self.bench_expanded.clear(),h=26)
        button('Select parent',left+133,214,125,
               lambda:self.tree_select(self.editor.selected.parent),
               self.editor.selected is not None and self.editor.selected.parent is not None,h=26)
        rows=self.tree_rows()
        visible=max(1,int((wh-380)/32))
        self.bench_tree_offset=min(self.bench_tree_offset,max(0,len(rows)-visible))
        for i,(body,depth,has_children) in enumerate(rows[self.bench_tree_offset:self.bench_tree_offset+visible]):
            y=250+i*32
            indent=min(depth,5)*10
            if has_children:
                button('-' if body.id in self.bench_expanded else '+',left+indent,y,24,
                       lambda n=body.id:self.toggle_tree(n),h=26)
            button(body.id,left+indent+28,y,width-indent-28,
                   lambda n=body.id:self.tree_select(n),active=body.id==self.editor.selection,h=26)
        button('<',left,wh-100,48,lambda:setattr(self,'bench_tree_offset',max(0,self.bench_tree_offset-visible)),self.bench_tree_offset>0)
        button('>',left+width-48,wh-100,48,lambda:setattr(self,'bench_tree_offset',min(max(0,len(rows)-visible),self.bench_tree_offset+visible)),self.bench_tree_offset+visible<len(rows))
        text(f'{len(self.editor.bodies)} parts',left+63,wh-91,12,(.6,.73,.76))

    def draw_module_list(self,ui,button,text,left,width,wh):
        """The machine as modules - base, drives, wheels, supports, arm, tool - with their
        roles, keys and masses. Clicking one selects its root, as Pick: component does."""
        found,_,mass=self.machine_modules()
        text('WHAT THIS MACHINE IS MADE OF',left+4,182,11,(.6,.74,.77),width)
        row=46;top=202
        visible=max(1,int((wh-top-110)/row))
        self.module_offset=min(self.module_offset,max(0,len(found)-visible))
        owner=self.bench_module(self.editor.selection) if self.editor.selection else None
        for i,m in enumerate(found[self.module_offset:self.module_offset+visible]):
            y=top+i*row
            indent=min(m.depth,4)*12
            button('',left+indent,y,width-indent,lambda r=m.root:self.tree_select(r),
                   active=m.root in (self.editor.selection,owner),h=row-4)
            self.buttons[-1].label=m.title
            text(m.role.upper(),left+indent+8,y+5,10,(.37,.83,.69))
            text(m.title,left+indent+8+ui.width(m.role.upper(),10)+8,y+3,12,max_width=width-indent-24-ui.width(m.role.upper(),10))
            keys='  '.join(f'{p}/{n}' for _,p,n in m.keys)
            weight='mass in its model file' if m.mass is None else f'{m.mass:.2f} kg'
            detail=weight+(f'  /  keys {keys}' if keys else '')+(f'  /  {len(m.actuators)} motor'+('s' if len(m.actuators)>1 else '') if m.actuators and not keys else '')
            text(detail,left+indent+8,y+22,10,(.6,.73,.76),width-indent-16)
        button('<',left,wh-100,48,lambda:setattr(self,'module_offset',max(0,self.module_offset-visible)),self.module_offset>0)
        button('>',left+width-48,wh-100,48,lambda:setattr(self,'module_offset',min(max(0,len(found)-visible),self.module_offset+visible)),self.module_offset+visible<len(found))
        text(f'{len(found)} modules / {mass:.2f} kg',left+60,wh-91,12,(.6,.73,.76))

    def bench_filter(self,hardware):
        self.bench_hardware=hardware
        self.bench_offset=0

    def set_real_filter(self,label):
        self.bench_real_filter=label
        self.parts_input('')
        items=self.parts_items()
        if items:self.select_card(items[0].id)

    def set_library_style(self,style):
        self.cancel_docking()
        self.bench_style=style
        self.parts_input('')
        self.bench_tab='Library'
        items=self.parts_items()
        if items:self.select_card(items[0].id)
