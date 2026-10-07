"""Precise, reviewable factory changes over the existing direct-manipulation UI."""
from pathlib import Path
import glfw
from little_world.factory.changes import CellChange,CellRequest,preview_changes
from little_world.factory.recipe import TRAYS,PRODUCT_NAMES
from .inspector import numbers

class CellChanges:
    def init_cell_changes(self):
        self.recipe_revision=0
        self.recipe_future=[]
        self.cell_proposal=None

    def change_request(self,changes=()):
        return CellRequest(self.recipe,self.recipe_revision,tuple(changes))

    def review_cell_request(self,request):
        if not self.building or self.guided:raise ValueError('Reset the cell and leave the guide before reviewing changes.')
        proposal=preview_changes(self.recipe,self.recipe_revision,request)
        self.cell_proposal=proposal
        self.clear_keys();self.tray_drag=None;self.pending_source=None
        self.dialog=dict(cell_review=True,error='')

    def open_cell_changes(self):
        def selected(action):
            if action=='Move a tray precisely':
                def tray(name):
                    point=self.recipe.point(name)
                    request=self.change_request()
                    self.form('Move '+name+' tray',[('World X, Y (metres)',f'{point[0]}, {point[1]}')],
                        lambda v:self.review_cell_request(CellRequest(request.base,request.revision,(CellChange('tray',name,numbers(v[0],2)),))),
                        'Next: review exact changes. Nothing moves yet.')
                self.choose('Choose tray ID',TRAYS,tray)
            elif action=='Change product':
                request=self.change_request()
                self.choose('Choose product',PRODUCT_NAMES,lambda name:self.review_cell_request(CellRequest(request.base,request.revision,(CellChange('product','product',name),))))
            elif action=='Change route':
                request=self.change_request()
                self.form('Change source and destination', [('Source tray ID',self.recipe.source),('Destination tray ID',self.recipe.destination)],
                    lambda v:self.review_cell_request(CellRequest(request.base,request.revision,(CellChange('task','route',tuple(x.strip() for x in v)),))),
                    'Tray IDs: input, Blue, Amber. Next: review.',text_input=True)
            elif action=='Import JSON proposal':
                self.form('Review proposal from code',[('JSON file path',str(self.recipe_path.with_name(f'factory-change-r{self.recipe_revision}.json')))],
                    lambda v:self.review_cell_request(CellRequest.from_json(Path(v[0]).expanduser().read_text())),
                    'Data only. Must match the current cell and revision.',text_input=True)
            elif action=='Export JSON draft':
                self.form('Export current cell for code',[('New JSON file path',str(self.recipe_path.with_name(f'factory-change-r{self.recipe_revision}.json')))],
                    lambda v:self.export_cell_request(Path(v[0]).expanduser()),
                    'Existing files are preserved. Edit changes, then Import.',text_input=True)
            elif action=='Redo cell edit':self.redo_recipe()
        self.choose('Cell changes / revision '+str(self.recipe_revision),
            ('Move a tray precisely','Change product','Change route','Import JSON proposal','Export JSON draft')+
            (('Redo cell edit',) if self.recipe_future else ()),selected)

    def export_cell_request(self,path):
        # Include editable operations with current values, so the draft is a no-op.
        changes=[CellChange('tray',name,self.recipe.point(name)) for name in TRAYS]
        changes.extend((CellChange('task','route',(self.recipe.source,self.recipe.destination)),CellChange('product','product',self.recipe.product)))
        request=self.change_request(changes)
        with path.open('x') as file:file.write(request.to_json())
        self.authoring_note='Draft exported at revision '+str(self.recipe_revision)+'. Edit it, then import for review.'

    def apply_cell_proposal(self):
        try:
            if self.cell_proposal is None:raise ValueError('No proposal to apply.')
            recipe=self.cell_proposal.apply(self.recipe,self.recipe_revision)
            self.apply_recipe(recipe)
        except (ValueError,TypeError,KeyError,OSError) as error:
            self.dialog['error']=str(error);return
        self.cell_proposal=None;self.dialog=None
        self.authoring_note='Reviewed changes applied. Undo restores the entire previous cell.'

    def dismiss_cell_proposal(self):
        self.cell_proposal=None;self.dialog=None

    def dialog_key(self,key,action,mods):
        if self.dialog is not None and self.dialog.get('cell_review'):
            if action==glfw.PRESS and key==glfw.KEY_ESCAPE:self.dismiss_cell_proposal()
            return
        super().dialog_key(key,action,mods)

    def character(self,*args):
        if self.dialog is not None and self.dialog.get('cell_review'):return
        super().character(*args)

    def draw_dialog(self,ui,button,text,ww,wh):
        if self.dialog is None or not self.dialog.get('cell_review'):
            return super().draw_dialog(ui,button,text,ww,wh)
        import textwrap
        p=self.cell_proposal
        fresh=p is not None and p.before==self.recipe and p.revision==self.recipe_revision
        self.buttons=[];ui.begin();ui.rect(0,0,ww,wh,(.035,.052,.065,.88))
        width=min(720,ww-80);x=(ww-width)/2;y=80
        ui.rect(x,y,width,wh-160,(.085,.12,.15))
        text('Review cell changes',x+24,y+22,21)
        text('Revision '+str(p.revision)+' / exact world coordinates in metres',x+24,y+60,12,(.65,.78,.8))
        text('NOT APPLIED',x+24,y+90,12,(1.,.8,.4))
        for i,line in enumerate(p.summary or ('No values changed.',)):
            text(line,x+24,y+125+i*30,13,max_width=width-48)
        top=y+300
        text('Checked: table bounds, tray spacing, fixed obstructions.',x+24,top,12,(.4,.85,.7),width-48)
        for i,line in enumerate(textwrap.wrap('Not checked: robot reach, motion-path collisions, grasp success or throughput. Run Preview path and the physical cycle after applying.',80)):
            text(line,x+24,top+28+i*20,12,(.85,.75,.55),width-48)
        message=self.dialog['error'] or ('' if fresh else 'Cell changed. Dismiss and prepare a fresh proposal.')
        for i,line in enumerate(textwrap.wrap(message,80)):
            text(line,x+24,wh-218+i*18,12,(1.,.55,.4),width-48)
        button('Dismiss',x+24,wh-140,130,self.dismiss_cell_proposal,h=34)
        button('Apply changes',x+width-194,wh-140,170,self.apply_cell_proposal,
               fresh and bool(p.summary) and self.building and not self.guided,h=34,tone='primary')
