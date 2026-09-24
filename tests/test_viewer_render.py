"""Actual GLFW window regression, opt-in alongside the RGB camera tests."""
import os
import pytest
pytest.importorskip('mujoco')
pytestmark = pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER') != '1',
                                reason='requires a display and OpenGL')


def test_drive_keys_do_not_change_rendering_and_reset(monkeypatch):
    import glfw
    import mujoco as mj
    import numpy as np
    from little_world import Entity, World
    from little_world.core.scene import Scene
    from little_world.core.world import Mode
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.robots.two_wheel import two_wheel_blueprint
    from little_world.scenes.room import room_entity
    from little_world.ui.viewer import inspect

    callbacks = {}
    set_key = glfw.set_key_callback
    poll = glfw.poll_events
    render = mj.mjr_render
    frames = []
    ticks = 0

    def register(window, callback):
        callbacks['key'] = callback
        callbacks['window'] = window
        return set_key(window, callback)

    events = {2: (glfw.KEY_W, glfw.PRESS), 12: (glfw.KEY_W, glfw.RELEASE),
              13: (glfw.KEY_A, glfw.PRESS), 23: (glfw.KEY_A, glfw.RELEASE),
              24: (glfw.KEY_D, glfw.PRESS), 34: (glfw.KEY_D, glfw.RELEASE),
              35: (glfw.KEY_S, glfw.PRESS), 45: (glfw.KEY_S, glfw.RELEASE),
              46: (glfw.KEY_P, glfw.PRESS), 48: (glfw.KEY_P, glfw.PRESS),
              50: (glfw.KEY_R, glfw.PRESS)}

    def poll_and_type():
        nonlocal ticks
        poll()
        ticks += 1
        if ticks in events:
            key, action = events[ticks]
            callbacks['key'](callbacks['window'], key, 0, action, 0)

    def verify_render(viewport, scene, context):
        assert not scene.flags[mj.mjtRndFlag.mjRND_WIREFRAME]
        assert not scene.flags[mj.mjtRndFlag.mjRND_SEGMENT]
        assert not scene.flags[mj.mjtRndFlag.mjRND_IDCOLOR]
        render(viewport, scene, context)
        if ticks in (3, 14, 25, 36):
            rgb = np.zeros((viewport.height, viewport.width, 3), dtype=np.uint8)
            mj.mjr_readPixels(rgb, None, viewport, context)
            assert rgb.mean() > 10  # catches an empty/black drive view
            frames.append(scene.ngeom)

    monkeypatch.setattr(glfw, 'set_key_callback', register)
    monkeypatch.setattr(glfw, 'poll_events', poll_and_type)
    monkeypatch.setattr(mj, 'mjr_render', verify_render)
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity('robot', two_wheel_blueprint())))) as world:
        assert inspect(world, backend, left='robot/left_motor', right='robot/right_motor', seconds=10) == 'reset'
        assert world.mode == Mode.BUILD
        assert backend.snapshot().time == 0
    assert len(frames) == 4 and len(set(frames)) == 1
