from dataclasses import dataclass
from math import isfinite
from .component import positive, vector


@dataclass(frozen=True)
class Material:
    id: str
    density: float
    sliding_friction: float = 0.8
    rgba: tuple = (0.6, 0.6, 0.6, 1.)

    texture: str | None = None
    roughness: float = .6
    # Named real-world surface for sourced PAIR friction (materials/contact_pairs.py).
    # None keeps the illustrative sliding_friction above and MuJoCo's own combination.
    surface: str | None = None

    def __post_init__(self):
        positive(self.density, "density")
        if self.surface is not None and (not isinstance(self.surface, str) or not self.surface.isidentifier()):
            raise ValueError("surface must be a surface ID such as 'rubber', or None")
        if self.texture is not None and (not isinstance(self.texture,str) or not self.texture):
            raise ValueError("texture must be a nonempty asset ID or None")
        if not isfinite(self.roughness) or not 0 <= self.roughness <= 1:
            raise ValueError("roughness must be in [0, 1]")
        if not isfinite(self.sliding_friction) or self.sliding_friction < 0:
            raise ValueError("friction must be finite and nonnegative")
        color = vector(self.rgba, 4, "rgba")
        if any(not 0 <= x <= 1 for x in color):
            raise ValueError("RGBA must be in [0, 1]")
        object.__setattr__(self, "rgba", color)
