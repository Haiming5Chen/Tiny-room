"""Cached RGB surface assets for the lightweight renderer.

Wood assets are CC0 Poly Haven images (data/SOURCES.json); the other patterns
are procedural. These are appearance assets, not measured physical roughness
or geometric tire tread.
"""
from functools import lru_cache
import numpy as np

TEXTURES=('wood_grain','brushed_metal','rubber_tread','matte_plastic','wood_floor')
SIZE=512


@lru_cache(maxsize=5)
def texture_bytes(name):
    if name in ('wood_grain','wood_floor'):
        import gzip
        from importlib.resources import files
        return gzip.decompress(files('little_world.assets').joinpath('data',name+'.rgb.gz').read_bytes())
    rng=np.random.default_rng(47)
    y,x=np.mgrid[0:SIZE,0:SIZE]/SIZE
    noise=rng.uniform(-1,1,(SIZE,SIZE))
    if name=='brushed_metal':
        grain=rng.uniform(-1,1,(SIZE,1))
        value=.91+.035*grain+.018*noise+.02*np.cos(2*np.pi*x)
    elif name=='rubber_tread':
        groove=((x+.35*np.abs(np.sin(2*np.pi*y))) * 12)%1 < .22
        value=np.where(groove,.46,.91)+.045*noise
    elif name=='matte_plastic':
        value=.92+.055*noise
    else:
        raise ValueError(f'Unknown surface texture: {name}')
    rgb=np.repeat((np.clip(value,0,1)*255).astype(np.uint8)[...,None],3,axis=2)
    return rgb.tobytes()
