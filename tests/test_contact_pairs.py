"""Contracts for sourced pair friction (ADR 0010).

The headline defect this exists for: a 'skid' material of 0.01 on a 0.8 floor slid at
0.8, because MuJoCo combines two geoms' coefficients with max(). The two-wheel robot
could not move at 0.2 Nm - 2 cm in four seconds - while its skids dragged at the
floor's friction.
"""
from dataclasses import replace
import json
import math
import pytest

from little_world import Blueprint, Entity
from little_world.components import box, Transform
from little_world.core.material import Material
from little_world.materials import (FLOOR, METAL, PLASTIC, RUBBER, SKID, WOOD,
                                    LEGACY_SURFACES, surface_of)
from little_world.materials import contact_pairs as cp


# -- the table itself: data contracts, no solver needed ----------------------------------

def test_every_pair_is_sourced_bounded_and_labelled():
    assert cp.PAIRS, "the table is empty"
    for (a, b), p in cp.PAIRS.items():
        assert a <= b, "keys are sorted so every pair has exactly one entry"
        assert a in cp.SURFACES and b in cp.SURFACES
        assert 0 < p.kinetic < 2 and (p.static is None or 0 < p.static < 2)
        assert p.confidence in cp.CONFIDENCE and p.basis in cp.BASIS
        assert p.sources and all(s in cp.SOURCES for s in p.sources)
        assert len(p.note) > 20, "every value carries the spread or conditions behind it"
        if p.basis == "analogue":
            assert p.confidence == "low", "an analogue is never better than low confidence"
    for src in cp.SOURCES.values():
        assert src.url.startswith("https://") and src.citation and src.checked


def test_lookup_is_symmetric_and_silent_about_what_it_does_not_know():
    assert cp.lookup("rubber", "concrete") is cp.lookup("concrete", "rubber")
    assert cp.lookup("rubber", "concrete").kinetic == .95
    assert cp.lookup("abs", "concrete") is None, "no source, no value"
    assert cp.lookup(None, "rubber") is None
    with pytest.raises(ValueError, match="Unknown contact surface"):
        cp.validate_surface("plaster")


def test_fingerprint_follows_the_values():
    before = cp.fingerprint()
    key = ("concrete", "rubber")
    original = cp.PAIRS[key]
    try:
        cp.PAIRS[key] = replace(original, kinetic=.94)
        assert cp.fingerprint() != before
    finally:
        cp.PAIRS[key] = original
    assert cp.fingerprint() == before
    assert "rubber / concrete" not in cp.markdown_table()  # keys print sorted
    assert "concrete / rubber | 0.95" in cp.markdown_table()


# -- materials and saved designs ---------------------------------------------------------

def test_material_surface_roundtrips_and_old_designs_still_load():
    bp = Blueprint((box("b", (.1, .1, .1), "rubber", dynamic=True),), (RUBBER,))
    again = Blueprint.from_json(bp.to_json())
    assert again.materials[0].surface == "rubber"
    old = json.loads(bp.to_json())
    del old["materials"][0]["surface"]
    legacy = Blueprint.from_json(json.dumps(old))
    assert legacy.materials[0].surface is None
    with pytest.raises(ValueError):
        Material("x", 1000, .5, surface="not a surface id")


def test_library_materials_name_their_surfaces():
    assert (WOOD.surface, METAL.surface, RUBBER.surface, FLOOR.surface, SKID.surface,
            PLASTIC.surface) == ("wood", "aluminium", "rubber", "concrete", "ptfe", "abs")
    from little_world.assets.hardware import COPPER, STEEL
    from little_world.assets.lab_equipment import CARTON
    assert STEEL.surface == "steel", "a replace() of METAL must not stay aluminium"
    assert COPPER.surface is None and CARTON.surface is None


def test_legacy_library_materials_are_recognised_and_edited_ones_are_not():
    for (mid, density, mu), surface in LEGACY_SURFACES.items():
        assert surface in cp.SURFACES
        assert surface_of(Material(mid, density, mu)) == surface
    assert surface_of(Material("rubber", 1100, .9)) is None, "user-edited friction stays theirs"
    assert surface_of(Material("custom", 1100, 1.2, surface="ptfe")) == "ptfe"


def test_custom_gripper_friction_is_not_overridden_by_the_table():
    from little_world.construction.editor import AssemblyEditor
    from little_world.robots.arm_lab import arm_lab_blueprint
    editor = AssemblyEditor(arm_lab_blueprint())
    editor.select("two_finger_gripper_1_finger_left_pad")
    editor.configure_gripper("flat", "rubber", 1.2, .3, .05)
    kept = next(m for m in editor.blueprint.materials if m.id.endswith("_contact"))
    assert kept.surface == "rubber", "the untouched library value is still sourced rubber"
    editor.configure_gripper("flat", "rubber", .45, .3, .05)
    typed = next(m for m in editor.blueprint.materials if m.id.endswith("_contact"))
    assert typed.surface is None and typed.sliding_friction == .45


# -- the adapter --------------------------------------------------------------------------

mujoco = pytest.importorskip("mujoco")
from little_world import World  # noqa: E402
from little_world.core.scene import Scene  # noqa: E402
from little_world.physics.mujoco_backend import MujocoBackend  # noqa: E402
from little_world.robots.two_wheel import two_wheel_blueprint  # noqa: E402
from little_world.scenes.room import room_entity  # noqa: E402


