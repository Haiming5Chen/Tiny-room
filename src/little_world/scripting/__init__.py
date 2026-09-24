"""Convenient Python authoring over the same immutable editor as the GUI."""
from dataclasses import replace
from little_world.core.component import Body,Geometry,Transform
from little_world.core.blueprint import Blueprint
from little_world.materials import METAL
from little_world.construction.editor import AssemblyEditor
from little_world.construction.docking import dock,wheel_at


class RobotBuilder:
    def __init__(self,blueprint):
        self.editor=AssemblyEditor(blueprint)
        self.base=next(b.id for b in self.editor.bodies if b.parent is None)

    @classmethod
    def chassis(cls,length=.6,width=.28,height=.04):
        return cls(Blueprint((Body('chassis',Geometry('box',(length,width,height)),'metal',Transform((0,0,height/2)),dynamic=True),),(METAL,)))

    @property
    def blueprint(self):return self.editor.blueprint

    def wheel(self,part='drive_100',*,side='Left',x=0.,parent=None,clearance=.005):
        wheel_at(self.editor,part,parent or self.base,side,x,clearance=clearance)
        return self.editor.selection

    def add(self,part,*,parent=None,mount='Top'):
        dock(self.editor,part,parent or self.base,mount)
        return self.editor.selection

    def drive(self,**settings):
        from little_world.core.drive_settings import DriveSettings
        self.editor._commit(replace(self.blueprint,controllers=tuple(replace(c,drive_settings=DriveSettings(**settings)) if c.kind=='differential_torque' else c for c in self.blueprint.controllers)))
        return self
