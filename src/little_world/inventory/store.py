from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,uuid
from math import isfinite
from little_world.core.blueprint import Blueprint
from little_world.programming.program import Program


def fingerprint(value):
    return hashlib.sha256(value.to_json().encode()).hexdigest()


@dataclass(frozen=True)
class SavedDesign:
    id: str
    name: str
    status: str
    notes: str
    created: str
    blueprint: Blueprint
    program: Program


class Inventory:
    def __init__(self,path):self.path=Path(path)
    def _file(self,identifier):
        if str(uuid.UUID(identifier))!=identifier:raise ValueError('Invalid inventory ID')
        return self.path/(identifier+'.json')
    def _write(self,record):
        self.path.mkdir(parents=True,exist_ok=True)
        path=self._file(record.id)
        data=dict(version=1,id=record.id,name=record.name,status=record.status,notes=record.notes,created=record.created,
                  blueprint=json.loads(record.blueprint.to_json()),program=json.loads(record.program.to_json()))
        temporary=path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
        temporary.write_text(json.dumps(data,indent=2,allow_nan=False), encoding='utf-8');temporary.replace(path)
        return record
    @staticmethod
    def _metadata(name,status,notes):
        if not isinstance(name,str) or not 1<=len(name.strip())<=72:raise ValueError('Name must be 1 to 72 characters')
        if status not in ('draft','finished'):raise ValueError('Status must be draft or finished')
        if not isinstance(notes,str) or len(notes)>2000:raise ValueError('Notes must be at most 2000 characters')
    def save(self,name,status,notes,blueprint,program):
        self._metadata(name,status,notes)
        return self._write(SavedDesign(str(uuid.uuid4()),name.strip(),status,notes,datetime.now(timezone.utc).isoformat(),blueprint,program))
    def read(self,identifier):
        d=json.loads(self._file(identifier).read_text(encoding='utf-8'))
        if d.get('version')!=1 or d.get('id')!=identifier:raise ValueError('Invalid inventory record')
        self._metadata(d['name'],d['status'],d['notes'])
        return SavedDesign(identifier,d['name'],d['status'],d['notes'],d['created'],Blueprint.from_json(json.dumps(d['blueprint'])),Program.from_json(json.dumps(d['program'])))
    def list(self):
        records=[];errors=[]
        for path in self.path.glob('*.json'):
            try:records.append(self.read(path.stem))
            except (ValueError,TypeError,KeyError,OSError) as e:errors.append(path.name+': '+str(e))
        return sorted(records,key=lambda r:r.created,reverse=True),errors
    def update(self,identifier,name,status,notes):
        from dataclasses import replace
        self._metadata(name,status,notes)
        return self._write(replace(self.read(identifier),name=name.strip(),status=status,notes=notes))
    @staticmethod
    def valid_comparison(d):
        try:
            if d['version']!=1 or not isinstance(d['created'],str):return False
            for field in ('left_hash','right_hash'):
                if len(d[field])!=64 or any(c not in '0123456789abcdef' for c in d[field]):return False
            p=d['protocol']
            if p['mode'] not in ('hold_drive','program') or not isinstance(p['solver'],str) or not isinstance(p['environment'],str):return False
            if p['mode']=='program' and (not isinstance(p.get('program'),str) or len(p['program'])!=64):return False
            for side in ('left','right'):
                if not isinstance(d[side]['program_state'],str):return False
                for key in ('displacement_m','peak_joint_error_deg','peak_tilt_deg','absolute_mechanical_work_J'):
                    if not isfinite(d[side][key]):return False
            return True
        except (KeyError,TypeError,ValueError):return False

    def save_comparison(self,result):
        if not self.valid_comparison(result):raise ValueError('Invalid comparison result')
        path=self.path/'comparisons';path.mkdir(parents=True,exist_ok=True)
        target=path/(str(uuid.uuid4())+'.json');temporary=target.with_suffix('.tmp')
        temporary.write_text(json.dumps(result,indent=2,allow_nan=False));temporary.replace(target)
        return target
    def comparisons(self):
        records=[]
        for path in (self.path/'comparisons').glob('*.json'):
            try:
                d=json.loads(path.read_text())
                if self.valid_comparison(d):records.append(d)
            except (ValueError,OSError):continue
        return sorted(records,key=lambda d:d.get('created',''),reverse=True)
