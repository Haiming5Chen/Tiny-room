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

STOCK_SHELF=(.25,.80)   # a shelf beside the table holding the parts a production run feeds in


def stock_name(i):
    """The i-th part of a run: 'product' is the one on the input tray, then 'product_2'..."""
    return 'product' if i==0 else 'product_'+str(i+1)


def factory_scene(machine=None,product='Small block',recipe=None,stock=0):
    from .recipe import CellRecipe,TRAYS
    recipe=recipe or CellRecipe(product=product)
    product=recipe.product
    # Surfaces for sourced pair friction: steel table and frame, concrete floor, HDPE
    # trays, a wooden product. The Panda's own finger geoms come from Menagerie and
    # keep their upstream friction, so the grasp itself is unchanged by this table.
    palette=(Material('steel',2700,.7,(.5,.56,.6,1),surface='steel'),Material('dark',2700,.7,(.12,.16,.20,1),surface='steel'),
             Material('floor',2000,.8,(.25,.29,.32,1),surface='concrete'),Material('blue',950,.8,(.08,.4,.75,1),surface='hdpe'),
             Material('amber',950,.8,(.9,.55,.09,1),surface='hdpe'),Material('product',600,1.,(.78,.22,.12,1),surface='wood'))
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
    payloads=[payload]
    if stock:
        # The parts waiting for a production run (ADR 0019). The feeder that would bring
        # each to the input tray is not simulated: the run moves the next one there.
        sx,sy=STOCK_SHELF
        box('stock_shelf',(.07*stock+.05,.12,.03),(sx,sy,TABLE-.015),'dark')
        for i,x in enumerate((sx-.07*(stock-1)/2+.07*k for k in range(stock))):
            if i in (0,stock-1):box('stock_leg'+str(i),(.03,.03,TABLE-.03),(x,sy,(TABLE-.03)/2),'dark')
            payloads.append(Body(stock_name(i+1),Geometry('box',size),'product',Transform((x,sy,TABLE+size[2]/2+.001)),dynamic=True))
    # A sky backdrop instead of the black void round the floor, as the test fields have.
    return Scene((Entity('factory',Blueprint(tuple(parts),palette)),Entity('objects',Blueprint(tuple(payloads),palette)),machine or Entity('machine',robot_blueprint())),backdrop='sky')
