from dataclasses import replace
import json
import subprocess
import sys
import pytest
from little_world.core.blueprint import Blueprint
from little_world.core.component import Body, Camera, Geometry, Hinge, Motor, Transform
from little_world.core.entity import Entity
from little_world.core.material import Material
from little_world.core.scene import Scene
from little_world.core.state import State
from little_world.core.world import World, Mode
from little_world.physics.backend import PhysicsBackend


def design():
    return Blueprint((Body("block", Geometry("box", (1, 1, 1)), "wood", dynamic=True),),
                     (Material("wood", 600),))


class FakeBackend:
    def compile(self, scene, timestep):
        self.dt = timestep
        self.time = 0
    def snapshot(self):
        return State(self.time, {})
    def step(self, commands):
        self.time += self.dt
        return self.snapshot()
    def reset(self):
        self.time = 0
        return self.snapshot()
    def close(self):
        pass


def test_core_has_no_solver_import():
    subprocess.run([sys.executable, "-c", "import little_world; import sys; assert 'mujoco' not in sys.modules"], check=True)


def test_roundtrip_and_geometry_material_independence():
    bp = design()
    assert Blueprint.from_json(bp.to_json()) == bp
    assert replace(bp, materials=(Material("wood", 900),)).components == bp.components


def test_lifecycle_and_saved_design():
    backend = FakeBackend()
    assert isinstance(backend, PhysicsBackend)
    scene = Scene((Entity("object", design()),))
    with World(backend, scene) as world:
        with pytest.raises(RuntimeError):
            world.step()
        world.start()
        snapshot = world.step()
        assert snapshot.time == .002
        with pytest.raises(RuntimeError):
            world.set_scene(scene)
        assert world.reset().time == 0
        assert world.mode == Mode.BUILD
        assert snapshot.time == .002
        world.set_scene(scene)
        world.start()
        assert world.scene == scene
    with pytest.raises(RuntimeError):
        world.start()


@pytest.mark.parametrize("parts", [
    (Body("a", Geometry("sphere", (1,)), "missing"),),
    (Body("a", Geometry("sphere", (1,)), "wood", parent="b"),),
    (Body("a", Geometry("sphere", (1,)), "wood", parent="a"),),
    (Motor("motor", "missing"),),
    (Camera("camera", "missing"),),
    (Hinge("hinge", "missing"),),
])
def test_invalid_references(parts):
    with pytest.raises(ValueError):
        Blueprint(parts, (Material("wood", 600),))


def test_duplicate_ids_and_versions():
    bp = design()
    with pytest.raises(ValueError):
        replace(bp, components=bp.components * 2)
    with pytest.raises(ValueError):
        Scene((Entity("x", bp), Entity("x", bp)))
    raw = json.loads(bp.to_json())
    raw["version"] = 2
    with pytest.raises(ValueError):
        Blueprint.from_json(json.dumps(raw))


@pytest.mark.parametrize("factory", [lambda: Geometry("box", (-1, 1, 1)),
    lambda: Material("x", float("nan")), lambda: Transform(quaternion=(0, 0, 0, 0)),
    lambda: Hinge("x", "y", axis=(0, 0, 0))])
def test_invalid_physical_values(factory):
    with pytest.raises(ValueError):
        factory()


def test_attachments_controllers_and_all_part_types_roundtrip():
    from little_world.core.blueprint import ControllerSpec
    from little_world.core.component import Attachment
    bp = Blueprint((
        Body("base", Geometry("box", (1, 1, 1)), "wood", dynamic=True,
             attachments=(Attachment("mount", Transform((0, 0, .5))),)),
        Body("wheel", Geometry("cylinder", (.2, .1)), "wood", parent="base"),
        Hinge("hinge", "wheel"), Motor("motor", "hinge"), Camera("camera", "base"),
    ), (Material("wood", 600),), (ControllerSpec("controller", "test", ("motor",)),))
    assert Blueprint.from_json(bp.to_json()) == bp
    with pytest.raises(ValueError):
        replace(bp, controllers=(ControllerSpec("bad", "test", ("absent",)),))


def test_failed_compile_stays_in_build_and_state_is_readonly():
    class FailingBackend(FakeBackend):
        def compile(self, scene, timestep):
            raise ValueError("unsupported")
    world = World(FailingBackend(), Scene(()))
    with pytest.raises(ValueError):
        world.start()
    assert world.mode == Mode.BUILD
    with pytest.raises(TypeError):
        State(0, {}).bodies["x"] = None
    world.close()


def test_preview_compile_is_reused_until_design_changes():
    class CountingBackend(FakeBackend):
        calls = 0
        def compile(self, scene, timestep):
            self.calls += 1
            super().compile(scene, timestep)
    backend = CountingBackend()
    with World(backend, Scene((Entity('a', design()),))) as world:
        world.preview()
        world.preview()
        world.start()
        world.step()
        world.reset()
        world.start()
        assert backend.calls == 1
        world.reset()
        world.set_scene(Scene((Entity('b', design()),)))
        world.start()
        assert backend.calls == 2
