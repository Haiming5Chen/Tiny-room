"""Small inspection/drive window using MuJoCo rendering and GLFW input.

No simulate-app key handler is installed: drive keys cannot toggle debug visuals.
This is a presentation adapter, not a builder or a second simulation architecture.
"""
import os
import sys
import time
import glfw
import mujoco as mj
from .controls import DriveInput


def inspect(world, backend, *, left=None, right=None, seconds=None):
    # Old launch commands used mjpython, which moves Python off the macOS main
    # thread. Our GLFW window must run on the main thread; restart with Python.
    if sys.platform == 'darwin':
        from mujoco import viewer as native_viewer
        if native_viewer._MJPYTHON is not None:
            os.execv(sys.executable, [sys.executable, *sys.argv])
    if not glfw.init():
        raise RuntimeError('Could not initialize GLFW display')
    window = None
    context = None
    try:
        window = glfw.create_window(1100, 760, 'Little World — Drive & Inspect', None, None)
        if not window:
            raise RuntimeError('Could not create Little World window')
        glfw.make_context_current(window)
        glfw.swap_interval(1)
        state = world.start()
        model, data = backend.model, backend.data
        scene = mj.MjvScene(model, maxgeom=10000)
        option = mj.MjvOption()
        camera = mj.MjvCamera()
        context = mj.MjrContext(model, mj.mjtFontScale.mjFONTSCALE_150)
        controls = DriveInput()
        paused = False
        follow = bool(left and right)
        reset_requested = False
        body_id = -1
        channels = []
        if left and right:
            for name in (left, right):
                actuator = model.actuator(name).id
                joint = int(model.actuator_trnid[actuator, 0])
                channels.append((name, int(model.jnt_dofadr[joint]),
                                 float(model.actuator_ctrlrange[actuator, 1])))
            body_id = int(model.jnt_bodyid[int(model.actuator_trnid[model.actuator(left).id, 0])])
            while model.body_parentid[body_id] != 0:
                body_id = int(model.body_parentid[body_id])

        def home():
            camera.type = mj.mjtCamera.mjCAMERA_FREE
            camera.lookat[:] = data.xpos[body_id] if body_id >= 0 else (0, 0, .15)
            camera.distance = 2.2 if body_id >= 0 else 6
            camera.azimuth, camera.elevation = 135, -30

        home()
        keys = {glfw.KEY_W: 'W', glfw.KEY_UP: 'W', glfw.KEY_S: 'S', glfw.KEY_DOWN: 'S',
                glfw.KEY_A: 'A', glfw.KEY_LEFT: 'A', glfw.KEY_D: 'D', glfw.KEY_RIGHT: 'D'}
        pressed_codes = set()

        def clear():
            pressed_codes.clear()
            controls.clear()

        def key_callback(win, key, scancode, action, mods):
            nonlocal paused, follow, reset_requested
            if key in keys:
                if action == glfw.PRESS:
                    pressed_codes.add(key)
                elif action == glfw.RELEASE:
                    pressed_codes.discard(key)
                controls.clear()
                for code in pressed_codes:
                    controls.press(keys[code])
            elif action == glfw.PRESS:
                if key in (glfw.KEY_SPACE, glfw.KEY_X):
                    clear()
                elif key == glfw.KEY_P:
                    paused = not paused
                    clear()
                elif key == glfw.KEY_R:
                    reset_requested = True
                    clear()
                elif key == glfw.KEY_F:
                    follow = not follow and body_id >= 0
                    camera.type = mj.mjtCamera.mjCAMERA_FREE
                elif key == glfw.KEY_C and model.ncam:
                    camera.type = (mj.mjtCamera.mjCAMERA_FREE if camera.type == mj.mjtCamera.mjCAMERA_FIXED
                                   else mj.mjtCamera.mjCAMERA_FIXED)
                    camera.fixedcamid = 0
                elif key == glfw.KEY_HOME:
                    home()
                    follow = body_id >= 0
                elif key == glfw.KEY_ESCAPE:
                    glfw.set_window_should_close(win, True)

        last_mouse = [0., 0.]

        def mouse_move(win, x, y):
            nonlocal follow
            dx, dy = x - last_mouse[0], y - last_mouse[1]
            last_mouse[:] = x, y
            if camera.type == mj.mjtCamera.mjCAMERA_FIXED:
                return
            height = max(glfw.get_window_size(win)[1], 1)
            if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
                action = mj.mjtMouse.mjMOUSE_ROTATE_V
            elif glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS:
                action = mj.mjtMouse.mjMOUSE_MOVE_V
                follow = False
            else:
                return
            mj.mjv_moveCamera(model, action, dx / height, dy / height, scene, camera)

        def scroll(win, x, y):
            if camera.type != mj.mjtCamera.mjCAMERA_FIXED:
                mj.mjv_moveCamera(model, mj.mjtMouse.mjMOUSE_ZOOM, 0, -.05 * y, scene, camera)
                camera.distance = max(.4, min(20., camera.distance))

        glfw.set_key_callback(window, key_callback)
        glfw.set_window_focus_callback(window, lambda win, focused: clear() if not focused else None)
        glfw.set_cursor_pos_callback(window, mouse_move)
        glfw.set_scroll_callback(window, scroll)
        print('Hold WASD/arrows to drive; release to brake. Space/X: brake. P: pause. '
              'R: reset. F: follow. C: onboard camera. Home: restore view. Esc: close.')
        started = previous = time.monotonic()
        accumulator = 0.
        while not glfw.window_should_close(window):
            now = time.monotonic()
            if seconds is not None and now - started >= seconds:
                break
            elapsed = min(now - previous, .1)
            previous = now
            glfw.poll_events()
            if reset_requested:
                return 'reset'
            if glfw.get_window_attrib(window, glfw.ICONIFIED):
                clear()
                accumulator = 0
                time.sleep(.02)
                continue
            if paused:
                accumulator = 0
            else:
                accumulator += elapsed
                while accumulator >= world.timestep:
                    commands = {}
                    for (name, dof, limit), target in zip(channels, controls.targets()):
                        # Bounded wheel-speed feedback: releasing the input applies
                        # physical braking torque; poses/velocities are never forced.
                        commands[name] = max(-limit, min(limit, .3 * (target - data.qvel[dof])))
                    state = world.step(commands)
                    accumulator -= world.timestep
            if follow and camera.type != mj.mjtCamera.mjCAMERA_FIXED:
                camera.lookat[:] = data.xpos[body_id]
            mj.mjv_updateScene(model, data, option, None, camera, mj.mjtCatBit.mjCAT_ALL, scene)
            width, height = glfw.get_framebuffer_size(window)
            if width and height:
                viewport = mj.MjrRect(0, 0, width, height)
                mj.mjr_render(viewport, scene, context)
                mode = 'PAUSED' if paused else 'RUNNING'
                view = 'ONBOARD' if camera.type == mj.mjtCamera.mjCAMERA_FIXED else ('FOLLOW' if follow else 'FREE')
                mj.mjr_overlay(mj.mjtFont.mjFONT_NORMAL, mj.mjtGridPos.mjGRID_TOPLEFT, viewport,
                               f'Little World | {mode} | {view} | {state.time:.1f}s',
                               'Hold WASD / arrows: drive   Release: brake\nSpace: brake   P: pause   R: reset\nF: follow   C: camera   Home: restore view\nMouse drag: orbit   Right drag: pan   Scroll: zoom', context)
                glfw.swap_buffers(window)
            time.sleep(.001)
        return 'closed'
    finally:
        if context is not None:
            context.free()
        if window is not None:
            glfw.destroy_window(window)
        glfw.terminate()
        # Ending an inspection returns to the saved design, including reset.
        from little_world.core.world import Mode
        if world.mode == Mode.SIMULATE:
            world.reset()
