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
PRODUCT_DENSITY=600     # kg/m3: the parts' wood (the 'product' material)

def robot_blueprint(asset='franka_panda'):
    bp=blueprint(asset)
    return replace(bp,components=tuple(replace(c,transform=replace(c.transform,position=tuple(v+(TABLE if i==2 else 0) for i,v in enumerate(c.transform.position)))) if isinstance(c,Body) and c.parent is None else c for c in bp.components))

STOCK_SHELF=(.25,.80)   # a shelf beside the table holding the parts a production run feeds in
FEEDERS=('hand','conveyor') # how parts reach the source: put there by hand, or by the roller conveyor (ADR 0068)
ON_LINE=2   # pallets on the conveyor: one at its stop, one queued behind; each emptied one goes back to its start
# Each pallet locates its part between two bars across the line, as a workpiece carrier's fixture
# does: m of room each side, the bars' thickness and height. A loose part slides on its pallet at
# every stop (ADR 0068); the fingers close across the line, between the bars.
NEST=(.002,.004,.008)
CAMERA_POSTS=((.72,-.43),(.72,.43))
TABLE_TOP=((-.375,-.55),(.875,.55))     # the worktable's top, (x, y) low and high corners


def stock_name(i):
    """The i-th part of a run: 'product' is the one on the input tray, then 'product_2'..."""
    return 'product' if i==0 else 'product_'+str(i+1)


def conveyor_line(recipe):
    """The roller conveyor that feeds the cell (ADR 0068): standing on the table, carrying towards
    the robot along -x, its stop holding a pallet centred on the source tray's place - or a
    ValueError where it does not fit: off the table, over another tray or a camera post, or at
    the robot's base."""
    from little_world.fields.conveyor import BED, Line, PALLET, PITCH, ROLLER, ROLLERS
    from .recipe import TRAYS
    x,y=recipe.point(recipe.source)
    start=x-PALLET[0]/2+(ROLLERS-1)*PITCH+PITCH/2       # the first roller's axis: the stop half a pitch past the last
    w,d,h=PRODUCTS[recipe.product]
    line=Line((start,y),TABLE+2*ROLLER[0]+BED+.010,-1,'factory',load=w*d*h*PRODUCT_DENSITY)
    x0,y0,x1,y1=line.footprint();(tx0,ty0),(tx1,ty1)=TABLE_TOP
    if x0<tx0 or x1>tx1 or y0<ty0 or y1>ty1:raise ValueError('The conveyor runs off the table from there.')
    for name,(px,py) in zip(TRAYS,recipe.positions):
        if name!=recipe.source and x0-.10<px<x1+.10 and y0-.09<py<y1+.09:raise ValueError(f'The conveyor would cross the {name} tray.')
    for px,py in CAMERA_POSTS:
        if x0-.0125<px<x1+.0125 and y0-.0125<py<y1+.0125:raise ValueError('The conveyor would cross a camera support.')
    if x0<.20:raise ValueError('Leave space round the robot base for the conveyor.')
    return line


