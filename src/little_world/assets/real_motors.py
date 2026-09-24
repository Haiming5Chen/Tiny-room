"""Manufacturer endpoints, checked 2026-09-14. No physical calibration yet."""
from little_world.core.motor_profile import MotorProfile

PROFILES={
    'XH430-W210 / 12 V':MotorProfile('ROBOTIS XH430-W210',12.,2.5,50.,
        'https://emanual.robotis.com/docs/en/dxl/x/xh430-w210/','2026-09-14'),
    'XH430-W350 / 12 V':MotorProfile('ROBOTIS XH430-W350',12.,3.4,30.,
        'https://emanual.robotis.com/docs/en/dxl/x/xh430-w350/','2026-09-14'),
}
