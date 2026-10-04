"""Portable named tool positions; independent of physics and presentation."""
from dataclasses import dataclass, replace
import json
import math

@dataclass(frozen=True)
class TaughtPosition:
    name: str
    point: tuple[float,float,float]

    def __post_init__(self):
        if not isinstance(self.name,str) or not self.name.strip() or len(self.name)>64:
            raise ValueError('Use a position name of 1–64 characters.')
        if len(self.point)!=3 or any(not isinstance(v,(float,int)) or not math.isfinite(v) for v in self.point):
            raise ValueError('Position needs three finite coordinates in metres.')
        object.__setattr__(self,'name',self.name.strip())
        object.__setattr__(self,'point',tuple(float(v) for v in self.point))

@dataclass(frozen=True)
class TeachingBook:
    positions: tuple[TaughtPosition,...]=()

    def saved(self,position):
        return replace(self,positions=tuple(p for p in self.positions if p.name!=position.name)+(position,))

    def removed(self,name):
        return replace(self,positions=tuple(p for p in self.positions if p.name!=name))

    def to_json(self):
        return json.dumps(dict(version=1,robot='franka_panda',orientation='downward',positions=[dict(name=p.name,point=p.point) for p in self.positions]),indent=2)

    @classmethod
    def from_json(cls,text):
        data=json.loads(text)
        if data.get('version')!=1 or data.get('robot')!='franka_panda' or data.get('orientation')!='downward':
            raise ValueError('Unsupported teaching file.')
        book=cls()
        for p in data['positions']:book=book.saved(TaughtPosition(p['name'],p['point']))
        return book
