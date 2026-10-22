"""Ideal observations from native state; no noise or vendor sensor behavior."""
from math import sqrt


class Observations:
    def __init__(self,model,data,jaws=()):
        # `jaws`: an imported gripper's two jaw links, by name (MujocoBackend.robot_jaws, ADR 0047).
        self.model=model;self.data=data;self.jaws=tuple(tuple(pair) for pair in jaws)
        self.names={i:model.body(i).name for i in range(1,model.nbody)}
        self.indices={name:i for i,name in self.names.items()}

    def contact_pairs(self):
        pairs=set()
        for i in range(self.data.ncon):
            c=self.data.contact[i]
            if c.dist>0:continue
            a=int(self.model.geom_bodyid[c.geom1]);b=int(self.model.geom_bodyid[c.geom2])
            if a in self.names and b in self.names:pairs.add(frozenset((self.names[a],self.names[b])))
        return frozenset(pairs)

    def distance(self,a,b):
        p=self.data.xpos[self.indices[a]];q=self.data.xpos[self.indices[b]]
        return sqrt(sum(float(v-w)**2 for v,w in zip(p,q)))

    def program_inputs(self,program):
        distances={(b.target,b.other):self.distance(b.target,b.other) for b in program.blocks if b.kind=='distance'}
        contacts=self.contact_pairs() if any(b.kind in ('contact','if_contact') for b in program.blocks) else frozenset()
        return contacts,distances

    def grasped(self):
        # Bilateral jaw contact on something that can move: a part fixed to the world - a
        # table, a wall - pressed between the jaws is not held (ADR 0030). It does not prove
        # a stable grasp or a payload rating.
        pair_names=[tuple(pair) for pair in self.contact_pairs()]
        left={};right={}
        for pair in pair_names:
            for a,b in (pair,pair[::-1]):
                if '_finger_left_pad' in a:left.setdefault(a.split('_finger_left_pad')[0],set()).add(b)
                if '_finger_right_pad' in a:right.setdefault(a.split('_finger_right_pad')[0],set()).add(b)
                if '__robot_left_finger' in a:left.setdefault(a.split('left_finger')[0],set()).add(b)
                if '__robot_right_finger' in a:right.setdefault(a.split('right_finger')[0],set()).add(b)
                for first,second in self.jaws:
                    prefix=first.split('__robot_')[0]+'__robot_'
                    if a==first:left.setdefault(prefix,set()).add(b)
                    if a==second:right.setdefault(prefix,set()).add(b)
        return frozenset(obj for prefix,objects in left.items() for obj in objects & right.get(prefix,set())
                         if not obj.startswith(prefix) and self.model.body_weldid[self.indices[obj]]!=0)
