"""Precision forms and connection inspector for the workshop."""
from math import atan2, asin, degrees
import time
import glfw
from little_world.construction.connections import frames


def rotation_degrees(q):
    w,x,y,z=q
    return (degrees(atan2(2*(w*x+y*z),1-2*(x*x+y*y))),
            degrees(asin(max(-1,min(1,2*(w*y-z*x))))),
            degrees(atan2(2*(w*z+x*y),1-2*(y*y+z*z))))


def numbers(text, count):
    values=tuple(float(v) for v in text.replace(',', ' ').split())
    if len(values)!=count:
        raise ValueError(f'Enter {count} numbers separated by commas')
    return values


def formatted(values):
    return ', '.join(f'{v:.6g}' for v in values)


class PrecisionInspector:
    def init_inspector(self):
        self.dialog=None
        self.connect_parent=None
        self.source_frame='Bottom'
        self.target_frame='Top'
        self.connection_gap=0.
        self.motor_test=None

    def form(self,title,fields,apply,hint='',text_input=False):
        self.clear_keys()
        self.press_mouse=None
        self.dialog=dict(title=title,fields=[list(f) for f in fields],apply=apply,
                         hint=hint,focus=0,replace=True,error='',query=None,text_input=text_input)

    def choose(self,title,values,apply):
        self.form(title,[('Search','')],apply,'Type to filter, then click an item.')
        self.dialog['query']=tuple(values)

    def character(self,win,code):
        if self.script_open and self.dialog is None:
            self.script_replace(chr(code));return
        if self.dialog is None and self.bench_open and (self.bench_parts or self.bench_details) and self.bench_tab=='Library' and self.parts_focus:
            self.parts_input(('' if self.parts_select_all else self.parts_query)+chr(code))
            return
        if self.dialog is None:
            return
        self.last_input=time.monotonic()
        d=self.dialog
        if d.get('part_info'):return
        field=d['fields'][d['focus']]
        c=chr(code)
        if d['query'] is not None or d.get('text_input') or c in '0123456789., +-eE':
            field[1]=('' if d['replace'] else field[1])+c
            d['replace']=False

    def dialog_key(self,key,action,mods):
        if action not in (glfw.PRESS,glfw.REPEAT):
            return
        d=self.dialog
        if d.get('part_info'):
            if key in (glfw.KEY_ESCAPE,glfw.KEY_ENTER):self.dialog=None
            return
        if key==glfw.KEY_ESCAPE:
            self.dialog=None
        elif key==glfw.KEY_ENTER and d['query'] is None:
            self.events.append(self.apply_form)
        elif key==glfw.KEY_TAB:
            d['focus']=(d['focus']+(-1 if mods & glfw.MOD_SHIFT else 1))%len(d['fields'])
            d['replace']=True
        elif key==glfw.KEY_A and mods & (glfw.MOD_CONTROL|glfw.MOD_SUPER):
            d['replace']=True
        elif key==glfw.KEY_BACKSPACE:
            field=d['fields'][d['focus']]
            field[1]='' if d['replace'] else field[1][:-1]
            d['replace']=False

    def apply_form(self):
        d=self.dialog
        try:
            d['apply']([v for _,v in d['fields']])
        except (ValueError,KeyError,TypeError) as error:
            d['error']=str(error)
        else:
            self.dialog=None

    def exact_form(self):
        b=self.editor.selected
        if b is None:
            return
        if b.robot_asset:
            self.form('Real robot placement',[('Position X, Y, Z (mm)',formatted(v*1000 for v in b.transform.position)),
                ('Rotation X, Y, Z (degrees)',formatted(rotation_degrees(b.transform.quaternion)))],
                lambda v:self.edit(lambda:self.editor.set_pose(tuple(x/1000 for x in numbers(v[0],3)),numbers(v[1],3))),
                'Fixed-size source model; moving the assembly preserves its joints and inertias.')
            return
        def apply(values):
            position=tuple(v/1000 for v in numbers(values[0],3))
            rotation=numbers(values[1],3)
            size=tuple(v/1000 for v in numbers(values[2],len(b.geometry.size)))
            self.edit(lambda:self.editor.set_parameters(position,rotation,size))
        size_label={'box':'Size X, Y, Z (mm)','sphere':'Radius (mm)','cylinder':'Radius, length (mm)'}[b.geometry.shape]
        self.form('Exact dimensions & pose',[
            ('Position X, Y, Z (mm)',formatted(v*1000 for v in b.transform.position)),
            ('Rotation X, Y, Z (degrees)',formatted(rotation_degrees(b.transform.quaternion))),
            (size_label,formatted(v*1000 for v in b.geometry.size))],apply,
            'Relative to parent. Rotation order: X, then Y, then Z.')

    def hinge_form(self):
        h=self.editor.selected_hinge()
        if h is None:
            return
        def apply(values):
            axis=numbers(values[0],3)
            pivot=tuple(v/1000 for v in numbers(values[1],3))
            damping=numbers(values[2],1)[0]
            limits=None if not values[3].strip() else numbers(values[3],2)
            self.edit(lambda:self.editor.configure_hinge(axis,pivot,damping,limits))
        self.form('Hinge settings',[
            ('Axis X, Y, Z',formatted(h.axis)),
            ('Pivot X, Y, Z (mm)',formatted(v*1000 for v in h.position)),
            ('Damping (Nm s/rad)',formatted((h.damping,))),
            ('Lower, upper angle (degrees)',formatted(h.limits or ()))],apply,
            'Axis and pivot are local to this part. Empty limits = free rotation.')

    def gripper_form(self):
        from little_world.construction.manipulation import MATERIALS
        root=self.editor.gripper_root()
        if root is None:return
        prefix=root.removesuffix('_root')
        parts={c.id:c for c in self.editor.blueprint.components}
        pad=parts[prefix+'_finger_left_pad']
        torque=parts[prefix+'_finger_left_joint_motor'].max_torque
        current_material=next(m for m in self.editor.blueprint.materials if m.id==pad.material)
        length=pad.geometry.size[1] if pad.geometry.shape=='cylinder' else pad.geometry.size[0]
        def shape_selected(shape):
            def material_selected(material):
                def apply(values):
                    friction=numbers(values[0],1)[0]
                    strength=numbers(values[1],1)[0]
                    length_mm=numbers(values[2],1)[0]
                    self.edit(lambda:self.editor.configure_gripper(shape,material,friction,strength,length_mm/1000))
                self.form('Gripper / '+shape+' / '+material,[
                    ('Sliding friction coefficient',str(current_material.sliding_friction if (current_material.texture,current_material.density)==(MATERIALS[material].texture,MATERIALS[material].density) else MATERIALS[material].sliding_friction)),
                    ('Torque limit per jaw (Nm)',str(torque)),
                    ('Contact pad length (mm)',str(round(length*1000,3)))],apply,
                    'Torque limits squeeze strength. A library material uses the sourced friction of '
                    'each contact pair; a typed coefficient is unsourced and MuJoCo takes the higher of the two.')
            self.choose('Gripper material / 2 of 3',tuple(MATERIALS),material_selected)
        self.choose('Gripper shape / 1 of 3',('flat','round','narrow'),shape_selected)

    def motor_profile_form(self):
        from little_world.assets.real_motors import PROFILES
        motors=self.editor.selected_motors()
        if not motors:
            self.status='Select a powered joint, then open Connections.'
            return
        current=motors[0]
        def choose_model(label):
            if label=='Ideal motor / remove profile':
                self.edit(lambda:self.editor.set_motor_profile(None,current.max_torque))
                return
            profile=PROFILES[label]
            cap=current.max_torque if current.profile==profile else min(current.max_torque,profile.stall_torque*.3)
            self.form(profile.model+' / 12 V',[
                ('Assumed operating torque cap (Nm)',str(round(cap,4)))],
                lambda values:self.edit(lambda:self.editor.set_motor_profile(profile,numbers(values[0],1)[0])),
                f'Spec endpoints: {profile.stall_torque:g} Nm stall / {profile.no_load_rpm:g} rpm. Curve estimated; continuous rating unknown.'
                +(f' Gearbox friction {profile.friction_torque:.3f} Nm from the {profile.no_load_current:g} A no-load current.'
                  if profile.friction_torque else ''))
        self.choose('Motor model / unvalidated estimate',tuple(PROFILES)+('Ideal motor / remove profile',),choose_model)

    def torque_form(self):
        motors=self.editor.selected_motors()
        self.form('Motor torque limit',[('Maximum torque (Nm)',formatted((motors[0].max_torque if motors else 1.,)))],
                  lambda values:self.edit(lambda:self.editor.set_motor(numbers(values[0],1)[0])),
                  'Ideal torque actuator. Test in simulation using the pulse buttons.')

    def pulse_motor(self,sign):
        motors=self.editor.selected_motors()
        if not self.building and not self.paused and motors:
            self.clear_keys()
            self.motor_test=('machine/'+motors[0].id,sign*motors[0].max_torque*.25,self.state.time+.5)
            self.status='Testing selected motor for 0.5 seconds at 25% torque. Space stops.'

    def draw_connections(self,ui,button,text,section,ww,wh):
        b=self.editor.selected
        text(b.id if b else 'Select a part in the scene',16,120,15,max_width=254)
        if b is None:
            return
        enabled=self.building
        targets=self.editor.connection_targets()
        valid={p.id:p for p in targets}
        if self.connect_parent not in valid:
            self.connect_parent=b.parent if b.parent in valid else next(iter(valid),None)
        parent=valid.get(self.connect_parent)
        source_options=frames(b)
        target_options=frames(parent) if parent else {}
        if self.source_frame not in source_options:
            self.source_frame=next(iter(source_options))
        if self.target_frame not in target_options:
            self.target_frame=next(iter(target_options),None)
        text('Parent: '+(b.parent or 'world / free body'),16,146,11,(.6,.69,.73),254)
        section('SNAP CONNECTION  /  local surface frames',180)
        button('Parent: '+(self.connect_parent or 'none'),12,202,264,
               lambda:self.choose('Choose parent',tuple(valid),lambda v:setattr(self,'connect_parent',v)),enabled and bool(valid))
        button('This part: '+self.source_frame,12,242,264,
               lambda:self.choose('This part connection',tuple(source_options),lambda v:setattr(self,'source_frame',v)),enabled)
        button('Parent face: '+(self.target_frame or 'none'),12,282,264,
               lambda:self.choose('Parent connection',tuple(target_options),lambda v:setattr(self,'target_frame',v)),enabled and bool(parent))
        def gap_form():
            def apply(values):
                gap=numbers(values[0],1)[0]/1000
                if not 0 <= gap <= 1:
                    raise ValueError('Gap must be between 0 and 1000 mm')
                self.connection_gap=gap
            self.form('Connection gap',[('Gap (mm)',formatted((self.connection_gap*1000,)))],apply)
        button(f'Gap: {self.connection_gap*1000:g} mm',12,322,128,gap_form,enabled)
        button('Snap faces',148,322,128,
               lambda:self.edit(lambda:self.editor.snap(self.connect_parent,self.source_frame,self.target_frame,self.connection_gap)),
               enabled and bool(parent),active=True)
        text('Aligns faces; moves the selected subtree.',16,365,11,(.6,.69,.73),254)
        section('JOINT TO PARENT',398)
        hinge=self.editor.selected_hinge()
        button('Fixed',12,420,128,lambda:self.edit(self.editor.make_fixed),enabled and b.parent is not None,active=hinge is None)
        button('Hinge',148,420,128,lambda:self.edit(self.editor.configure_hinge),enabled and b.parent is not None,active=hinge is not None)
        if hinge:
            limits='unlimited' if hinge.limits is None else f'{hinge.limits[0]:g} to {hinge.limits[1]:g} deg'
            text('Axis '+formatted(hinge.axis)+' / '+limits,16,462,11,(.6,.69,.73),254)
            button('Axis, pivot & limits',12,485,264,self.hinge_form,enabled)
            motors=self.editor.selected_motors()
            button(f'Motor: {motors[0].max_torque:g} Nm' if motors else 'Add motor',12,532,168,self.torque_form,enabled)
            button('Remove',188,532,88,lambda:self.edit(lambda:self.editor.set_motor(None)),enabled and bool(motors))
            if not self.building:
                button('Pulse -',12,577,128,lambda:self.pulse_motor(-1),bool(motors) and not self.paused)
                button('Pulse +',148,577,128,lambda:self.pulse_motor(1),bool(motors) and not self.paused)
                text('0.5 s at 25% torque. Space stops.',16,621,11,(.6,.69,.73),254)
            else:
                button('Choose motor model',12,575,264,self.motor_profile_form,enabled and bool(motors))
                profile=motors[0].profile if motors else None
                text(profile.model+' / estimated' if profile else 'Ideal motor / no real model assigned',16,617,11,(.6,.69,.73),254)
        else:
            text('Fixed parts move together with their parent.',16,466,11,(.6,.69,.73),254)
        button('Exact dimensions & pose',12,wh-78,264,self.exact_form,enabled)

    def connection_overlay(self):
        if self.active_tab!='Connect' or not self.building or self.editor.selected is None:
            return
        import mujoco as mj
        import numpy as np
        b=self.editor.selected
        hinge=self.editor.selected_hinge()
        if hinge is None:
            return
        idx=self.model.body('machine/'+b.id).id
        matrix=self.data.xmat[idx].reshape(3,3)
        pivot=self.data.xpos[idx]+matrix@np.array(hinge.position)
        axis=matrix@np.array(hinge.axis)*.09
        if self.render_scene.ngeom < self.render_scene.maxgeom:
            geom=self.render_scene.geoms[self.render_scene.ngeom]
            mj.mjv_initGeom(geom,mj.mjtGeom.mjGEOM_CAPSULE,np.zeros(3),np.zeros(3),np.eye(3).ravel(),np.array((1,.65,.22,1),dtype=np.float32))
            mj.mjv_connector(geom,mj.mjtGeom.mjGEOM_CAPSULE,.003,pivot-axis,pivot+axis)
            geom.category=mj.mjtCatBit.mjCAT_DECOR
            self.render_scene.ngeom+=1

    def draw_dialog(self,ui,button,text,ww,wh):
        if self.dialog is None:
            return
        d=self.dialog
        self.buttons=[]  # Modal hit testing: nothing behind the form is clickable.
        ui.begin()  # The batched font pass must not draw underlying labels over the form.
        ui.rect(0,0,ww,wh,(.035,.052,.065,.85))
        width=540; x=(ww-width)/2; y=100
        ui.rect(x-8,y-8,width+16,wh-184,(.035,.052,.065))
        ui.rect(x,y,width,wh-200,(.10,.14,.18))
        if d.get('part_info'):
            from little_world.assets.catalog import BY_ID
            from little_world.assets.part_guides import part_guide
            from .part_cards import draw_part_picture
            import textwrap
            item=BY_ID[d['part_info']];guide=part_guide(item)
            text(item.title,x+20,y+18,19,max_width=width-40)
            draw_part_picture(ui,item.id,x+20,y+54,130,96)
            text(guide['level']+' / '+item.category,x+168,y+57,13,(.49,.85,.73),width-188)
            for i,line in enumerate(textwrap.wrap(guide['purpose'],width=43)):
                text(line,x+168,y+80+i*17,12,max_width=width-188)
            top=y+166
            for label,key in (('CONNECTS TO','connection'),('TRY THIS','example'),('MODEL SCOPE','limits')):
                text(label,x+20,top,11,(.49,.85,.73));top+=20
                for line in textwrap.wrap(guide[key],width=73):
                    text(line,x+20,top,12,max_width=width-40);top+=17
                top+=12
            if guide['related']:
                def related():
                    self.parts_input(guide['related']);
                    if not self.parts_items():self.bench_hardware=False
                    self.dialog=None;self.bench_parts=True;self.bench_tab='Library'
                button('Find matching parts',x+width-204,wh-154,184,related,tone='primary')
            button('Close guide',x+20,wh-154,132,lambda:setattr(self,'dialog',None))
            return
        text(d['title'],x+20,y+18,20,max_width=width-40)
        text(d['hint'],x+20,y+52,11,(.6,.72,.76),width-40)
        for i,(label,value) in enumerate(d['fields']):
            top=y+87+i*74
            text(label,x+20,top,12,(.65,.75,.78))
            def focus(i=i):
                d['focus']=i; d['replace']=True
            button(value or '(empty)',x+20,top+21,width-40,focus,active=d['focus']==i)
        if d['query'] is not None:
            query=d['fields'][0][1].lower()
            choices=[v for v in d['query'] if query in v.lower()]
            for i,value in enumerate(choices[:max(1,int((wh-410)/35))]):
                def choose(value=value):
                    d['apply'](value)
                    if self.dialog is d:self.dialog=None
                button(value,x+20,y+162+i*35,width-40,choose,h=30)
            if not choices:
                text('No matching parts.',x+20,y+167,13)
        else:
            text(d['error'],x+20,wh-199,12,(1,.6,.4),width-40)
            button('Apply',x+width-150,wh-154,130,self.apply_form,active=True)
        button('Cancel',x+20,wh-154,110,lambda:setattr(self,'dialog',None))
        text('Tab: next field   |   Enter: apply   |   Esc: cancel',x+145,wh-116,11,(.6,.72,.76),width-155)
