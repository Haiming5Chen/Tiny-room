"""Visual sequence editor; programs are data and run on simulation time."""
from dataclasses import replace
import glfw
from little_world.programming.program import Program,Block,Runner
from .inspector import numbers


class ProgramWorkspace:
    def init_program(self):
        self.program=Program();self.runner=Runner();self.program_selected=0;self.program_offset=0
        self.program_past=[];self.program_future=[];self.program_drag=None;self.program_rows=[]
        self.panel_mode='keys';self.program_keys=set();self.program_drive=None
        self.eye=None;self.look_rect=None

    @property
    def program_path(self):return self.path.with_suffix('.program.json')

    def show_program(self):
        self.close_bench();self.control_panel=True;self.panel_mode='program'

    def program_edit(self,program):
        if self.runner.state in ('running','paused'):raise ValueError('Stop the program before editing')
        self.program_past.append(self.program);self.program_future.clear();self.program=program
        self.program_selected=min(self.program_selected,max(0,len(program.blocks)-1))

    def program_undo(self):
        if self.program_past:
            self.program_future.append(self.program);self.program=self.program_past.pop()

    def program_redo(self):
        if self.program_future:
            self.program_past.append(self.program);self.program=self.program_future.pop()

    def save_program(self):
        self.program_path.parent.mkdir(parents=True,exist_ok=True)
        temporary=self.program_path.with_suffix('.json.tmp')
        temporary.write_text(self.program.to_json());temporary.replace(self.program_path)
        self.status='Program saved: '+self.program_path.name

    def load_program(self):
        self.program_edit(Program.from_json(self.program_path.read_text()))

    def pickup_program(self):
        specs=self.editor.blueprint.controllers
        def action(key,duration):
            spec=next((c for c in specs if c.kind=='keyboard_position' and key in (c.positive_key,c.negative_key)),None)
            if spec is None:raise ValueError('Pickup template needs G/H gripper and R shoulder bindings')
            return Block('action',spec.id,1 if key==spec.positive_key else -1,duration)
        self.program_edit(Program((Block(duration=.5),action('G',.9),Block(duration=.2),action('R',.8),Block(duration=.6),action('H',1),Block(duration=.8))))

    def program_options(self):
        self.form('Program settings',[('Repeat count',str(self.program.repeat)),('Keyboard trigger: F6 / F7 / F8',self.program.trigger)],
            lambda v:self.program_edit(replace(self.program,repeat=int(v[0]),trigger=v[1].upper().strip())),text_input=True)

    def pick_place_program(self):
        """Pick up the object at the gripper and set it in the field's tray, each waypoint
        solved for this arm (ADR 0016)."""
        from little_world.control.tool_motion import pick_and_place
        if self.tool_motion is None:raise ValueError(self.tool_reason or 'The template needs an arm with a gripper')
        jaws=self.jaws_action()
        if jaws is None:raise ValueError('Bind the gripper to a keyboard action first')
        try:tray=self.model.body('field/tray_base').id
        except KeyError:raise ValueError('Choose the Pick and place field: its tray is where the template sets the cube down') from None
        top=float(self.data.xpos[tray][2]+max(self.model.geom_size[g][2] for g in range(self.model.ngeom) if self.model.geom_bodyid[g]==tray))
        self.program_edit(pick_and_place(self.tool_motion,jaws.id,(float(self.data.xpos[tray][0]),float(self.data.xpos[tray][1]),top)))
        self.status='Pick and place solved for this arm. Run it: the field judges the result.'

    def fetch_program(self):
        """Drive to the table, pick the cube, bring it back and set it in the bin, each stop
        and waypoint solved for this machine (ADR 0018)."""
        from little_world.control.tool_motion import fetch
        from little_world.fields import BIN_SIZE
        if self.tool_motion is None:raise ValueError(self.tool_reason or 'The Fetch program needs an arm with a gripper')
        if getattr(self,'base_pose',None) is None:raise ValueError('The Fetch program needs a left and a right drive wheel')
        jaws=self.jaws_action()
        if jaws is None:raise ValueError('Bind the gripper to a keyboard action first')
        try:bin_id=self.model.body('field/bin_base').id;self.model.body('objects/fetch_cube')
        except KeyError:raise ValueError('Choose the Fetch field: its table, cube and bin are what the program uses') from None
        top=float(self.data.xpos[bin_id][2]+max(self.model.geom_size[g][2] for g in range(self.model.ngeom) if self.model.geom_bodyid[g]==bin_id))
        place=(float(self.data.xpos[bin_id][0]),float(self.data.xpos[bin_id][1]),top)
        if self.building:
            # Plan from the machine as it stands, settled on the floor, not level as designed.
            self.simulate()
            for _ in range(round(.6/self.world.timestep)):
                commands=dict(self.drive_control.step_commands((0.,0.),self.world.timestep,angular=True))
                commands.update(self.joint_control.step_commands(self.world.timestep))
                self.state=self.world.step(commands)
            self.paused=True
        look=self.field_camera() is not None
        self.program_edit(fetch(self.tool_motion,self.base_pose,jaws.id,'objects/fetch_cube',place,reach_in=BIN_SIZE/2-.045,look=look))
        self.status=('Fetch solved for this machine: drive, look with the table camera, pick, bring back, set down. Run it: the field judges it.'
                     if look else 'Fetch solved for this machine: drive, pick, bring back, set down. Run it: the field judges it.')

    def field_camera(self):
        """The chosen field's own depth camera, (camera id, sensor id), or None (ADR 0032)."""
        from little_world.fields import FIELDS
        field=FIELDS.get(getattr(self,'field_id','workshop'))
        return field.camera if field is not None and field.camera else None

    def program_eye(self):
        """The field camera that a program's looks take their pictures with, or None."""
        from little_world.perception.eye import Eye,sizes_in
        from little_world.perception.sensors import SENSORS
        camera=self.field_camera()
        if camera is None:return None
        return Eye(self.backend,'field/'+camera[0],SENSORS[camera[1]],sizes_in(self._scene()))

    def doorway_program(self):
        """Line up 0.7 m before the Doorway field's door, drive through it and park in the
        bay beyond: three stops for the base's axle midpoint (ADR 0020)."""
        from little_world.fields import BAY, DOOR_Y, WALL_X
        if getattr(self,'base_pose',None) is None:raise ValueError('The Doorway program needs a left and a right drive wheel')
        (x0,y0),(x1,y1)=BAY
        stops=((WALL_X-.7,DOOR_Y,0.),(WALL_X+.6,DOOR_Y,0.),((x0+x1)/2,(y0+y1)/2,0.))
        self.program_edit(Program(tuple(Block('goto',value=.02,duration=40.,point=p) for p in stops)))
        self.status='Doorway: line up before the door, drive through, park in the bay. Run it: the field judges it.'

    FIELD_TASKS={'pick_place':'Pick and place','fetch':'Fetch program','doorway':'Doorway program'}

    def field_task_ready(self,field):
        """Whether this machine can use the chosen field's program template."""
        if field in ('fetch','pick_place'):return self.tool_motion is not None
        return field=='doorway' and getattr(self,'base_pose',None) is not None

    def field_program(self):
        """The template for the chosen field's task."""
        task={'pick_place':self.pick_place_program,'fetch':self.fetch_program,
              'doorway':self.doorway_program}.get(getattr(self,'field_id',None))
        if task is None:raise ValueError('Choose the Pick and place, Fetch or Doorway field: their goals have a program template')
        task()

    def goto_form(self,index=None):
        """A goto step: drive the base's axle midpoint to a point, then turn to a heading."""
        old=self.program.blocks[index] if index is not None else None
        base=getattr(self,'base_pose',None)
        if old is None and base is None:raise ValueError('Driving to a point needs a left and a right drive wheel')
        if old:x,y,*heading=old.point
        else:
            x,y,yaw=base.degrees();heading=[yaw]
        def apply(values):
            nx,ny=(numbers(v,1)[0] for v in values[:2])
            point=(nx,ny) if not values[2].strip() else (nx,ny,numbers(values[2],1)[0])
            b=Block('goto',value=numbers(values[3],1)[0],duration=numbers(values[4],1)[0],point=point)
            if old is not None:b=replace(b,target=old.target,secondary=old.secondary)   # a stop at an object stays one (ADR 0035)
            blocks=list(self.program.blocks)
            if index is None:blocks.append(b)
            else:blocks[index]=b
            self.program_edit(replace(self.program,blocks=tuple(blocks)))
            self.program_selected=len(blocks)-1 if index is None else index
        self.form('Block / drive to a point',[('x (metres, field frame: ahead of the start)',f'{x:.3f}'),
                                             ('y (metres, left of the start)',f'{y:.3f}'),
                                             ('Heading at the end (degrees; blank: any)',f'{heading[0]:.1f}' if heading else ''),
                                             ('Arrive within (metres)',str(old.value if old and old.value else .01)),
                                             ('Timeout (seconds)',str(old.duration if old else 30))],apply,
                  'Ideal position sensing. Starts from where the base is now: drive there first to use it as a waypoint.',text_input=True)

    def pose_form(self,index=None):
        """A pose step: the arm's joint targets now, or an existing pose's speed and settle time."""
        old=self.program.blocks[index] if index is not None else None
        if old is None and self.tool_motion is None:raise ValueError(self.tool_reason or 'Poses need an arm with a tool')
        def apply(values):
            speed,settle=(numbers(v,1)[0] for v in values)
            b=Block('pose',value=speed,duration=settle,angles=old.angles if old else self.tool_motion.teach())
            blocks=list(self.program.blocks)
            if index is None:blocks.append(b)
            else:blocks[index]=b
            self.program_edit(replace(self.program,blocks=tuple(blocks)))
            self.program_selected=len(blocks)-1 if index is None else index
        self.form('Block / pose',[('Speed of the fastest joint (degrees / second)',str(old.value if old else 30)),
                                  ('Settle time after the move (seconds)',str(old.duration if old else 2))],apply,
                  'Keeps its taught angles.' if old else 'Teaches the arm\'s current joint targets: jog there first.')

    def grasp_form(self,index=None):
        old=self.program.blocks[index] if index is not None else None
        def apply(values):
            target=values[0].strip()
            b=Block('grasp',target,duration=numbers(values[1],1)[0])
            blocks=list(self.program.blocks)
            if index is None:blocks.append(b)
            else:blocks[index]=b
            self.program_edit(replace(self.program,blocks=tuple(blocks)))
        self.form('Block / grasp check',[('Object to hold (blank: anything)',old.target if old else ''),
                                         ('Timeout (seconds)',str(old.duration if old else 1))],apply,
                  'Fails the program if the jaws hold nothing: a missed grasp stops, it is not carried on.',text_input=True)

    def block_form(self,index=None):
        old=self.program.blocks[index] if index is not None else None
        def kind_selected(kind):
            if kind in ('contact','distance','if_contact'):
                self.sensor_block_form(kind,index);return
            if kind=='pose':
                self.pose_form(index);return
            if kind=='grasp':
                self.grasp_form(index);return
            if kind=='goto':
                self.goto_form(index);return
            if kind=='look':
                self.look_form(index);return
            def target_selected(target=''):
                if kind=='action':fields=[('Direction: 1 increase / -1 decrease',str(old.value if old else 1)),('Duration (seconds)',str(old.duration if old else 1))]
                elif kind=='drive':fields=[('Left wheel target (rad/s)',str(old.value if old else 3)),('Right wheel target (rad/s)',str(old.secondary if old else 3)),('Duration (seconds)',str(old.duration if old else 1))]
                elif kind=='move':fields=[('Target (degrees; Panda grip: % closed)',str(old.value if old else 20)),('Timeout (seconds)',str(old.duration if old else 5))]
                else:fields=[('Duration (seconds)',str(old.duration if old else 1))]
                def apply(values):
                    nums=[numbers(v,1)[0] for v in values]
                    b=Block(kind,target,nums[0] if kind!='wait' else 0,nums[-1],secondary=nums[1] if kind=='drive' else 0)
                    blocks=list(self.program.blocks)
                    if index is None:blocks.append(b)
                    else:blocks[index]=b
                    self.program_edit(replace(self.program,blocks=tuple(blocks)))
                    self.program_selected=len(blocks)-1 if index is None else index
                self.form('Block / '+kind,fields,apply,'Wheel targets: rad/s. Joints: degrees. Panda gripper: 0-100% closed.')
            if kind in ('action','move'):
                labels={c.label+' ['+c.id+']':c.id for c in self.editor.blueprint.controllers if c.kind=='keyboard_position'}
                if not labels:raise ValueError('Bind a joint in Keyboard first')
                self.choose('Choose joint action',tuple(labels),lambda label:target_selected(labels[label]))
            else:target_selected()
        if old:kind_selected(old.kind)
        else:self.choose('Add program block',('pose','grasp','goto','look','action','drive','wait','move','contact','distance','if_contact'),kind_selected)

    def look_form(self,index=None):
        """A look: the field's camera finds a loose object, and the poses at this stop aimed
        near where it was planned aim where it was seen (ADR 0032)."""
        old=self.program.blocks[index] if index is not None else None
        if self.field_camera() is None:raise ValueError('This field has no camera to look with: the Fetch table has one')
        names=tuple(n for n in self.observations.indices if n.startswith('objects/'))
        if not names:raise ValueError('Nothing loose in this field to look for')
        def chosen(name):
            def apply(values):
                watch,timeout=(numbers(v,1)[0] for v in values)
                here=tuple(float(v) for v in self.data.xpos[self.model.body(name).id])
                b=Block('look',name,watch,timeout,secondary=old.secondary if old else 0.,
                        point=old.point if old and old.target==name else here)
                blocks=list(self.program.blocks)
                if index is None:blocks.append(b)
                else:blocks[index]=b
                self.program_edit(replace(self.program,blocks=tuple(blocks)))
                self.program_selected=len(blocks)-1 if index is None else index
            self.form('Block / look',[('Watch (seconds)',str(old.value if old else 1)),('Timeout (seconds)',str(old.duration if old else 5))],apply,
                      'The table camera watches until three pictures agree; poses aimed near the object then aim where it was seen.')
        if old:chosen(old.target)
        else:self.choose('Object to look for',names,chosen)

    def sensor_block_form(self,kind,index=None):
        names=tuple(self.observations.indices)
        def first(a):
            def second(b):
                fields=[('Timeout (seconds)','5')]
                if kind=='distance':fields.insert(0,('Body-centre distance threshold (metres)','0.1'))
                def apply(values):
                    threshold=numbers(values[0],1)[0] if kind=='distance' else 0
                    block=Block(kind,a,threshold,numbers(values[-1],1)[0],b)
                    blocks=list(self.program.blocks)
                    if index is None:blocks.append(block)
                    else:blocks[index]=block
                    self.program_edit(replace(self.program,blocks=tuple(blocks)))
                self.form('Sensor / '+kind,fields,apply,
                    'Ideal observation. If contact: run next block; otherwise skip it.' if kind=='if_contact' else 'Wait until true; a timeout pauses with an explicit failure.')
            self.choose('Second sensor body',tuple(n for n in names if n!=a),second)
        self.choose('First sensor body',names,first)

    def move_block(self,index,new):
        blocks=list(self.program.blocks)
        if 0<=index<len(blocks) and 0<=new<len(blocks):
            blocks.insert(new,blocks.pop(index));self.program_edit(replace(self.program,blocks=tuple(blocks)));self.program_selected=new

    def start_program(self,single=False):
        if self.runner.state=='running':return
        if self.runner.state=='paused':
            self.runner.single=single;self.runner.state='running';self.runner.message='Running';self.paused=False;return
        names=tuple(self.model.body(i).name for i in range(1,self.model.nbody))
        self.program.validate(self.editor.blueprint,names)
        if not self.program.blocks:raise ValueError('Add blocks or load the Pickup template')
        self.close_bench()
        if self.building:self.simulate()
        self.clear_keys();self.paused=False;self.runner.start(self.program,single)
        self.eye=self.program_eye() if any(b.kind=='look' for b in self.program.blocks) else None

    def stop_program(self):
        self.runner.stop();self.program_keys.clear();self.program_drive=None;self.clear_keys();self.paused=False

    def look_again(self):
        """Tell the running program its reach is going wrong: at a stop where it looked, it opens
        its jaws, rises, goes back and looks again, as its own recovery does (ADR 0052)."""
        if not self.runner.alarm('You asked it to look again'):
            raise ValueError('It looks again only at a stop where it looked, once a run')
        self.status='Looking again: it opens its jaws, rises, goes back to its stop and looks.'

    def pause_program(self):
        if self.runner.state=='running':self.runner.state='paused';self.runner.message='Paused';self.paused=True;self.clear_keys()
        elif self.runner.state=='paused':self.start_program()

    def tick_program(self):
        from little_world.programming.execution import apply,base_targets,held_now,joint_angles
        self.program_keys.clear();self.program_drive=None
        if self.runner.state!='running':return
        contacts,distances=self.observations.program_inputs(self.program)
        base=getattr(self,'base_pose',None)
        motion=getattr(self,'tool_motion',None)
        # The program feels its grasps from its jaw servos' registers (ADR 0048).
        from little_world.control.feel import read
        felt=read(self.backend,self.joint_control,motion.jaws) if motion is not None else None
        held=held_now(self.program,self.observations,felt)
        result=self.runner.tick(self.world.timestep,joint_angles(self.joint_control),contacts,distances,held,
                                base.pose() if base is not None else None,motion.aim if motion is not None else None,
                                getattr(self,'eye',None))
        self.program_drive=base_targets(result,base) if result['base'] else result['drive']
        self.program_keys|=apply(result,self.joint_control)
        if self.runner.state in ('paused','failed'):self.paused=True
        if self.runner.state in ('paused','failed','completed'):self.status='Program: '+self.runner.message

    def draw_look_frame(self,ui,text,wh):
        """The table camera's last depth picture - the region round where the object was
        planned - in the corner of the view, the object's pixels green (ADR 0032)."""
        self.look_rect=None
        picture=getattr(getattr(self,'eye',None),'last',None)
        if picture is None or not picture.depth.size or self.building:return
        rows,cols=picture.depth.shape
        scale=min(220/cols,220/rows);w,h=cols*scale,rows*scale
        x,top=self.PANEL+14,wh-74-h
        ui.pixels('look',picture.colours(),x,top,w,h,version=self.eye.pictures)
        self.look_rect=(x,74,w,h)
        for rx,ry,rw,rh in ((x-2,top-2,w+4,2),(x-2,top+h,w+4,2),(x-2,top,2,h),(x+w,top,2,h)):ui.rect(rx,ry,rw,rh,(.37,.83,.69))
        ui.rect(x-2,top-38,max(w+4,220),36,(.045,.065,.085,.9))
        text('TABLE CAMERA / DEPTH',x+6,top-34,10,(.68,.82,.84))
        seen=self.runner.seen[-1] if self.runner.seen else None
        line=(f'{seen[0].split("/")[-1]} seen {100*sum((a-c)**2 for a,c in zip(seen[2][:2],seen[1][:2]))**.5:.1f} cm from the plan'
              if seen else 'near warm, far cool, the part green')
        text(line,x+6,top-19,10,(.6,.74,.77),max(w,212)-8)

    def program_mouse(self,x,y,action):
        if self.panel_mode!='program' or not self.control_panel or self.dialog is not None:return False
        if action==glfw.RELEASE and self.program_drag is not None:
            index=self.program_drag;self.program_drag=None
            target=next((i for i,rx,ry,rw,rh in self.program_rows if rx<=x<=rx+rw and ry<=y<=ry+rh),None)
            if target is not None and target!=index:self.events.append(lambda:self.move_block(index,target))
            return True
        if self.runner.state in ('running','paused'):return False
        if action==glfw.PRESS:
            for i,rx,ry,rw,rh in self.program_rows:
                if rx<=x<=rx+rw and ry<=y<=ry+rh:self.program_selected=i;self.program_drag=i;return True
        return False

    def draw_program(self,ui,button,text,ww,wh):
        x=ww-338;editing=self.runner.state not in ('running','paused')
        text('PROGRAM',x+16,153,16)
        button('Settings',x+224,149,86,self.program_options,editing,h=26)
        text(f'{self.runner.message} / repeat {min(self.runner.cycle+1,self.program.repeat)} of {self.program.repeat} / {self.program.trigger}',x+16,183,11,(.6,.74,.77),294)
        button('Run',x+16,207,110,self.start_program,self.runner.state!='running' and bool(self.program.blocks),h=36,tone='primary')
        button('Pause',x+134,207,84,self.pause_program,self.runner.state in ('running','paused'),h=36)
        button('Stop',x+226,207,84,self.stop_program,self.runner.state in ('running','paused'),h=36,tone='danger')
        text('SEQUENCE  /  drag steps to reorder',x+16,258,11,(.6,.74,.77))
        rows=max(2,int((wh-520)/43));self.program_rows=[]
        if self.runner.state in ('running','paused') and not self.program_offset<=self.runner.index<self.program_offset+rows:
            self.program_offset=self.runner.index
        self.program_offset=min(self.program_offset,max(0,len(self.program.blocks)-rows))
        labels={s.id:s.label for s in self.editor.blueprint.controllers}
        for row,b in enumerate(self.program.blocks[self.program_offset:self.program_offset+rows]):
            i=self.program_offset+row;y=282+row*43
            names={'wait':'Wait','action':'Joint action','drive':'Drive','move':'Move to angle','contact':'Wait for contact','distance':'Wait for distance','if_contact':'If contact',
                   'pose':'Move to pose','grasp':'Check grasp','goto':'Drive to','look':'Look for'}
            label=f'{i+1}. '+names[b.kind]+(' / '+labels.get(b.target,b.target.split('/')[-1]) if b.target else '')
            active=self.runner.index==i and self.runner.state in ('running','paused')
            button(label,x+16,y,294,lambda i=i:setattr(self,'program_selected',i),active=active or (editing and self.program_selected==i),h=26)
            detail=f'{b.duration:g}s'
            if b.kind=='action':detail=('Increase / close' if b.value>0 else 'Decrease / open')+f' for {b.duration:g}s'
            elif b.kind=='drive':detail=f'L {b.value:g} / R {b.secondary:g} rad/s for {b.duration:g}s'
            elif b.kind=='move':detail=f'{b.value:g} degrees / timeout {b.duration:g}s'
            elif b.kind=='distance':detail=f'Within {b.value:g} m / timeout {b.duration:g}s'
            elif b.kind=='contact':detail=f'Touch {b.other.split(chr(47))[-1]} / {b.duration:g}s'
            elif b.kind=='if_contact':detail='True: next block / false: skip next'
            elif b.kind=='pose':
                detail=f'{len(b.angles)} joints together / up to {b.value:g} deg/s'
                # Aimed: where the tool got to is checked and the pose solved again (ADR 0025).
                if b.point:detail=f'{len(b.angles)} joints / {b.value:g} deg/s / aimed at a point {100*b.point[2]:.0f} cm up'
            elif b.kind=='grasp':detail=f'Holding {b.target.split(chr(47))[-1] if b.target else "anything"} / timeout {b.duration:g}s'
            elif b.kind=='goto':
                detail=f'x {b.point[0]:.2f}  y {b.point[1]:.2f} m'+(f'  /  {round(b.point[2]):d} deg' if len(b.point)>2 else '')+f'  /  within {100*(b.value or .01):.0f} cm'
                # A stop at an object goes where the camera saw it (ADR 0035).
                if b.target:detail=f'Stop at the {b.target.split(chr(47))[-1]}, where it is seen'+(f' / {100*b.secondary:.1f} cm nearer at most' if b.secondary else '')
            elif b.kind=='look':
                seen=next((s for t,p,s in reversed(self.runner.seen) if p==b.point),None)
                detail=(f'Seen {100*sum((a-c)**2 for a,c in zip(seen[:2],b.point[:2]))**.5:.1f} cm from the plan' if seen else
                        f'Table camera / watches {b.value:g}s / timeout {b.duration:g}s'+(f' / {100*b.secondary:.0f} cm round' if b.secondary else ''))
            text(detail,x+24,y+28,10,(.6,.74,.77),276)
            self.program_rows.append((i,x+16,y,294,38))
        if not self.program.blocks:text('Add blocks or load an example.',x+16,286,12,(.6,.74,.77),294)
        y=wh-220
        button('<',x+16,y,35,lambda:setattr(self,'program_offset',max(0,self.program_offset-rows)),h=26)
        button('>',x+56,y,35,lambda:setattr(self,'program_offset',self.program_offset+rows),h=26)
        button('Undo',x+105,y,63,self.program_undo,editing and bool(self.program_past),h=26)
        button('Redo',x+174,y,63,self.program_redo,editing and bool(self.program_future),h=26)
        button('Load',x+243,y,67,self.load_program,editing and self.program_path.exists(),h=26)
        y+=34
        button('Add',x+16,y,63,self.block_form,editing,h=28,tone='primary')
        button('Edit',x+85,y,63,lambda:self.block_form(self.program_selected),editing and bool(self.program.blocks),h=28)
        button('Delete',x+154,y,70,lambda:self.program_edit(replace(self.program,blocks=tuple(b for i,b in enumerate(self.program.blocks) if i!=self.program_selected))),editing and bool(self.program.blocks),h=28)
        button('Save',x+230,y,80,self.save_program,h=28)
        y+=36
        if getattr(self,'factory_mode',False):
            button('Joint motion example',x+16,y,294,self.joint_example,editing,h=28)
        else:
            button('Pickup template',x+16,y,143,self.pickup_program,editing,h=28)
            field=getattr(self,'field_id',None)
            button(self.FIELD_TASKS.get(field,'Field task'),x+167,y,143,self.field_program,
                   editing and self.field_task_ready(field),h=28)
        button('Step',x+16,wh-110,143,lambda:self.start_program(True),self.runner.state!='running' and bool(self.program.blocks),h=28)
        # Something outside the program says its reach is going wrong - you: it looks again (ADR 0052, 0055).
        button('Look again',x+167,wh-110,143,self.look_again,self.runner.listening(),h=28)
        if not self.building and self.runner.state!='stopped':
            # What the program has to go on, as it runs (ADR 0055).
            for i,line in enumerate(self.senses()):text(line,x+16,wh-76+14*i,10,(.6,.74,.77),294)
        else:text('Drag blocks to reorder. Space stops program.',x+16,wh-65,10,(.6,.74,.77),294)

    def senses(self):
        """What a running program has to go on, said plainly, as two lines: its camera - what it
        last saw where it looked (ADR 0032), or what is wrong with its pictures (ADR 0038) - and
        what its jaw servos' registers say (ADR 0048)."""
        from little_world.control.feel import CURRENT_UNIT,holding,read
        from little_world.programming.program import TROUBLE
        seen=self.runner.seen[-1] if self.runner.seen else None
        faults=getattr(self.runner,'faults',())
        if getattr(self,'eye',None) is None:sees='Camera: this program does not look'
        elif faults:sees='Camera: '+TROUBLE[faults[-1]].replace("the camera's",'its')
        elif seen is None:sees='Camera: it has not looked yet'
        else:
            off=100*sum((a-c)**2 for a,c in zip(seen[2][:2],seen[1][:2]))**.5
            sees=f'Camera: saw the {seen[0].split("/")[-1]} {off:.1f} cm from the plan'
        motion=getattr(self,'tool_motion',None)
        jaws=read(self.backend,self.joint_control,motion.jaws) if motion is not None else None
        if jaws is None:feels='Jaws: no servos to read'
        elif holding(jaws):feels=f'Jaws: holding - stopped on it, pushing ({1000*CURRENT_UNIT*min(j.current for j in jaws):.0f} mA)'
        elif any(j.moving for j in jaws):feels='Jaws: moving'
        else:feels='Jaws: nothing between them'
        return sees,feels