def _contacts(backend):
    m, d = backend.model, backend.data
    out = {}
    for i in range(d.ncon):
        c = d.contact[i]
        names = tuple(sorted((m.geom(c.geom1).name, m.geom(c.geom2).name)))
        out[names] = float(c.friction[0])
    return out


def test_the_staged_step_is_bit_identical_to_mj_step_when_nothing_is_sourced():
    """Contact policy runs inside a staged copy of mj_step. With every material
    unsourced it must change nothing at all - not approximately nothing."""
    # Unsourced on purpose: surface=None, and friction nudged by 1e-9 so the legacy
    # library match (exact id, density and friction) cannot recognise them either.
    room = room_entity()
    room = Entity(room.id, replace(room.blueprint, materials=tuple(
        replace(m, sliding_friction=m.sliding_friction + 1e-9, surface=None)
        for m in room.blueprint.materials)))
    robot = Entity("robot", two_wheel_blueprint())
    robot = Entity("robot", replace(robot.blueprint, materials=tuple(
        replace(m, sliding_friction=m.sliding_friction + 1e-9, surface=None)
        for m in robot.blueprint.materials)))
    backend = MujocoBackend()
    with World(backend, Scene((room, robot))) as world:
        world.start()
        m = backend.model
        reference = mujoco.MjData(m)
        reference.qpos[:] = backend.data.qpos
        reference.ctrl[:] = 0
        mujoco.mj_forward(m, reference)
        for k in range(600):
            u = .6 * math.sin(k / 40)
            world.step({"robot/left_motor": u, "robot/right_motor": -u / 2})
            reference.ctrl[:] = backend.data.ctrl
            mujoco.mj_step(m, reference)
        assert (backend.data.qpos == reference.qpos).all()
        assert (backend.data.qvel == reference.qvel).all()


def test_contacts_use_the_sourced_pair_and_unsourced_ones_keep_mujoco():
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("robot", two_wheel_blueprint())))) as world:
        world.start()
        for _ in range(400):
            world.step({})
        seen = _contacts(backend)
    wheel = [mu for names, mu in seen.items() if "wheel" in "".join(names) and "floor" in "".join(names)]
    assert wheel and all(mu == cp.lookup("rubber", "concrete").kinetic for mu in wheel)
    # A surface with no sourced pair against rubber: the room's wooden obstacle is
    # sourced, so build an explicit unsourced one - a copper block on the floor.
    copper = Material("copper", 8900, .33)
    block = Entity("block", Blueprint((box("body", (.1, .1, .1), "copper", dynamic=True,
                                           transform=Transform((1, 1, .06))),), (copper,)))
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), block))) as world:
        world.start()
        for _ in range(200):
            world.step({})
        mus = set(_contacts(backend).values())
    assert mus == {max(.33, FLOOR.sliding_friction)}, "unsourced: MuJoCo's own max()"


def test_skids_skid_now():
    """0.2 Nm per wheel. Before: 0.02 m in 4 s, the skids pinned at the floor's 0.8."""
    backend = MujocoBackend()
    with World(backend, Scene((room_entity(), Entity("robot", two_wheel_blueprint())))) as world:
        world.start()
        x0 = backend.data.body("robot/chassis").xpos[0]
        for _ in range(2000):
            world.step({"robot/left_motor": .2, "robot/right_motor": .2})
        travelled = backend.data.body("robot/chassis").xpos[0] - x0
    assert travelled > .5


def _incline(angle_deg, surface="wood"):
    """A wooden block resting on a fixed plank tilted about Y; returns metres slid in 1 s."""
    a = math.radians(angle_deg)
    q = (math.cos(a / 2), 0., math.sin(a / 2), 0.)
    mat = Material("m", 600, .6, surface=surface)
    # The block sits 3 cm above the plank's centre, measured along the plank normal.
    n = (math.sin(a), 0., math.cos(a))
    centre = (0., 0., .5)
    lift = .01 + .025 + .0005
    pos = tuple(c + lift * k for c, k in zip(centre, n))
    parts = (box("plank", (1., .4, .02), "m", transform=Transform(centre, q)),)
    block = (box("block", (.08, .08, .05), "m", dynamic=True, transform=Transform(pos, q)),)
    backend = MujocoBackend()
    scene = Scene((Entity("ramp", Blueprint(parts, (mat,))), Entity("load", Blueprint(block, (mat,)))))
    with World(backend, scene) as world:
        world.start()
        for _ in range(50):
            world.step({})
        start = backend.data.body("load/block").xpos.copy()
        for _ in range(500):
            world.step({})
        return float(((backend.data.body("load/block").xpos - start) ** 2).sum() ** .5)


def test_a_block_holds_below_its_friction_angle_and_slides_above_it():
    mu = cp.lookup("wood", "wood").kinetic
    limit = math.degrees(math.atan(mu))          # 19.8 degrees for wood on wood
    assert _incline(limit - 6) < .005
    assert _incline(limit + 6) > .05


def test_contact_table_is_part_of_the_trial_environment():
    from little_world.inventory.benchmark import environment_fingerprint
    before = environment_fingerprint()
    key = ("concrete", "rubber")
    original = cp.PAIRS[key]
    try:
        cp.PAIRS[key] = replace(original, kinetic=.9)
        assert environment_fingerprint() != before, "stored comparisons must go stale"
    finally:
        cp.PAIRS[key] = original


def test_the_reference_page_is_generated_from_the_table():
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    done = subprocess.run([sys.executable, str(root / "scripts" / "contact_pairs_doc.py"), "--check"])
    assert done.returncode == 0, "run scripts/contact_pairs_doc.py to regenerate docs/CONTACT_PAIRS.md"
