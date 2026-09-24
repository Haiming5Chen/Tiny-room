from dataclasses import replace
import math
import pytest
pytest.importorskip("mujoco")
from little_world import Blueprint, Entity, World
from little_world.components import box, Transform
from little_world.core.scene import Scene
from little_world.materials import WOOD
from little_world.physics.mujoco_backend import MujocoBackend
from little_world.robots.two_wheel import two_wheel_blueprint
from little_world.scenes.room import room_entity


def robot_scene():
    bp = Blueprint.from_json(two_wheel_blueprint().to_json())
    return Scene((room_entity(), Entity("robot", bp)))


def test_fall_and_contact():
    block = Entity("block", Blueprint((box("body", (.1, .1, .1), "wood", dynamic=True,
                   transform=Transform((0, 0, 1))),), (WOOD,)))
    with World(MujocoBackend(), Scene((room_entity(), block))) as world:
        world.start()
        for _ in range(1000):
            state = world.step()
        assert abs(state.bodies["block/body"].pose.position[2] - .05) < .005


def test_drive_turn_reset_and_namespacing():
    backend = MujocoBackend()
    with World(backend, robot_scene()) as world:
        initial = world.start()
        assert backend.model.nu == 2 and backend.model.ncam == 1
        for _ in range(1000):
            state = world.step({"robot/left_motor": .5, "robot/right_motor": .5})
        assert state.bodies["robot/chassis"].pose.position[0] > .1
        assert all(math.isfinite(x) for b in state.bodies.values() for x in b.pose.position)
        assert world.reset() == initial
        world.start()
        for _ in range(1000):
            turned = world.step({"robot/left_motor": -.5, "robot/right_motor": .5})
        assert abs(turned.bodies["robot/chassis"].pose.quaternion[3]) > .1


def test_commands_validate_before_mutating_state():
    backend = MujocoBackend()
    with World(backend, robot_scene()) as world:
        world.start()
        for commands in ({"oops": 1}, {"robot/left_motor": float("nan")}, {"robot/right_motor": 10}):
            with pytest.raises(ValueError):
                world.step(commands)
            assert backend.snapshot().time == 0
        world.step({"robot/left_motor": .1})
        world.step()
        assert not backend.data.ctrl.any()


def test_repeat_instantiation_and_parent_order():
    bp = two_wheel_blueprint()
    bp = replace(bp, components=tuple(reversed(bp.components)))
    scene = Scene((room_entity(), Entity("a", bp), Entity("b", bp, Transform((0, 1, 0)))))
    backend = MujocoBackend()
    with World(backend, scene) as world:
        state = world.start()
        assert backend.model.nu == 4
        assert abs(state.bodies["b/chassis"].pose.position[1] - 1) < 1e-9


def test_static_observation_cache_preserves_moving_welded_children():
    backend = MujocoBackend()
    with World(backend, robot_scene()) as world:
        first = world.start()
        for _ in range(500):
            last = world.step({'robot/left_motor': .5, 'robot/right_motor': .5})
        assert last.bodies['room/floor'] is first.bodies['room/floor']
        assert last.bodies['robot/front_skid'].pose != first.bodies['robot/front_skid'].pose
        world.reset()
        from little_world.core.component import Transform
        replacement = Scene((Entity('room', room_entity().blueprint, Transform((0,0,1))),))
        world.set_scene(replacement)
        changed = world.start()
        assert changed.bodies['room/floor'].pose.position[2] == pytest.approx(.95)


def test_deferred_body_observations_are_detached_and_match_native_velocity():
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    from little_world import World,Entity
    from little_world.core.scene import Scene
    from little_world.physics.mujoco_backend import MujocoBackend
    import numpy as np
    import mujoco as mj
    backend=MujocoBackend()
    with World(backend,Scene((Entity('test',mobile_platform_blueprint()),))) as world:
        first=world.start()
        name='test/root'
        # Do not read this pose until after subsequent native integration.
        initial=backend.data.xpos[backend.model.body(name).id].copy()
        backend.data.qvel[:]=np.linspace(-.5,.7,backend.model.nv)
        for _ in range(4): last=world.step()
        assert first.bodies[name].pose.position==pytest.approx(initial)
        for name in last.bodies:
            v=np.zeros(6)
            mj.mj_objectVelocity(backend.model,backend.data,mj.mjtObj.mjOBJ_BODY,backend.model.body(name).id,v,0)
            observed=last.bodies[name]
            assert observed.linear_velocity==pytest.approx(v[3:])
            assert observed.angular_velocity==pytest.approx(v[:3])
        with pytest.raises(TypeError):
            last.bodies[name]=last.bodies[name]


def test_step_observations_match_full_forward_refresh():
    import mujoco as mj
    import numpy as np
    backend=MujocoBackend()
    with World(backend,robot_scene()) as world:
        world.start()
        for _ in range(100):
            state=world.step({'robot/left_motor':.2,'robot/right_motor':-.1})
        before=[getattr(backend.data,k).copy() for k in ('xpos','xquat','geom_xpos','cam_xpos','cam_xmat','cvel')]
        mj.mj_forward(backend.model,backend.data)
        for key,values in zip(('xpos','xquat','geom_xpos','cam_xpos','cam_xmat','cvel'),before):
            assert np.allclose(values,getattr(backend.data,key))
