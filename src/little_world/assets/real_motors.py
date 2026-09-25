"""Manufacturer endpoints. No physical calibration yet.

ROBOTIS values checked 2026-09-14. Pololu 37D values checked 2026-09-25 at the 37D
category comparison table and the 30:1 product page: every 12 V ratio shares 0.2 A
no-load and 5.5 A stall current; stall torques and currents are, in Pololu's words,
"theoretical extrapolations; units will typically stall well before these points as
the motors heat up". Pololu recommends at most 10 kg-cm continuously on the 30:1.
"""
from little_world.core.motor_profile import MotorProfile

KGCM = 9.80665e-2  # N m per kg-cm
POLOLU_37D = 'https://www.pololu.com/category/116/37d-metal-gearmotors'

PROFILES={
    'XH430-W210 / 12 V':MotorProfile('ROBOTIS XH430-W210',12.,2.5,50.,
        'https://emanual.robotis.com/docs/en/dxl/x/xh430-w210/','2026-09-14'),
    'XH430-W350 / 12 V':MotorProfile('ROBOTIS XH430-W350',12.,3.4,30.,
        'https://emanual.robotis.com/docs/en/dxl/x/xh430-w350/','2026-09-14'),
}
for ratio, rpm, kgcm in (('6.3',1600,3.0),('10',1000,4.9),('19',530,8.5),('30',330,14.),
                         ('50',200,21.),('70',150,27.),('100',100,34.),('131',76,45.),
                         ('150',67,49.)):
    PROFILES[f'Pololu 37D {ratio}:1 / 12 V']=MotorProfile(
        f'Pololu 37D {ratio}:1 metal gearmotor',12.,round(kgcm*KGCM,4),float(rpm),
        POLOLU_37D,'2026-09-25','dc_friction_v1',.2,5.5)

# The kit's 37 mm gearmotor is modelled on the Pololu 37D (THIRD_PARTY.md); 30:1 is
# the ratio whose free speed suits the kit's 100 mm tread wheel (1.7 m/s).
KIT_GEARMOTOR = 'Pololu 37D 30:1 / 12 V'
