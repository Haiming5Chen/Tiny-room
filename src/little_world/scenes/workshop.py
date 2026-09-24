"""Procedural furnished room and loose objects, independent of the machine/task."""
from little_world.components import box, Transform
from little_world.core.blueprint import Blueprint
from little_world.core.entity import Entity
from little_world.core.material import Material
from little_world.core.scene import Scene


def workshop_entities():
    palette = (
        Material('plaster', 1600, .7, (.84, .85, .80, 1)),
        Material('teal', 1600, .7, (.27, .43, .44, 1)),
        Material('oak', 650, .6, (1., 1., 1., 1), 'wood_grain', .75),
        Material('floor_a', 650, .65, (1., 1., 1., 1), 'wood_floor', .8),
        Material('floor_b', 650, .65, (.97, .97, .97, 1), 'wood_floor', .8),
        Material('dark', 2700, .6, (.12, .17, .19, 1)),
        Material('sky', 1200, .5, (.58, .79, .85, 1)),
        Material('cream', 650, .6, (.91, .84, .65, 1)),
        Material('red', 600, .6, (.76, .25, .16, 1)),
    )
    parts = []

    def fixed(name, size, material, position):
        parts.append(box(name, size, material, transform=Transform(position)))

    fixed('floor', (5,4,.08), 'floor_a', (0,0,-.04))
    # Cutaway walls keep the workshop visible from its open front.
    fixed('back_wall', (5, .12, 2.5), 'plaster', (0, 2.06, 1.25))
    fixed('side_wall', (.12, 4.12, 2.5), 'teal', (2.56, 0, 1.25))
    fixed('back_trim', (5, .035, .10), 'cream', (0, 1.985, .05))
    fixed('window', (1.4, .03, .9), 'sky', (-.7, 1.975, 1.65))
    for x in (-1.43, -.7, .03):
        fixed('window_v_' + str(len(parts)), (.055, .07, 1), 'cream', (x, 1.945, 1.65))
    for z in (1.17, 2.13):
        fixed('window_h_' + str(len(parts)), (1.5, .07, .055), 'cream', (-.7, 1.945, z))
    fixed('bench_top', (1.45, .55, .08), 'oak', (-1.15, 1.40, .76))
    for i, (x, y) in enumerate(((-1.77, 1.2), (-.53, 1.2), (-1.77, 1.6), (-.53, 1.6))):
        fixed(f'bench_leg_{i}', (.065, .065, .72), 'dark', (x, y, .36))
    fixed('bench_crate', (.32, .27, .24), 'red', (-1.5, 1.4, .92))
    for i, z in enumerate((.18, .70, 1.22)):
        fixed(f'shelf_{i}', (.85, .4, .05), 'oak', (1.45, 1.65, z))
    for i, x in enumerate((1.05, 1.85)):
        fixed(f'shelf_post_{i}', (.05, .4, 1.5), 'dark', (x, 1.65, .75))
    for i, (x, z) in enumerate(((1.2, .35), (1.57, .36), (1.4, .88), (1.6, 1.4))):
        fixed(f'storage_{i}', (.23, .24, .26), 'cream' if i % 2 else 'teal', (x, 1.65, z))
    room = Entity('workshop', Blueprint(tuple(parts), palette))
    props = Entity('objects', Blueprint((
        box('pickup_stand', (.065,.085,.187), 'dark', transform=Transform((.460,0,.0935))),
        box('grasp_cube', (.025,.025,.040), 'cream', dynamic=True, transform=Transform((.460,0,.208))),
        box('red_block', (.14, .14, .14), 'red', dynamic=True, transform=Transform((.75, .2, .08))),
        box('wood_block', (.18, .18, .18), 'oak', dynamic=True, transform=Transform((.9, .45, .10))),
        box('cream_block', (.12, .12, .24), 'cream', dynamic=True, transform=Transform((.6, .65, .13))),
    ), palette))
    return room, props


def workshop_scene(machine):
    return Scene((*workshop_entities(), machine))
