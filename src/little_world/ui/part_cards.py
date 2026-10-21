"""Cached isometric illustrations from actual catalog geometry, with SI-derived labels."""
from functools import lru_cache
from math import cos, sin, pi
import numpy as np
from little_world.assets.catalog import BY_ID
from little_world.core.component import Body, Motor, Hinge, RobotServo
from little_world.construction.docking import poses
from little_world.construction.connections import rotate


@lru_cache(maxsize=64)
def card_data(item_id):
    item=BY_ID[item_id];bp=item.blueprint();transforms=poses(bp)
    materials={m.id:m for m in bp.materials};polygons=[]
    projection=np.array(((.8,-.6,0),(.26,.35,-.9),(.54,.72,.44)))
    for b in bp.components:
        if not isinstance(b,Body):continue
        g=b.geometry;t=transforms[b.id]
        if g.shape=='box':
            x,y,z=np.array(g.size)/2
            points=[(a,c,d) for a in (-x,x) for c in (-y,y) for d in (-z,z)]
            faces=((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3))
        elif g.shape=='cylinder':
            r,length=g.size
            points=[(r*cos(i*pi/6),r*sin(i*pi/6),z) for z in (-length/2,length/2) for i in range(12)]
            faces=[tuple(range(11,-1,-1)),tuple(range(12,24))]+[(i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)]
        else:
            r=g.size[0]
            points=[(r*cos(j*pi/8-pi/2)*cos(i*pi/6),r*cos(j*pi/8-pi/2)*sin(i*pi/6),r*sin(j*pi/8-pi/2)) for j in range(9) for i in range(12)]
            faces=[(j*12+i,j*12+(i+1)%12,(j+1)*12+(i+1)%12,(j+1)*12+i) for j in range(8) for i in range(12)]
        points=np.array([np.array(t.position)+rotate(t.quaternion,p) for p in points])@projection.T
        color=np.array(materials[b.material].rgba[:3])
        for i,face in enumerate(faces):
            poly=points[list(face)]
            shade=.64+.32*((i%3)/2)
            rgb=np.clip(color*shade+.09,.10,.95)
            polygons.append((float(poly[:,2].mean()),poly[:,:2],tuple(rgb)))
    polygons.sort(key=lambda p:p[0])
    all_points=np.concatenate([p[1] for p in polygons])
    lo=all_points.min(axis=0);hi=all_points.max(axis=0)
    motors=[m for m in bp.components if isinstance(m,Motor)]
    variant=item.variant
    if variant in ('drive','wheel','hw_tread'):
        labels=(f'Diameter {item.dimensions[0]*1000:g} mm',f'Width {item.dimensions[1]*1000:g} mm','Powered / 1 Nm' if variant=='drive' else 'Passive / free rolling')
    else:
        dimensions=item.dimensions
        if variant.startswith(('ready_','lab_')):
            from little_world.construction.docking import world_bounds
            lower,upper=world_bounds(bp);dimensions=tuple(b-a for a,b in zip(lower,upper))
        dims='x'.join(f'{d*1000:.0f}' for d in dimensions)
        labels=(dims+' mm',f'{len(motors)} powered joints' if motors else item.capability,
                f'Up to {max(m.max_torque for m in motors):g} Nm' if motors else 'Rigid part' if not any(isinstance(c,Hinge) for c in bp.components) else 'Passive joints')
    if variant.startswith('lab_'):
        powered=len(motors)+sum(isinstance(c,RobotServo) for c in bp.components)
        labels=(labels[0],f'{powered} powered channels' if powered else item.capability,'Generic lab assembly')
    if item.variant=='real_robot':
        from little_world.assets.robot_models import metadata
        m=metadata(item.id)
        labels=(item.capability,f"{m['mass']:.2f} kg / fixed size",'Imported robot' if item.id.startswith('user:') else 'Menagerie model')
    return polygons,lo,hi,labels


def draw_part_picture(ui,item_id,x,y,w,h):
    if BY_ID[item_id].variant.startswith('lab_'):
        from pathlib import Path
        ui.image(Path(__file__).resolve().parents[1]/'assets'/'data'/(item_id+'.png'),x,y,w,h)
        return
    if BY_ID[item_id].variant=='real_robot':
        from little_world.assets.robot_models import asset_root
        picture=asset_root(item_id)/'thumbnail.png'
        if picture.is_file():   # an imported robot has none: its outline is drawn instead
            ui.image(picture,x,y,w,h)
            return
    polygons,lo,hi,_=card_data(item_id)
    ui.rect(x,y,w,h,(.055,.08,.105))
    scale=min((w-14)/max(.001,hi[0]-lo[0]),(h-14)/max(.001,hi[1]-lo[1]))
    center=(lo+hi)/2
    for _,poly,color in polygons:
        points=(poly-center)*scale+np.array((x+w/2,y+h/2))
        ui.polygon(points,color)


def draw_part_card(ui,text,item,x,y,w):
    *_,labels=card_data(item.id)
    draw_part_picture(ui,item.id,x+10,y+34,108,77)
    for i,label in enumerate(labels):text(label,x+127,y+39+i*22,10,(.67,.79,.81),w-135)
    from little_world.assets.part_guides import part_guide
    text(('Real robot / drop in build area' if item.variant=='real_robot' else 'Lab assembly / drag to place' if item.variant.startswith('lab_') else 'Complete base / drop in build area' if item.mount=='Floor' else part_guide(item)['level']+' / drag to connect'),x+12,y+116,10,(.48,.66,.7),w-24)
