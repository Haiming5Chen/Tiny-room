"""Task starters and contextual attachment suggestions."""
from little_world.construction.guidance import build_checks,suggestions,add_suggested


class GuidedBuild:
    def show_guide(self):
        self.close_bench();self.active_tab='Guide'

    def starter_kit(self,label):
        from little_world.robots.arm_lab import arm_lab_blueprint
        from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
        from little_world.robots.mobile_platform import mobile_platform_blueprint
        factory={'Tabletop pickup':arm_lab_blueprint,'Mobile pickup':mobile_manipulator_blueprint,'Driving cart':mobile_platform_blueprint}[label]
        self.edit(lambda:self.editor.load(factory()))
        self.stop_program();self.program_edit(type(self.program)())
        self.camera.lookat[:]=(.2,0,.2);self.camera.distance=1.4
        self.status='Kit loaded. Review controls, then open Program or Test.'

    def choose_arm_family(self):
        from little_world.robots.arm_family import FAMILIES,arm_family_blueprint
        def selected(name):
            self.edit(lambda:self.editor.load(arm_family_blueprint(name)))
            self.stop_program();self.program_edit(type(self.program)())
            self.camera.lookat[:]=(.2,0,.15);self.camera.distance=1.4
        self.choose('Matched arm family / approximate',tuple(FAMILIES),selected)

    def draw_guide(self,ui,button,text,section,ww,wh):
        # The first hour's lessons first (ADR 0046); the starter kits and checks a click away.
        view=getattr(self,'guide_view','Lessons')
        if view=='New':
            self.draw_whats_new(ui,button,text,section,ww,wh);return
        if view=='Lessons':
            self.draw_lessons(ui,button,text,section,ww,wh);return
        section('WHAT DO YOU WANT TO BUILD?',122)
        for i,name in enumerate(('Tabletop pickup','Mobile pickup','Driving cart')):
            button(name,12,154+i*42,264,lambda n=name:self.starter_kit(n),self.building,h=34)
        button('Matched arm families',12,282,264,self.choose_arm_family,self.building,h=28)
        section('SUGGESTED NEXT CONNECTION',322)
        selected=self.editor.selected
        text(selected.id if selected else 'Select a target part',16,346,12,(.6,.74,.77),254)
        if not suggestions(self.editor):
            text('Mount occupied or no matching suggestion.',16,382,11,(.6,.74,.77),254)
            text('Select a free deck, tool or output frame.',16,404,11,(.6,.74,.77),254)
        for i,(item,description) in enumerate(suggestions(self.editor)[:2]):
            button(description,12,374+i*42,264,lambda k=item:self.edit(lambda:add_suggested(self.editor,k)),self.building,h=34)
        section('BUILD CHECKS',476)
        y=503
        import textwrap
        for message in build_checks(self.editor.blueprint):
            for line in textwrap.wrap(message,37):
                text(line,16,y,11,(.7,.78,.8),254);y+=17
            y+=8
        button('Lessons: the first hour',12,wh-118,264,lambda:setattr(self,'guide_view','Lessons'),h=30)
        button("What's new: watch it work",12,wh-158,264,lambda:setattr(self,'guide_view','New'),h=30)
        button('Search all parts',12,wh-78,264,lambda:(self.open_bench(),self.bench_search()),self.building)
