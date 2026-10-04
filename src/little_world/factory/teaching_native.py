"""Panda Cartesian teaching through existing scratch IK and native servos."""
import numpy as np
from .controller import FactoryCycle
from .teaching import TaughtPosition

class TeachingMotion:
    def __init__(self,backend):
        self.ik=FactoryCycle(backend)
        self.target=None;self.state='idle';self.message='Drag the target, then Preview reach.'
        self.held={}

    def preview(self,point):
        self.target=None;self.state='idle'
        point=np.asarray(TaughtPosition('Target',point).point)
        try:q=self.ik.solve(point,self.ik.data.qpos[self.ik.qids].copy())
        except ValueError:
            self.state='unreachable';self.message='Unreachable with the hand pointing down.';raise
        self.point=point;self.target=q;self.state='ready';self.message='Reachable. Path is not checked for obstacles.'

    def start(self):
        if self.target is None:raise ValueError('Preview a reachable target first.')
        self.begin=self.ik.data.qpos[self.ik.qids].copy()
        self.duration=max(1.2,float(np.max(np.abs(self.target-self.begin)))/.4)
        self.elapsed=0.;self.state='moving';self.message='Moving to taught position.'

    def commands(self,dt):
        if self.state!='moving':return self.held
        self.elapsed+=dt;t=min(1.,self.elapsed/self.duration);blend=t*t*(3-2*t)
        q=self.begin+(self.target-self.begin)*blend
        self.held={'machine/servo_'+str(i+1):float(v) for i,v in enumerate(q)}
        if self.elapsed>=self.duration+.4:
            error=float(np.linalg.norm(self.ik.tool(self.ik.data)-self.point))
            if error<.012:self.state='reached';self.message='Position reached (within 12 mm).'
            elif self.elapsed>self.duration+3:
                self.state='failed';self.message='Could not reach target. Inspect contact or joint limits.'
        return self.held
