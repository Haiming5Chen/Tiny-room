"""Original driven components: one rigid load, attached to an existing output."""
from math import pi,cos,sin
from little_world.core.component import Body,Geometry,Transform,Attachment
from little_world.core.blueprint import Blueprint
from little_world.materials import METAL,RUBBER


def entries(Part):
    rows=[]
    for name,label,values in (
        ('crank','Crank arm',((100,20),(180,24))),
        ('drive_roller','Drive roller',((60,80),(100,120))),
        ('flywheel','Flywheel',((80,12),(140,16))),
        ('spool','Cable spool',((40,50),(80,70))),
        ('turntable','Rotating tool plate',((80,8),(140,10)))):
        for diameter,width in values:
            dims=(diameter/1000,.020,width/1000) if name=='crank' else (diameter/1000,diameter/1000,width/1000)
            rows.append(Part(f'{name}_{diameter}',f'{label} / {diameter} mm','Driven parts',
                'Attaches rigidly to a motor output; the motor supplies the joint and torque.',
                'Shaft-driven component',dims,'shaft_load','output'))
    return tuple(rows)


def make_load(item):
    parts=[];x,y,z=item.dimensions
    def body(name,shape,size,pos=(0,0,0),material='metal',parent='root',attachments=()):
        parts.append(Body(name,Geometry(shape,size),material,Transform(pos),parent,
                          dynamic=parent is None,attachments=attachments))
    body('root','cylinder',(.012,.018),parent=None,
         attachments=(Attachment('shaft_mount',Transform((0,0,-.009),(0,1,0,0))),))
    if item.id.startswith('crank'):
        body('lever','box',(x,.018,.008),(x/2-.012,0,.013))
        body('end_pin','cylinder',(.005,.020),(x-.024,0,.019))
    elif item.id.startswith('drive_roller'):
        body('roller','cylinder',(x/2,z),(0,0,z/2+.009),'rubber')
        for i in (-1,1):body('end_'+str(i).replace('-','n'),'cylinder',(x*.44,.004),(0,0,.009+(z if i>0 else 0)))
    elif item.id.startswith('spool'):
        body('drum','cylinder',(x*.30,z),(0,0,z/2+.009))
        for i in (0,1):body('flange_'+str(i),'cylinder',(x/2,.004),(0,0,.009+i*z))
    else:
        body('disc','cylinder',(x/2,z),(0,0,.009+z/2))
        for i in range(6):
            a=i*pi/3
            body('bolt_'+str(i),'cylinder',(.0025,.003),(x*.35*cos(a),x*.35*sin(a),.011+z))
    return Blueprint(tuple(parts),(METAL,RUBBER))
