"""Portable fixed Panda sorting cell; no task logic in the scene."""
from dataclasses import replace
from little_world.core.component import Body,Geometry,Transform,Camera
from little_world.core.blueprint import Blueprint
from little_world.core.entity import Entity
from little_world.core.scene import Scene
from little_world.assets.robot_models import blueprint
from little_world.core.material import Material

TABLE=.70
BINS={'Blue':(.44,-.24),'Amber':(.44,.24)}
PRODUCTS={'Small block':(.032,.032,.04),'Tall block':(.032,.032,.065)}

def robot_blueprint(asset='franka_panda'):
    bp=blueprint(asset)
    return replace(bp,components=tuple(replace(c,transform=replace(c.transform,position=tuple(v+(TABLE if i==2 else 0) for i,v in enumerate(c.transform.position)))) if isinstance(c,Body) and c.parent is None else c for c in bp.components))

def factory_scene(machine=None,product='Small block',recipe=None):
    from .recipe import CellRecipe,TRAYS
    recipe=recipe or CellRecipe(product=product)
    product=recipe.product
    palette=(Material('steel',2700,.7,(.5,.56,.6,1)),Material('dark',2700,.7,(.12,.16,.20,1)),
             Material('floor',2000,.8,(.25,.29,.32,1)),Material('blue',950,.8,(.08,.4,.75,1)),
             Material('amber',950,.8,(.9,.55,.09,1)),Material('product',600,1.,(.78,.22,.12,1)))
    parts=[]
    def box(id,size,pos,mat='steel'):
        parts.append(Body(id,Geometry('box',size),mat,Transform(pos)))
    box('floor',(5,4,.1),(0,0,-.05),'floor')
    box('table',(1.25,1.1,.06),(.25,0,TABLE-.03))
    for i,(x,y) in enumerate(((-.32,-.48),(-.32,.48),(.82,-.48),(.82,.48))):box('leg'+str(i),(.055,.055,TABLE-.06),(x,y,(TABLE-.06)/2),'dark')
    for name,(x,y) in zip(TRAYS,recipe.positions):
        mat={'Blue':'blue','Amber':'amber'}.get(name,'dark')
        box(name+'_base',(.20,.18,.008),(x,y,TABLE+.004),mat)
        for i,side in enumerate((-1,1)):
            box(name+'_wallx'+str(i),(.008,.18,.035),(x+side*.096,y,TABLE+.0255),mat)
            box(name+'_wally'+str(i),(.184,.008,.035),(x,y+side*.086,TABLE+.0255),mat)
    # A real camera, available as a view. Task control deliberately uses ideal state.
    for i,y in enumerate((-.43,.43)):box('camera_post'+str(i),(.025,.025,.90),(.72,y,TABLE+.45),'dark')
    box('camera_beam',(.025,.9,.025),(.72,0,TABLE+.90),'dark')
    box('camera_mount',(.30,.025,.025),(.58,0,TABLE+.90),'dark')
    box('camera_housing',(.06,.08,.045),(.45,0,TABLE+.86),'blue')
    parts.append(Camera('overhead','camera_housing',Transform((0,0,-.03)),60))
    size=PRODUCTS[product]
    payload=Body('product',Geometry('box',size),'product',Transform((*recipe.point(recipe.source),TABLE+.008+size[2]/2+.001)),dynamic=True)
    return Scene((Entity('factory',Blueprint(tuple(parts),palette)),Entity('objects',Blueprint((payload,),palette)),machine or Entity('machine',robot_blueprint())))
