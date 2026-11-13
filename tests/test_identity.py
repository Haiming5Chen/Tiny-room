"""Contracts for the set-up fingerprints (FR-041, ADR 0075): each run says which start it began from,
and a paired statistic checks that both of a pair's runs began from the same one.

The defect: pairs were matched by their draws' labels ('repeat 12'), and a label names a draw, not a
start - a scratch driver once drew the same labels with the payload placed elsewhere (`site=None`,
ADR 0052), and nothing would have said its pairs were not pairs.
"""
import json
from dataclasses import asdict

import pytest

from little_world.inventory.identity import Fingerprint, check, differ, from_dict

A = Fingerprint('3.10.0', ('m1', 'r1'), ('s1', 't1'), ('u1', 'v1'), 'p1', 'd1')


def test_two_starts_differ_in_the_parts_named_and_a_named_factor_may_differ():
    B = Fingerprint('3.10.0', ('m2', 'r1'), ('s1', 't1'), ('u2', 'v1'), 'p2', 'd1')
    assert differ(A, A) == () and differ(A, B) == ('model', 'settled', 'program')
    assert differ(A, B, 'rounded') == ('program',), "the same to six figures: alike, rounded"
    assert differ(A, B, 'rounded', factor=('program',)) == ()
    verified = check([('repeat 1', A, A), ('repeat 2', A, B), ('repeat 3', A, None)])
    assert (verified.pairs, verified.same, verified.unknown) == (3, 1, 1) and not verified.clean
    assert verified.line() == ('Set-ups verified: 1 of 3 pairs began from the same start, exact. Not the same start: '
                               'repeat 2: model, settled, program - read those pairs as two runs. 1 without a fingerprint.')
    assert check([('repeat 1', None, None)]).line() == "Set-ups verified: not - the 1 pairs' runs were recorded without fingerprints."
    assert len(A.code()) == 8 and A.code() != A.code('rounded') and from_dict(json.loads(json.dumps(asdict(A)))) == A


def test_the_backend_digests_the_same_model_alike_and_tells_a_part_made_heavier():
    pytest.importorskip('mujoco')
    from little_world import Entity, World
    from little_world.fields import FIELDS
    from little_world.physics.mujoco_backend import MujocoBackend
    from little_world.robots.mobile_platform import mobile_platform_blueprint
    seen = []
    for heavier in (1., 1. + 1e-12, 1.01):
        backend = MujocoBackend()
        with World(backend, FIELDS['curbs'].scene(Entity('machine', mobile_platform_blueprint()))) as world:
            world.start()
            if heavier != 1.:
                backend.scale_mass('machine/rail_right', heavier)
            seen.append(backend.digests())
    same, nudged, heavier = seen
    assert nudged['model'][0] != same['model'][0] and nudged['model'][1] == same['model'][1], "exact tells 1e-12; rounded does not"
    assert heavier['model'][1] != same['model'][1] and heavier['state'] == same['state'], "1 % heavier, at the same pose"


def test_the_payload_placed_elsewhere_is_flagged_and_a_disturbance_or_a_squeeze_is_not():
    """ADR 0052's slip, reproduced: the same label, the payload where its own mass puts it rather than the
    sweep's shared site - another start. A disturbance comes after the start; a program set to squeeze by
    current is the factor its study names."""
    pytest.importorskip('mujoco')
    from little_world.control.tool_motion import squeezed
    from little_world.fields.disturbance import DEFAULTS
    from little_world.fields.variation import plan
    from little_world.inventory import sweep
    from little_world.robots.mobile_manipulator import mobile_manipulator_blueprint
    bp = mobile_manipulator_blueprint()
    drawn = plan(sweep.ranges_for('fetch'), samples=59, seed=1)
    site = sweep.shared_site(bp, drawn)
    v = next(v for v in drawn if 0 < v.payload < max(d.payload for d in drawn))
    program = sweep.solve('fetch', bp)
    own = sweep.run('fetch', bp, v, program, site, until_start=True).fingerprint
    assert sweep.run('fetch', bp, v, program, site, until_start=True).fingerprint == own, "the same start, to the bit"
    slipped = sweep.run('fetch', bp, v, program, None, until_start=True).fingerprint
    assert set(differ(own, slipped)) >= {'model', 'settled'} and not check([(v.label, own, slipped)]).clean
    moved = sweep.run('fetch', bp, v, program, site, disturbance=DEFAULTS['fetch'][3], until_start=True).fingerprint
    assert differ(own, moved) == ()
    firm = sweep.run('fetch', bp, v, squeezed(program, 7.), site, until_start=True).fingerprint
    assert differ(own, firm) == ('program',) and check([(v.label, own, firm)], factor=('program',)).clean