def factory_scene(machine=None,product='Small block',recipe=None,stock=0,feeder='hand'):
    """The cell: its table, trays, camera and robot, the product on its source - and `stock` more
    parts for a production run. Fed by `feeder` 'conveyor' (ADR 0068), the source tray is the
    roller conveyor's stop instead: ON_LINE pallets on it, a part on each while parts last, the
    rest on the stock shelf."""
    from .recipe import CellRecipe,TRAYS
    if feeder not in FEEDERS:raise ValueError('Unknown feeder')
    recipe=recipe or CellRecipe(product=product)
    product=recipe.product
    line=conveyor_line(recipe) if feeder=='conveyor' else None
    # Surfaces for sourced pair friction: steel table and frame, concrete floor, HDPE
    # trays, a wooden product. The Panda's own finger geoms come from Menagerie and
    # keep their upstream friction, so the grasp itself is unchanged by this table.
    palette=(Material('steel',2700,.7,(.5,.56,.6,1),surface='steel'),Material('dark',2700,.7,(.12,.16,.20,1),surface='steel'),
             Material('floor',2000,.8,(.25,.29,.32,1),surface='concrete'),Material('blue',950,.8,(.08,.4,.75,1),surface='hdpe'),
             Material('amber',950,.8,(.9,.55,.09,1),surface='hdpe'),Material('product',PRODUCT_DENSITY,1.,(.78,.22,.12,1),surface='wood'))
    parts=[]
    def box(id,size,pos,mat='steel'):
        parts.append(Body(id,Geometry('box',size),mat,Transform(pos)))
    box('floor',(5,4,.1),(0,0,-.05),'floor')
    box('table',(1.25,1.1,.06),(.25,0,TABLE-.03))
    for i,(x,y) in enumerate(((-.32,-.48),(-.32,.48),(.82,-.48),(.82,.48))):box('leg'+str(i),(.055,.055,TABLE-.06),(x,y,(TABLE-.06)/2),'dark')
    for name,(x,y) in zip(TRAYS,recipe.positions):
        if line is not None and name==recipe.source:continue     # the conveyor's stop instead
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
    if line is not None:
        from little_world.fields.conveyor import PALLET
        # The conveyor's materials, as the fields' (a roller as heavy as its steel tube; HDPE pallets).
        palette+=(Material('roller',404,.5,(.70,.72,.74,1),surface='steel'),
                  Material('pallet',950,.3,(.20,.26,.30,1),'matte_plastic',.6,'hdpe'))
        parts.extend(line.parts(stand='dark'))
        payloads=[];y=line.start[1]
        for k in range(1,ON_LINE+1):
            # Pallet 1 at the stop, the next queued behind it, each set 1 mm short of its place.
            x=line.at_stop(k)-line.heading*.001*k
            payloads.append(Body('pallet_'+str(k),Geometry('box',PALLET),'pallet',Transform((x,y,line.pallet_z()+.0005)),dynamic=True))
            room,thick,high=NEST
            for j,side in enumerate((-1,1)):
                payloads.append(Body(f'pallet_{k}_bar_{j}',Geometry('box',(thick,size[1]+.008,high)),'pallet',
                                     Transform((side*(size[0]/2+room+thick/2),0.,PALLET[2]/2+high/2)),parent='pallet_'+str(k)))
            if k<=stock+1:
                payloads.append(Body(stock_name(k-1),Geometry('box',size),'product',Transform((x,y,line.top+PALLET[2]+size[2]/2+.001)),dynamic=True))
        shelf=range(ON_LINE,stock+1)        # the parts that wait for a pallet
    else:
        payload=Body('product',Geometry('box',size),'product',Transform((*recipe.point(recipe.source),TABLE+.008+size[2]/2+.001)),dynamic=True)
        payloads=[payload];shelf=range(1,stock+1)
    stock=len(shelf)
    if stock:
        # The parts waiting for a production run (ADR 0019). The feeder that would bring
        # each to the input tray is not simulated: the run moves the next one there.
        sx,sy=STOCK_SHELF
        box('stock_shelf',(.07*stock+.05,.12,.03),(sx,sy,TABLE-.015),'dark')
        for i,x in enumerate((sx-.07*(stock-1)/2+.07*k for k in range(stock))):
            if i in (0,stock-1):box('stock_leg'+str(i),(.03,.03,TABLE-.03),(x,sy,(TABLE-.03)/2),'dark')
            payloads.append(Body(stock_name(shelf[i]),Geometry('box',size),'product',Transform((x,sy,TABLE+size[2]/2+.001)),dynamic=True))
    # A sky backdrop instead of the black void round the floor, as the test fields have.
    return Scene((Entity('factory',Blueprint(tuple(parts),palette)),Entity('objects',Blueprint(tuple(payloads),palette)),machine or Entity('machine',robot_blueprint())),backdrop='sky')
