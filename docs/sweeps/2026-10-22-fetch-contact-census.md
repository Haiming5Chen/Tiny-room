Measured for ADR 0050 (a contact census) on 2026-10-22 with `python -m little_world.inventory.census`. The casters' gaps and loads beside it were read from the same run's contact forces (`MujocoBackend.contact_forces`) and `mj_geomDistance`, every 50 ms.

# Contact census: Fetch, as designed

One run of the Fetch field as designed, its contacts counted every 10 steps (20 ms) at the moments its results are decided: for each pair of parts, the kinds of shape that touch, the contact points MuJoCo finds between them as the model is set (multiccd off, ADR 0027) and on a copy of the same instant with multiccd on - the least and most over the window, summed over the pair's bodies (a tread wheel's tyre segments are one tyre).

| Moment | Pair | Shapes | Points | With multiccd | In contact |
| --- | --- | --- | --- | --- | --- |
| standing at the start | floor - swivel_caster_1_wheel | box-cylinder | 1 | 5 | 20 of 20 |
| standing at the start | floor - swivel_caster_2_wheel | box-cylinder | 1 | 5 | 20 of 20 |
| standing at the start | floor - tread_wheel_1_tread | box-box | 4 | 4 | 20 of 20 |
| standing at the start | floor - tread_wheel_2_tread | box-box | 4 | 4 | 20 of 20 |
| standing at the start | table - fetch_cube | box-box | 4 | 4 | 20 of 20 |
| standing at the table, reaching | floor - swivel_caster_1_wheel | box-cylinder | 1 | 4-5 | 366 of 366 |
| standing at the table, reaching | floor - swivel_caster_2_wheel | box-cylinder | 1 | 4-5 | 366 of 366 |
| standing at the table, reaching | floor - tread_wheel_1_tread | box-box | 2-6 | 2-6 | 366 of 366 |
| standing at the table, reaching | floor - tread_wheel_2_tread | box-box | 3-6 | 3-6 | 366 of 366 |
| standing at the table, reaching | table - fetch_cube | box-box | 4 | 4 | 366 of 366 |
| held on the table | floor - swivel_caster_1_wheel | box-cylinder | 1 | 4 | 15 of 15 |
| held on the table | floor - swivel_caster_2_wheel | box-cylinder | 1 | 4 | 15 of 15 |
| held on the table | floor - tread_wheel_1_tread | box-box | 4 | 4 | 15 of 15 |
| held on the table | floor - tread_wheel_2_tread | box-box | 4 | 4 | 15 of 15 |
| held on the table | table - fetch_cube | box-box | 1-2 | 1-2 | 4 of 15 |
| held on the table | two_finger_gripper_1_finger_left_pad - fetch_cube | box-box | 1-2 | 1-2 | 15 of 15 |
| held on the table | two_finger_gripper_1_finger_right_pad - fetch_cube | box-box | 3-4 | 3-4 | 15 of 15 |
| held on the table | two_finger_gripper_1_palm_stop - fetch_cube | box-box | 1-2 | 1-2 | 5 of 15 |
| carried | floor - swivel_caster_1_wheel | box-cylinder | 1 | 4 | 54 of 100 |
| carried | floor - swivel_caster_2_wheel | box-cylinder | 1 | 4-5 | 100 of 100 |
| carried | floor - tread_wheel_1_tread | box-box | 2-4 | 2-4 | 100 of 100 |
| carried | floor - tread_wheel_2_tread | box-box | 2-4 | 2-4 | 100 of 100 |
| carried | two_finger_gripper_1_finger_left_pad - fetch_cube | box-box | 1-2 | 1-2 | 100 of 100 |
| carried | two_finger_gripper_1_finger_right_pad - fetch_cube | box-box | 1-4 | 1-4 | 100 of 100 |
| carried | two_finger_gripper_1_palm_stop - fetch_cube | box-box | 1-2 | 1-2 | 100 of 100 |
| resting where it was set down | bin_base - fetch_cube | box-box | 3-4 | 3-4 | 50 of 50 |
| resting where it was set down | floor - swivel_caster_2_wheel | box-cylinder | 1 | 4 | 50 of 50 |
| resting where it was set down | floor - tread_wheel_1_tread | box-box | 4 | 4 | 50 of 50 |
| resting where it was set down | floor - tread_wheel_2_tread | box-box | 4 | 4 | 50 of 50 |

Pairs whose count multiccd would change: floor - swivel_caster_1_wheel; floor - swivel_caster_2_wheel.

| Moment | Caster 1: gap, load | Caster 2: gap, load |
| --- | --- | --- |
| standing at the start | -0.04 mm, 0.38-0.39 N | -0.56 mm, 7.16 N |
| standing at the table, reaching | -0.25 to -0.02 mm, 0.59-2.52 N | -0.56 to -0.26 mm, 2.19-5.58 N |
| held on the table | -0.08 to -0.07 mm, 0.57-0.74 N | -0.49 to -0.48 mm, 5.60-5.89 N |
| carried | -0.12 to +0.34 mm, 0-1.14 N | -0.59 to -0.43 mm, 3.88-8.23 N |
| resting where it was set down | +0.20 to +0.22 mm, 0 N | -0.57 to -0.53 mm, 7.31-7.84 N |

A negative gap is how far MuJoCo's soft contact lets the wheel into the floor under its load.
