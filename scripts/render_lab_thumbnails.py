"""Regenerate original lab-equipment catalog previews (requires MuJoCo/OpenGL)."""
from pathlib import Path
import numpy as np
import mujoco as mj
from PIL import Image
from little_world.assets.catalog import CATALOG
from little_world.core.scene import Scene
from little_world.core.entity import Entity
from little_world.physics.mujoco_backend import MujocoBackend
from little_world.construction.docking import world_bounds


def main():
    out=Path(__file__).resolve().parents[1]/'src/little_world/assets/data'
    for item in CATALOG:
        if not item.variant.startswith('lab_'):continue
        bp=item.blueprint();backend=MujocoBackend()
        try:
            backend.compile(Scene((Entity('machine',bp),)),.002)
            lo,hi=map(np.array,world_bounds(bp));camera=mj.MjvCamera()
            camera.lookat[:]=(lo+hi)/2;camera.distance=float(np.linalg.norm(hi-lo))*1.65
            camera.azimuth=135;camera.elevation=-25
            with mj.Renderer(backend.model,width=432,height=308) as renderer:
                renderer.update_scene(backend.data,camera=camera)
                Image.fromarray(renderer.render()).save(out/(item.id+'.png'))
        finally:backend.close()


if __name__=='__main__':main()
