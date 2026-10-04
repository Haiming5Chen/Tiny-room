"""A program goes back to a stop it was pushed off (ADR 0031, OPEN LW-019).

Shoved 6 N s once stopped at the table, the arm on a cart ended 3.7 to 11.8 cm from its stop
and fetched its cube in 3 of 9 set-ups: aimed from there, the arm worked at the edge of its
reach (ADR 0030). These are the runner's rules for going back, with joints that go where
they are sent and a base that is wherever the test puts it.
"""
import pytest

from little_world.programming.program import REAPPROACH, RUN_UP, Block, Program, Runner

ABOVE = Block('pose', value=30., duration=2., angles=(('arm', (10.,)),))                  # driven in
STOP = Block('goto', value=.01, duration=60., point=(1.6, 0., 0.))                       # facing +X
AT = Block('pose', value=30., duration=2., angles=(('arm', (40.,)),), point=(1.84, 0., .14))
FETCH = Program((ABOVE, STOP, AT))


class Machine:
    """Joints that arrive at once; a base the test moves by hand."""

    def __init__(self):
        self.angles = {'arm': (10.,)}
        self.base = (1.6, 0., 0.)

    def tick(self, runner, aim=lambda point, pose: None):
        out = runner.tick(.01, self.angles, base=self.base, aim=aim)
        if out['pose']:
            self.angles = dict(out['pose'])
        return out


def at_the_stop(runner, machine):
    """Run until the aimed pose is under way at the stop."""
    for _ in range(500):
        machine.tick(runner)
        if runner.index == 2:
            return
    raise AssertionError('never reached the aimed pose')


def test_a_machine_pushed_off_its_stop_goes_back_the_way_it_came():
    runner, machine = Runner(), Machine()
    runner.start(FETCH)
    at_the_stop(runner, machine)
    assert runner.stop_at == (1.6, 0.)
    machine.base = (1.6, .05, .1)                      # shoved 5 cm to its left during the pose
    for _ in range(300):
        machine.tick(runner)
        if runner.retries:
            break
    assert runner.retries == 1 and runner.index == 0 and runner.message == 'Pushed 5 cm off its stop: going back'
    assert runner.run_up == pytest.approx((1.6 - RUN_UP, 0.))      # backs off along the stop's heading
    for _ in range(300):                                            # the pose it drove in, then the drive
        out = machine.tick(runner)
        if runner.index == 1 and out['base']:
            break
    assert runner.driver.goal == pytest.approx((1.6 - RUN_UP, 0.)) and out['base'] != (0., 0.)
    machine.base = (1.6 - RUN_UP, 0., 0.)                           # backed off
    machine.tick(runner)
    assert runner.run_up is None and runner.index == 1               # now in to the stop itself
    machine.base = (1.6, 0., 0.)
    for _ in range(500):
        machine.tick(runner)
        if runner.state != 'running':
            break
    assert runner.state == 'completed' and runner.retries == 1


def test_within_its_stop_or_out_of_retries_the_pose_stands():
    for base, retries in (((1.6, REAPPROACH * .9, 0.), 1), ((1.6, .05, 0.), 0)):
        runner, machine = Runner(retries=retries), Machine()
        runner.start(FETCH)
        at_the_stop(runner, machine)
        machine.base = base
        for _ in range(500):
            machine.tick(runner)
            if runner.state != 'running':
                break
        assert runner.state == 'completed' and runner.retries == 0, (base, retries)


def test_a_pose_that_cannot_settle_off_its_stop_goes_back_instead_of_failing():
    runner, machine = Runner(), Machine()
    runner.start(FETCH)
    at_the_stop(runner, machine)
    machine.base = (1.6, -.04, 0.)
    for _ in range(600):                        # the arm is blocked: its joints never move
        runner.tick(.01, {'arm': (10.,)}, base=machine.base, aim=lambda point, pose: None)
        if runner.retries or runner.state != 'running':
            break
    assert runner.state == 'running' and runner.retries == 1 and runner.index == 0
    with pytest.raises(ValueError):
        Runner(retries=-1)


def test_a_cart_shoved_6_N_s_at_the_table_goes_back_and_fetches_its_cube():
    """Measured, set-up 'repeat 2' of the Fetch sweep: shoved 8 cm, the cart's lift stopped
    just short of the field's 5 cm line and the run failed (ADR 0030). Going back, it meets
    every goal. The program as measured then, before it looked for the cube (ADR 0032)."""
    pytest.importorskip('mujoco')
    from little_world.fields.disturbance import DEFAULTS
    from little_world.fields.variation import payload_site
    from little_world.inventory.sweep import design, ranges_for, run, setups, solve
    variations = setups(ranges_for('fetch'))
    bp = design('mobile_manipulator')
    site = payload_site(bp, max(v.payload for v in variations))
    setup = next(v for v in variations if v.label == 'repeat 2')
    back = run('fetch', bp, setup, solve('fetch', bp, look=False), site=site, disturbance=DEFAULTS['fetch'][1])
    assert back.went_back == 1 and all(x.status in ('met', 'kept') for x in back.results), back.results
