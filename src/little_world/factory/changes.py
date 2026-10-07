"""Reviewable cell edits shared by code and UI; no native or executable content."""
from dataclasses import dataclass
import json
from math import isfinite
from .recipe import CellRecipe,TRAYS,PRODUCT_NAMES


def _finite_number(value):
    if type(value) not in (int,float):return False
    try:return isfinite(value)
    except OverflowError:return False


def _object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate JSON field: '+key)
        result[key]=value
    return result


@dataclass(frozen=True)
class CellChange:
    kind:str
    target:str
    value:object

    def __post_init__(self):
        if isinstance(self.value,list):object.__setattr__(self,'value',tuple(self.value))


@dataclass(frozen=True)
class CellRequest:
    base:CellRecipe
    revision:int
    changes:tuple[CellChange,...]

    def __post_init__(self):
        if not isinstance(self.base,CellRecipe) or type(self.revision) is not int or self.revision<0:
            raise ValueError('A request needs a base recipe and a nonnegative edit revision.')
        object.__setattr__(self,'changes',tuple(self.changes))
        if len(self.changes)>16 or any(not isinstance(c,CellChange) for c in self.changes):
            raise ValueError('A request supports at most 16 cell changes.')

    def to_json(self):
        return json.dumps(dict(version=1,units='m',frame='world',revision=self.revision,
            base=json.loads(self.base.to_json()),changes=[dict(kind=c.kind,target=c.target,value=c.value) for c in self.changes]),indent=2,allow_nan=False)

    @classmethod
    def from_json(cls,text):
        try:
            data=json.loads(text,object_pairs_hook=_object)
            if not isinstance(data,dict) or set(data)!={'version','units','frame','revision','base','changes'}:
                raise ValueError('Invalid cell request fields.')
            if type(data['version']) is not int or data['version']!=1 or data['units']!='m' or data['frame']!='world':
                raise ValueError('Use version 1, metres (m), world coordinates.')
            if not isinstance(data['changes'],list):raise ValueError('Changes must be a list.')
            changes=[]
            for entry in data['changes']:
                if not isinstance(entry,dict) or set(entry)!={'kind','target','value'}:raise ValueError('Invalid change fields.')
                changes.append(CellChange(**entry))
            return cls(CellRecipe.from_json(json.dumps(data['base'])),data['revision'],tuple(changes))
        except (TypeError,KeyError,OverflowError) as error:
            raise ValueError('Malformed cell request.') from error


@dataclass(frozen=True)
class CellPreview:
    before:CellRecipe
    after:CellRecipe
    revision:int
    summary:tuple[str,...]

    def apply(self,current,revision):
        if current!=self.before or revision!=self.revision:
            raise ValueError('The cell changed after this proposal was prepared. Export a fresh draft and review again.')
        return self.after


def preview_changes(current,revision,request):
    if current!=request.base or revision!=request.revision:
        raise ValueError('The cell changed after this proposal was prepared. Export a fresh draft and review again.')
    positions=list(current.positions);source=current.source;destination=current.destination;product=current.product
    seen=set()
    for c in request.changes:
        if not isinstance(c.kind,str) or not isinstance(c.target,str):raise ValueError('Change kind and target must be text IDs.')
        key=(c.kind,c.target)
        if key in seen:raise ValueError('Duplicate edit for '+c.target)
        seen.add(key)
        if c.kind=='tray':
            if c.target not in TRAYS:raise ValueError('Unknown tray: '+c.target)
            if not isinstance(c.value,tuple) or len(c.value)!=2 or any(not _finite_number(v) for v in c.value):
                raise ValueError('Tray position needs two finite numbers in world metres.')
            positions[TRAYS.index(c.target)]=c.value
        elif c.kind=='task':
            if c.target!='route' or not isinstance(c.value,tuple) or len(c.value)!=2 or any(v not in TRAYS for v in c.value):
                raise ValueError('Task route needs source and destination tray IDs.')
            source,destination=c.value
        elif c.kind=='product':
            if c.target!='product' or c.value not in PRODUCT_NAMES:raise ValueError('Unknown product or product target.')
            product=c.value
        else:raise ValueError('Unsupported cell operation: '+c.kind)
    # Validate the final transaction, not intermediate layouts (e.g. tray swaps).
    after=CellRecipe(tuple(positions),source,destination,product)
    summary=[]
    for name in TRAYS:
        a=current.point(name);b=after.point(name)
        if a!=b:summary.append(f'{name}: ({a[0]!r}, {a[1]!r}) -> ({b[0]!r}, {b[1]!r}) m')
    if (current.source,current.destination)!=(after.source,after.destination):
        summary.append(f'Route: {current.source} -> {current.destination} becomes {after.source} -> {after.destination}')
    if current.product!=after.product:summary.append(f'Product: {current.product} -> {after.product}')
    return CellPreview(current,after,revision,tuple(summary))
