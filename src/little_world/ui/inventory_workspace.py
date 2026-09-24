"""Saved drafts, finished designs and side-by-side evidence views."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import textwrap
import mujoco as mj
from little_world.inventory.store import Inventory,fingerprint
from little_world.inventory.analysis import analyze,differences,changed_fields


class InventoryWorkspace:
    def init_inventory(self):
        self.inventory=Inventory(self.path.parent/'inventory');self.inventory_open=False
        self.inventory_records=[];self.inventory_errors=[];self.inventory_selected=None
        self.inventory_filter='all';self.inventory_query='';self.inventory_offset=0;self.inventory_tab='Overview'
        self.inventory_previews={};self.inventory_analysis={};self.inventory_scroll=0
        from little_world.inventory.benchmark import environment_fingerprint
        self.trial_environment=environment_fingerprint()
        self.comparison=None;self.comparison_future=None;self.comparison_executor=None;self.comparison_status='No comparison trial run yet.'

    def show_inventory(self):
        if not self.building:
            if self.runner.state=='running':self.pause_program()
            else:self.paused=True;self.clear_keys()
        self.inventory_open=True;self.refresh_inventory()
        if not self.comparison_future:self.select_inventory(self.inventory_selected)

    def refresh_inventory(self):
        self.inventory_records,self.inventory_errors=self.inventory.list()
        if self.inventory_selected not in {r.id for r in self.inventory_records}:
            self.inventory_selected=self.inventory_records[0].id if self.inventory_records else None

    def selected_design(self):return next((r for r in self.inventory_records if r.id==self.inventory_selected),None)

    def save_inventory_form(self):
        def apply(values):
            r=self.inventory.save(values[0],values[1].lower().strip(),values[2],self.editor.blueprint,self.program)
            self.refresh_inventory();self.inventory_selected=r.id;self.status='Saved independent inventory snapshot: '+r.name
        self.form('Save to inventory',[('Design name','Robot '+datetime.now().strftime('%m-%d %H:%M')),('Status: draft / finished','draft'),('Notes','')],apply,
                  'Each save creates a new version, including its program. Finished is your label.',text_input=True)

    def edit_inventory_metadata(self):
        r=self.selected_design()
        if not r:return
        def apply(values):
            self.inventory.update(r.id,values[0],values[1].strip().lower(),values[2]);self.refresh_inventory()
        self.form('Design details',[('Name',r.name),('Status: draft / finished',r.status),('Notes',r.notes)],apply,text_input=True)

    def checkout_inventory(self):
        if not self.building:raise ValueError('Return to BUILD before loading an inventory design')
        r=self.selected_design()
        if not r:return
        if self.editor.blueprint!=r.blueprint or self.program!=r.program:
            self.inventory.save('Recovery before '+r.name[:45],'draft','Automatically preserved before loading another design.',self.editor.blueprint,self.program)
        self.edit(lambda:self.editor.load(r.blueprint));self.stop_program();self.program_edit(r.program)
        self.inventory_open=False;self.status='Loaded '+r.name+'. Previous workspace preserved in inventory.'

    def select_inventory(self,identifier):
        self.inventory_selected=identifier;self.inventory_scroll=0;self.comparison=None
        r=self.selected_design()
        if r:
            for report in self.inventory.comparisons():
                if report.get('left_hash')==fingerprint(self.editor.blueprint) and report.get('right_hash')==fingerprint(r.blueprint):
                    if report.get('protocol',{}).get('mode')!='program' or report['protocol'].get('program')==fingerprint(self.program):
                        self.comparison=report;break

    def start_comparison(self,mode):
        r=self.selected_design()
        if r is None:raise ValueError('Select a saved design to compare')
        if self.comparison_future:return
        from little_world.inventory.benchmark import compare_trials
        if self.comparison_executor is None:self.comparison_executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='little-world-trial')
        self.comparison_status='Running two isolated trials...';self.comparison=None
        current,previous,program=self.editor.blueprint,r.blueprint,self.program
        def work():
            result=compare_trials(current,previous,program,mode)
            self.inventory.save_comparison(result)
            return result
        self.comparison_future=self.comparison_executor.submit(work)

    def poll_comparison(self):
        if self.comparison_future and self.comparison_future.done():
            future=self.comparison_future;self.comparison_future=None
            try:
                self.comparison=future.result()
                self.comparison_status='Completed and saved. Simulated results, not physical measurements.'
            except Exception as error:self.comparison_status='Trial could not complete: '+str(error)

    def inventory_report(self,bp):
        key=fingerprint(bp)
        if key not in self.inventory_analysis:self.inventory_analysis[key]=analyze(bp)
        return self.inventory_analysis[key]

    def inventory_preview(self,bp,rect,ww,wh,fw,fh):
        key=fingerprint(bp)
        if key not in self.inventory_previews:
            from little_world.physics.mujoco_backend import MujocoBackend
            from little_world.core.scene import Scene
            from little_world.core.entity import Entity
            backend=MujocoBackend();backend.compile(Scene((Entity('design',bp),)),.002)
            model,data=backend.model,backend.data;scene=mj.MjvScene(model,maxgeom=10000);camera=mj.MjvCamera()
            camera.lookat[:]=model.stat.center;camera.distance=max(.2,float(model.stat.extent)*1.35);camera.azimuth=125;camera.elevation=-28
            if len(self.inventory_previews)>=4:
                first=next(iter(self.inventory_previews));self.inventory_previews.pop(first)[0].close()
            if model.nmesh:backend._preview_context=mj.MjrContext(model,150)
            self.inventory_previews[key]=(backend,scene,camera)
        backend,scene,camera=self.inventory_previews[key];option=mj.MjvOption()
        mj.mjv_updateScene(backend.model,backend.data,option,None,camera,mj.mjtCatBit.mjCAT_ALL,scene)
        scene.flags[mj.mjtRndFlag.mjRND_SHADOW]=False
        x,y,w,h=rect;mj.mjr_render(mj.MjrRect(int(x*fw/ww),int((wh-y-h)*fh/wh),int(w*fw/ww),int(h*fh/wh)),scene,backend._preview_context or self.context)

    def draw_inventory(self,ui,button,text,ww,wh,fw,fh):
        self.poll_comparison();ui.begin();self.buttons=[]
        ui.rect(0,0,ww,wh,(.055,.075,.095))
        self.draw_navigation(ui,button,text,ww)
        text('INVENTORY  /  Save versions and compare your designs.',24,67,12,(.61,.72,.77))
        button('Back to workspace',ww-186,61,162,lambda:setattr(self,'inventory_open',False),h=26)
        ui.rect(16,86,274,wh-130,(.08,.11,.14))
        for i,status in enumerate(('all','draft','finished')):
            button(status.title(),24+i*86,102,80,lambda s=status:(setattr(self,'inventory_filter',s),setattr(self,'inventory_offset',0)),active=self.inventory_filter==status,h=26)
        def search():self.form('Search saved designs',[('Name / notes',self.inventory_query)],lambda v:setattr(self,'inventory_query',v[0]),text_input=True)
        button('Search designs',24,143,170,search,h=28)
        button('Refresh',202,143,72,self.refresh_inventory,h=28)
        records=[r for r in self.inventory_records if (self.inventory_filter=='all' or r.status==self.inventory_filter) and self.inventory_query.lower() in (r.name+' '+r.notes).lower()]
        count=max(1,int((wh-305)/54));self.inventory_offset=min(self.inventory_offset,max(0,len(records)-count))
        for i,r in enumerate(records[self.inventory_offset:self.inventory_offset+count]):
            y=192+i*54
            button(r.name,24,y,250,lambda n=r.id:self.select_inventory(n),active=self.inventory_selected==r.id,h=30)
            text(r.status+' / '+r.created[:16].replace('T',' '),32,y+33,10,(.6,.74,.77),234)
        if not records:text('No saved designs. Save your current build.',24,200,11,(.6,.74,.77),250)
        button('<',24,wh-92,40,lambda:setattr(self,'inventory_offset',max(0,self.inventory_offset-count)),h=28)
        text(f'{len(records)} saved versions',76,wh-86,11,(.6,.74,.77))
        button('>',234,wh-92,40,lambda:setattr(self,'inventory_offset',self.inventory_offset+count),h=28)
        r=self.selected_design();x=310;width=ww-x-24;half=(width-16)/2
        text('CURRENT WORKSPACE',x+8,92,13)
        text(r.name if r else 'SELECT A SAVED BUILD',x+half+24,92,13,max_width=half-12)
        button('Load selected',x+half+24,119,130,self.checkout_inventory,self.building and r is not None,h=26)
        button('Name / status / notes',x+half+162,119,max(80,half-154),self.edit_inventory_metadata,r is not None,h=26)
        ui.flush(ww,wh,fw,fh)
        self.inventory_preview(self.editor.blueprint,(x,158,half,184),ww,wh,fw,fh)
        if r:self.inventory_preview(r.blueprint,(x+half+16,158,half,184),ww,wh,fw,fh)
        ui.begin()
        for i,tab in enumerate(('Overview','Parts changes','Performance')):
            button(tab,x+i*145,354,137,lambda t=tab:(setattr(self,'inventory_tab',t),setattr(self,'inventory_scroll',0)),active=self.inventory_tab==tab,h=28)
        left=self.inventory_report(self.editor.blueprint);right=self.inventory_report(r.blueprint) if r else None
        if self.inventory_tab=='Overview':
            text('Delta: current - saved',ww-153,388,10,(.6,.74,.77),130)
            rows=[('Geometry mass (kg)','mass_kg'),('Moving mass (kg)','moving_mass_kg'),('Bodies','parts'),('Motors','motors')]
            for i,(label,key) in enumerate(rows):
                y=402+i*24;text(label,x+8,y,12,(.6,.74,.77));text(f'{left[key]:.3f}' if 'mass' in key else str(left[key]),x+210,y,12)
                if right:
                    text(f'{right[key]:.3f}' if 'mass' in key else str(right[key]),x+half+24,y,12)
                    text(f'{left[key]-right[key]:+.3f}' if 'mass' in key else f'{left[key]-right[key]:+d}',ww-110,y,12)
            for column,report in ((x,left),(x+half+16,right)):
                if report is None:continue
                lines=['Strengths']+['+ '+v for v in report['pros']]+['Limitations']+['- '+v for v in report['cons']]
                wrapped=[line for item in lines for line in textwrap.wrap(item,max(24,int(half/6.2)))]
                for i,line in enumerate(wrapped[self.inventory_scroll:self.inventory_scroll+max(1,int((wh-602)/17))]):text(line,column+8,514+i*17,11,(.7,.79,.8),half-16)
            text('Estimates from parts; no payload guarantee. More analysis:',x+8,wh-70,11,(.6,.74,.77))
            button('<',ww-102,wh-78,34,lambda:setattr(self,'inventory_scroll',max(0,self.inventory_scroll-4)),h=26)
            button('>',ww-62,wh-78,34,lambda:setattr(self,'inventory_scroll',self.inventory_scroll+4),h=26)
        elif self.inventory_tab=='Parts changes':
            lines=[]
            if r:
                for kind,delta in differences(self.editor.blueprint,r.blueprint).items():
                    for change,names in delta.items():
                        lines.append(kind+' / '+change+f': {len(names)}')
                        lines.extend('  '+name for name in names)
                lines.append('Changed values (saved -> current):')
                for detail in changed_fields(self.editor.blueprint,r.blueprint):lines.extend(textwrap.wrap(detail,max(35,int(width/6.5))))
                lines.append('Program: '+('same' if self.program==r.program else 'changed'))
                if r.notes:lines.extend(textwrap.wrap('Saved notes: '+r.notes,90))
            else:lines=['Select a saved design to see additions, removals and edits.']
            for i,line in enumerate(lines[self.inventory_scroll:self.inventory_scroll+max(1,int((wh-480)/20))]):text(line,x+8,401+i*20,12,(.7,.79,.8),width-16)
            button('Previous',x,wh-85,100,lambda:setattr(self,'inventory_scroll',max(0,self.inventory_scroll-8)),h=28)
            button('More',x+108,wh-85,100,lambda:setattr(self,'inventory_scroll',min(max(0,len(lines)-1),self.inventory_scroll+8)),h=28)
        else:self.draw_comparison(button,text,x,ww,wh,r)
        message=self.status if not self.inventory_errors else f'{len(self.inventory_errors)} unreadable inventory file(s); existing valid designs remain available.'
        text(message,24,wh-27,11,(.6,.74,.77),ww-48)
        self.draw_dialog(ui,button,text,ww,wh)

    def draw_comparison(self,button,text,x,ww,wh,record):
        button('Drive / hold trial',x,398,155,lambda:self.start_comparison('hold_drive'),record is not None and self.comparison_future is None,h=30)
        button('Test current program',x+163,398,186,lambda:self.start_comparison('program'),record is not None and self.comparison_future is None,h=30)
        text('Same room, timestep and 5-second horizon. Program references must match both builds.',x+8,440,11,(.6,.74,.77),ww-x-32)
        text(self.comparison_status,x+8,461,11,(.6,.74,.77),ww-x-32)
        report=self.comparison
        if report is None:return
        if record is None or report['left_hash']!=fingerprint(self.editor.blueprint) or report['right_hash']!=fingerprint(record.blueprint) or (report['protocol']['mode']=='program' and report['protocol']['program']!=fingerprint(self.program)):
            text('Result belongs to an earlier design/program. Run a fresh comparison.',x+8,493,12,(1,.7,.4),ww-x-24);return
        if report['protocol'].get('environment')!=self.trial_environment or report['protocol'].get('solver')!=mj.__version__:
            text('Historical result: room or solver changed. Run a fresh comparison.',x+8,493,12,(1,.7,.4),ww-x-24);return
        text('SIMULATED / '+report['protocol']['mode']+' / '+report['created'][:16].replace('T',' '),x+8,491,11)
        text('Current',x+290,501,10,(.6,.74,.77));text('Saved',x+450,501,10,(.6,.74,.77))
        text('Delta',ww-110,501,10,(.6,.74,.77))
        fields=(('Displacement (m)','displacement_m'),('Peak joint error (deg)','peak_joint_error_deg'),('Peak tilt (deg)','peak_tilt_deg'),('Absolute mechanical work (J)','absolute_mechanical_work_J'))
        for i,(label,key) in enumerate(fields):
            y=519+i*25;text(label,x+8,y,12,(.6,.74,.77));text(f'{report["left"][key]:.3f}',x+290,y,12);text(f'{report["right"][key]:.3f}',x+450,y,12);text(f'{report["left"][key]-report["right"][key]:+.3f}',ww-110,y,12)
        text('Program: '+report['left']['program_state']+' / '+report['right']['program_state'],x+8,wh-111,11,(.6,.74,.77),ww-x-24)
        text('Work is not battery consumption. Trial limits do not certify a real build.',x+8,wh-78,11,(.6,.74,.77),ww-x-24)
