"""Revision-aware authoring transactions; independent of graphics and physics."""
from dataclasses import dataclass
import hashlib
import json
from .document import FactoryDocument,fields,strict_object


def asset_description(asset):
    payload=json.dumps(json.loads(asset.blueprint.to_json()),sort_keys=True,separators=(',',':'))
    return dict(id=asset.id,components=len(asset.blueprint.components),sha256=hashlib.sha256(payload.encode()).hexdigest())


def describe_changes(before,after):
    result=[]
    a=before.to_data();b=after.to_data()
    a['assets']=[asset_description(x) for x in before.assets];b['assets']=[asset_description(x) for x in after.assets]
    for collection in ('assets','stations','links'):
        old={x['id']:x for x in a[collection]};new={x['id']:x for x in b[collection]}
        for id in sorted(old.keys()|new.keys()):
            if old.get(id)!=new.get(id):
                result.append(dict(collection=collection,id=id,operation='add' if id not in old else 'remove' if id not in new else 'update',
                                   before=old.get(id),after=new.get(id)))
    return tuple(result)


@dataclass(frozen=True)
class DocumentProposal:
    before:FactoryDocument
    after:FactoryDocument
    revision:int

    def __post_init__(self):
        if not isinstance(self.before,FactoryDocument) or not isinstance(self.after,FactoryDocument):raise ValueError('Proposal needs two factory documents.')
        if type(self.revision) is not int or self.revision<0:raise ValueError('Invalid edit revision.')

    @property
    def changes(self):return describe_changes(self.before,self.after)

    @property
    def affected_stations(self):
        changes=self.changes
        assets={c['id'] for c in changes if c['collection']=='assets'}
        stations={c['id'] for c in changes if c['collection']=='stations'}
        for s in self.before.stations+self.after.stations:
            if s.asset in assets:stations.add(s.id)
        for doc in (self.before,self.after):
            changed_links={c['id'] for c in changes if c['collection']=='links'}
            for link in doc.links:
                if link.id in changed_links:stations.update((link.source,link.destination))
        return tuple(sorted(stations))

    def report(self):
        return dict(revision=self.revision,changes=list(self.changes),affected_stations=list(self.affected_stations),
                    checked=['schema','unique IDs','asset references','process-link references','world transforms'],
                    not_checked=['collision clearance','robot reach','process execution','throughput'],
                    process_links='layout intent only; no executor')

    def to_json(self):
        return json.dumps(dict(version=1,revision=self.revision,before=self.before.to_data(),after=self.after.to_data()),indent=2,allow_nan=False)

    @classmethod
    def from_json(cls,text):
        try:
            data=json.loads(text,object_pairs_hook=strict_object)
            fields(data,('version','revision','before','after'))
            if type(data['version']) is not int or data['version']!=1:raise ValueError('Unsupported proposal version.')
            return cls(FactoryDocument.from_json(json.dumps(data['before'])),FactoryDocument.from_json(json.dumps(data['after'])),data['revision'])
        except (TypeError,KeyError,OverflowError) as error:raise ValueError('Malformed document proposal.') from error


class FactoryEditor:
    def __init__(self,document=None):
        self.document=FactoryDocument() if document is None else document
        if not isinstance(self.document,FactoryDocument):raise ValueError('Expected a factory document.')
        self.revision=0;self._past=[];self._future=[]

    def clone(self):
        copy=FactoryEditor(self.document)
        copy.revision=self.revision;copy._past=list(self._past);copy._future=list(self._future)
        return copy

    @property
    def can_undo(self):return bool(self._past)
    @property
    def can_redo(self):return bool(self._future)

    def preview(self,candidate):return DocumentProposal(self.document,candidate,self.revision)

    def apply(self,proposal):
        if not isinstance(proposal,DocumentProposal):raise ValueError('Expected a reviewed document proposal.')
        if proposal.before!=self.document or proposal.revision!=self.revision:
            raise ValueError('Scene changed since this proposal. Review a fresh snapshot.')
        if proposal.after==self.document:return
        self._past.append(self.document);self.document=proposal.after;self._future.clear();self.revision+=1

    def undo(self):
        if self._past:
            self._future.append(self.document);self.document=self._past.pop();self.revision+=1

    def redo(self):
        if self._future:
            self._past.append(self.document);self.document=self._future.pop();self.revision+=1
