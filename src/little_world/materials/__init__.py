"""Illustrative densities and appearance; contact friction comes from sourced pairs.

`sliding_friction` is the old per-material coefficient. It still applies to any pair
that materials/contact_pairs.py does not cover, through MuJoCo's own combination (the
larger of the two). `surface` names the real surface whose sourced pair values replace
it where a source exists.
"""
from dataclasses import replace
from little_world.core.material import Material

WOOD = Material("wood", 600, .6, (1., 1., 1., 1), "wood_grain", .75, "wood")
METAL = Material("metal", 2700, .5, (.72, .77, .80, 1), "brushed_metal", .25, "aluminium")
RUBBER = Material("rubber", 1100, 1.2, (.16, .18, .20, 1), "rubber_tread", .95, "rubber")
FLOOR = Material("floor", 2200, .8, (.68, .70, .72, 1), surface="concrete")
SKID = Material("skid", 500, .01, (.85, .85, .86, 1), surface="ptfe")

PLASTIC = Material("plastic", 1050, .5, (.18, .38, .53, 1), "matte_plastic", .7, "abs")

# Designs saved before surfaces existed carry these materials without a `surface`.
# Same id, same density and same friction means it came from this library, so it is
# recognised as that surface. Anything the user changed stays unsourced.
LEGACY_SURFACES = {
    ("wood", 600, .6): "wood", ("metal", 2700, .5): "aluminium",
    ("rubber", 1100, 1.2): "rubber", ("floor", 2200, .8): "concrete",
    ("skid", 500, .01): "ptfe", ("plastic", 1050, .5): "abs",
    ("anodized", 2700, .5): "aluminium", ("steel", 7800, .5): "steel",
    ("lab_blue", 1050, .5): "abs", ("lab_dark", 2700, .5): "aluminium",
}


def surface_of(material):
    """The surface a material's contacts are sourced from, or None."""
    if material.surface is not None:
        return material.surface
    return LEGACY_SURFACES.get((material.id, material.density, material.sliding_friction))


def unsourced(material):
    """A copy that keeps its own friction number, for user-entered coefficients."""
    return replace(material, surface=None)
