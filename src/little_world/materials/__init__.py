"""Illustrative mechanical parameters, not calibrated material datasets."""
from little_world.core.material import Material

WOOD = Material("wood", 600, .6, (1., 1., 1., 1), "wood_grain", .75)
METAL = Material("metal", 2700, .5, (.72, .77, .80, 1), "brushed_metal", .25)
RUBBER = Material("rubber", 1100, 1.2, (.16, .18, .20, 1), "rubber_tread", .95)
FLOOR = Material("floor", 2200, .8, (.68, .70, .72, 1))
SKID = Material("skid", 500, .01, (.85, .85, .86, 1))

PLASTIC = Material("plastic", 1050, .5, (.18, .38, .53, 1), "matte_plastic", .7)
