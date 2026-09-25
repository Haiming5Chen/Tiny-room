"""Running a program against a position controller: the same steps in the window, in
the inventory's trials and headless (ADR 0016). Standard library; the controller is
duck-typed (specs, display_position, set_position_target)."""


def joint_angles(control):
    """Joint action -> its actuators' current positions, as the runner reads them."""
    return {s.id: tuple(control.display_position(a)[0] for a in s.actuators) for s in control.specs}


def apply(output, control):
    """Hand one runner output to the controller: targets for moves and poses. Returns the
    keys an action block holds down this step."""
    specs = {s.id: s for s in control.specs}
    keys = set()
    if output.get('action'):
        name, direction = output['action']
        spec = specs[name]
        keys.add(spec.positive_key if direction == 1 else spec.negative_key)
    if output.get('move'):
        name, angle = output['move']
        for actuator in specs[name].actuators:
            control.set_position_target(actuator, angle)
    for name, values in (output.get('pose') or {}).items():
        for actuator, value in zip(specs[name].actuators, values):
            control.set_position_target(actuator, value)
    return keys


def needs_grasp(program):
    return any(b.kind == 'grasp' for b in program.blocks)
