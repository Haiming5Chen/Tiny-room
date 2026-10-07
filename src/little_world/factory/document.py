"""Portable factory authoring document over existing Blueprint/Entity/Scene data."""
from dataclasses import dataclass,replace,asdict
import json
from math import isfinite
from little_world.core.blueprint import Blueprint,identifier
from little_world.core.component import Transform
from little_world.core.entity import Entity
from little_world.core.scene import Scene


def strict_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate JSON key: '+key)
        result[key]=value
    return result


def fields(value,expected):
    if not isinstance(value,dict) or set(value)!=set(expected):raise ValueError('Invalid document fields; expected '+', '.join(expected))


def pose(value):
    fields(value,('position','quaternion'))
    for name,length in (('position',3),('quaternion',4)):
        vector=value[name]
        if not isinstance(vector,list) or len(vector)!=length:raise ValueError('Invalid '+name)
        if any(type(v) not in (int,float) for v in vector):raise ValueError('Coordinates must be numeric.')
        if not all(isfinite(v) for v in vector):raise ValueError('Coordinates must be finite.')
    return Transform(**value)


@dataclass(frozen=True)
class MachineAsset:
    id:str
    blueprint:Blueprint

    def __post_init__(self):
        identifier(self.id)
        if not isinstance(self.blueprint,Blueprint):raise ValueError('Asset needs a Blueprint.')
        self.blueprint.validate()


@dataclass(frozen=True)
class Station:
    id:str
    asset:str
    label:str
    transform:Transform=Transform()

    def __post_init__(self):
        identifier(self.id);identifier(self.asset)
        if not isinstance(self.label,str) or not self.label.strip() or len(self.label)>80:raise ValueError('Station label needs 1–80 characters.')
        if not isinstance(self.transform,Transform):raise ValueError('Station needs a world Transform.')


@dataclass(frozen=True)
class ProcessLink:
    id:str
    source:str
    destination:str

    def __post_init__(self):
        for value in (self.id,self.source,self.destination):identifier(value)
        if self.source==self.destination:raise ValueError('A process link needs two different stations.')


@dataclass(frozen=True)
class FactoryDocument:
    assets:tuple[MachineAsset,...]=()
    stations:tuple[Station,...]=()
    links:tuple[ProcessLink,...]=()

    def __post_init__(self):
        for name,kind in (('assets',MachineAsset),('stations',Station),('links',ProcessLink)):
            values=tuple(getattr(self,name));object.__setattr__(self,name,values)
            if any(not isinstance(v,kind) for v in values):raise ValueError('Invalid '+name)
            if len({v.id for v in values})!=len(values):raise ValueError('Duplicate '+name+' IDs.')
            object.__setattr__(self,name,tuple(sorted(values,key=lambda v:v.id)))
        assets={a.id for a in self.assets};stations={s.id for s in self.stations}
        if any(s.asset not in assets for s in self.stations):raise ValueError('Station references an unknown asset.')
        if any(l.source not in stations or l.destination not in stations for l in self.links):raise ValueError('Process link references an unknown station.')
        if len({(l.source,l.destination) for l in self.links})!=len(self.links):raise ValueError('Duplicate process connection.')

    def with_asset(self,asset):return replace(self,assets=self._upsert(self.assets,asset))
    def with_station(self,station):return replace(self,stations=self._upsert(self.stations,station))
    def with_link(self,link):return replace(self,links=self._upsert(self.links,link))

    @staticmethod
    def _upsert(values,value):
        return tuple(value if item.id==value.id else item for item in values) if any(item.id==value.id for item in values) else values+(value,)

    def move_station(self,id,transform):
        station=next((s for s in self.stations if s.id==id),None)
        if station is None:raise ValueError('Unknown station: '+id)
        return self.with_station(replace(station,transform=transform))

    def remove_station(self,id,*,remove_links=False):
        if not any(s.id==id for s in self.stations):raise ValueError('Unknown station: '+id)
        linked=tuple(l for l in self.links if id in (l.source,l.destination))
        if linked and not remove_links:raise ValueError('Station has process links; remove them explicitly or use remove_links=True.')
        return replace(self,stations=tuple(s for s in self.stations if s.id!=id),links=tuple(l for l in self.links if l not in linked))

    def remove_asset(self,id):
        if any(s.asset==id for s in self.stations):raise ValueError('Asset is used by a station.')
        if not any(a.id==id for a in self.assets):raise ValueError('Unknown asset: '+id)
        return replace(self,assets=tuple(a for a in self.assets if a.id!=id))

    def remove_link(self,id):
        if not any(l.id==id for l in self.links):raise ValueError('Unknown link: '+id)
        return replace(self,links=tuple(l for l in self.links if l.id!=id))

    def to_scene(self):
        assets={a.id:a.blueprint for a in self.assets}
        return Scene(tuple(Entity(s.id,assets[s.asset],s.transform) for s in self.stations))

    def to_data(self):
        return dict(version=1,units='m',frame='world',assets=[dict(id=a.id,blueprint=json.loads(a.blueprint.to_json())) for a in self.assets],
                    stations=[asdict(s) for s in self.stations],links=[asdict(l) for l in self.links])

    def to_json(self):return json.dumps(self.to_data(),indent=2,allow_nan=False)

    @classmethod
    def from_json(cls,text):
        try:
            data=json.loads(text,object_pairs_hook=strict_object)
            fields(data,('version','units','frame','assets','stations','links'))
            if type(data['version']) is not int or data['version']!=1 or data['units']!='m' or data['frame']!='world':raise ValueError('Expected version 1, metres and world frame.')
            if any(not isinstance(data[key],list) for key in ('assets','stations','links')):raise ValueError('Document collections must be arrays.')
            assets=[];stations=[];links=[]
            for a in data['assets']:
                fields(a,('id','blueprint'));assets.append(MachineAsset(a['id'],Blueprint.from_json(json.dumps(a['blueprint']))))
            for s in data['stations']:
                fields(s,('id','asset','label','transform'));stations.append(Station(s['id'],s['asset'],s['label'],pose(s['transform'])))
            for l in data['links']:
                fields(l,('id','source','destination'));links.append(ProcessLink(**l))
            return cls(tuple(assets),tuple(stations),tuple(links))
        except (TypeError,KeyError,OverflowError,AttributeError) as error:raise ValueError('Malformed factory document.') from error
