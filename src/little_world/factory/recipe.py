"""Portable factory layout/task data, independent of native physics and UI."""
from dataclasses import dataclass,replace
import json
from math import isfinite,hypot

TRAYS=('input','Blue','Amber')
PRODUCT_NAMES=('Small block','Tall block')

@dataclass(frozen=True)
class CellRecipe:
    positions:tuple=((.45,0.),(.44,-.24),(.44,.24))
    source:str='input'
    destination:str='Blue'
    product:str='Small block'

    def __post_init__(self):
        positions=tuple(tuple(float(v) for v in p) for p in self.positions)
        if len(positions)!=3 or any(len(p)!=2 or not all(isfinite(v) for v in p) for p in positions):raise ValueError('A cell needs three finite tray positions.')
        object.__setattr__(self,'positions',positions)
        if self.source not in TRAYS or self.destination not in TRAYS or self.source==self.destination:raise ValueError('Choose different source and destination trays.')
        if self.product not in PRODUCT_NAMES:raise ValueError('Unknown product.')
        for x,y in positions:
            if not (-.25<=x<=.75 and -.44<=y<=.44):raise ValueError('Keep the entire tray on the worktable.')
            if hypot(x,y)<.25:raise ValueError('Leave space around the robot base.')
            for py in (-.43,.43):
                if abs(x-.72)<.125 and abs(y-py)<.115:raise ValueError('The tray overlaps a camera support.')
        for i,(x,y) in enumerate(positions):
            for a,b in positions[i+1:]:
                if abs(x-a)<.215 and abs(y-b)<.195:raise ValueError('The trays overlap; leave a small gap.')

    def point(self,name):return self.positions[TRAYS.index(name)]
    def moved(self,name,point):
        positions=list(self.positions);positions[TRAYS.index(name)]=tuple(point)
        return replace(self,positions=tuple(positions))
    def to_json(self):
        return json.dumps(dict(version=1,positions=self.positions,source=self.source,destination=self.destination,product=self.product),indent=2)
    @classmethod
    def from_json(cls,text):
        data=json.loads(text)
        if not isinstance(data,dict) or data.pop('version',None)!=1:raise ValueError('Unsupported factory recipe version.')
        if set(data)!={'positions','source','destination','product'}:raise ValueError('Invalid factory recipe fields.')
        return cls(**data)
