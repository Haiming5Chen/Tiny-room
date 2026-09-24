"""Local mating frames and quaternion math; no renderer or solver dependencies."""
from math import sqrt, cos, sin, radians
from little_world.core.component import Transform


def multiply(a, b):
    w,x,y,z=a
    v,i,j,k=b
    return (w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j,
            w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v)


def conjugate(q):
    return (q[0],-q[1],-q[2],-q[3])


def rotate(q, v):
    return multiply(multiply(q,(0,*v)),conjugate(q))[1:]


def euler_quaternion(degrees):
    x,y,z=(radians(v)/2 for v in degrees)
    return multiply(multiply((cos(z),0,0,sin(z)),(cos(y),0,sin(y),0)),(cos(x),sin(x),0,0))


def frames(body):
    g=body.geometry
    x,y,z=(tuple(v/2 for v in g.size) if g.shape=='box' else
           (g.size[0],)*3 if g.shape=='sphere' else (g.size[0],g.size[0],g.size[1]/2))
    s=sqrt(.5)
    # Z points outward; X defines twist. Curved faces are tangent frames.
    result={
        'Top':Transform((0,0,z)),
        'Bottom':Transform((0,0,-z),(0,1,0,0)),
        'Front':Transform((x,0,0),(s,0,s,0)),
        'Back':Transform((-x,0,0),(s,0,-s,0)),
        'Left':Transform((0,y,0),(s,-s,0,0)),
        'Right':Transform((0,-y,0),(s,s,0,0)),
    }
    # Explicit custom frames override generated defaults of the same name.
    result.update((a.id,a.transform) for a in body.attachments)
    return result


def mate(source, target, gap=0):
    q=multiply(multiply(target.quaternion,(0,1,0,0)),conjugate(source.quaternion))
    normal=rotate(target.quaternion,(0,0,gap))
    offset=rotate(q,source.position)
    return Transform(tuple(t+n-s for t,n,s in zip(target.position,normal,offset)),q)


def module_bounds(blueprint):
    """Bounds of all initial geometry, retaining root orientation but not translation."""
    from little_world.core.component import Body
    bodies={b.id:b for b in blueprint.components if isinstance(b,Body)}
    poses={}
    def pose(body):
        if body.id in poses:
            return poses[body.id]
        if body.parent is None:
            result=Transform(quaternion=body.transform.quaternion)
        else:
            parent=pose(bodies[body.parent])
            offset=rotate(parent.quaternion,body.transform.position)
            result=Transform(tuple(a+b for a,b in zip(parent.position,offset)),multiply(parent.quaternion,body.transform.quaternion))
        poses[body.id]=result
        return result
    lo=[float('inf')]*3; hi=[-float('inf')]*3
    for body in bodies.values():
        p=pose(body); g=body.geometry
        half=(tuple(v/2 for v in g.size) if g.shape=='box' else
              (g.size[0],)*3 if g.shape=='sphere' else (g.size[0],g.size[0],g.size[1]/2))
        basis=[rotate(p.quaternion,tuple(1 if j==i else 0 for j in range(3))) for i in range(3)]
        for i in range(3):
            extent=sum(abs(basis[j][i])*half[j] for j in range(3))
            lo[i]=min(lo[i],p.position[i]-extent)
            hi[i]=max(hi[i],p.position[i]+extent)
    return tuple(lo),tuple(hi)
