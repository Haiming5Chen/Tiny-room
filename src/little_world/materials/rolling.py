"""Rolling resistance of wheel treads, as the lever arm of the floor's reaction.

A rolling tread deforms, and the floor's reaction ends up a little ahead of the point
under the axle. That offset, b, turns the wheel's load N into a torque b * N that
opposes rolling - independent of wheel radius, which is why b (a length) is the
number manufacturers publish, and why the equivalent force F = b * N / r is larger
for small wheels. MuJoCo's own rolling friction needs condim 6 and was never enabled
here (every geom is condim 4); the adapter applies b * N at the wheel's hinge instead,
with N taken from the contact the solver has just computed.

Standard library only.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RollingLoss:
    lever_arm: float  # b, metres
    source: str
    confidence: str
    basis: str
    note: str


HAMILTON = ("Hamilton Caster & Mfg. Co., 'Rolling Resistance and Industrial Wheels', "
            "White Paper No. 11; F = f * W / R with f in inches")
HAMILTON_URL = "https://www.hamiltoncaster.com/Portals/0/blog/White%20Paper%20Rolling%20Resistance.pdf"

ROLLING = {
    "steel": RollingLoss(
        .019 * .0254, HAMILTON, "medium", "measured",
        "Forged steel wheel, the lowest coefficient in Hamilton's comparison: 0.019 in."),
    "rubber": RollingLoss(
        .047 * .0254, HAMILTON, "low", "analogue",
        "No published rubber value was found. Uses Hamilton's 85A polyurethane on a steel "
        "floor (0.047 in; 8 in wheel, 1200 lb, 3 mph). Softer rubber rolls harder - "
        "Hamilton ranks the softest rubber highest - so this understates rubber on that "
        "count; the test load is about fifty times a kit wheel's and hysteresis loss "
        "grows with contact width, which pulls the other way."),
}


def lever_arm(surface):
    """b in metres for a tread surface, or 0.0 when no source covers it."""
    loss = ROLLING.get(surface)
    return 0.0 if loss is None else loss.lever_arm
