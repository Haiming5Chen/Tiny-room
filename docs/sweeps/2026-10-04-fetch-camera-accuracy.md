# The Fetch table camera finding its cube

The cube set down at 80 placements round where the program plans it (moved -2 to +8 cm towards the camera's side of the table, -8 to +8 cm sideways, turned 0 to 45 deg), the machine at its start. Each sighting against where the cube really was (ADR 0032).

| Camera | Pictures | Found | Position error, median / largest | Turn error, median / largest |
| --- | --- | --- | --- | --- |
| Without noise | 80 (1 a placement) | 80 of 80 | 1.2 / 1.9 mm | 0.3 / 2.4 deg |
| Intel RealSense D435 noise | 1600 (20 a placement) | 1600 of 1600 | 1.3 / 2.4 mm | 0.6 / 6.0 deg |

The largest error with noise: 2.4 mm, the cube moved -2 cm, +0 cm and turned 0 deg.

A picture is the D435's 848 x 480 depth pixels over the region round the planned place, cast as rays from the camera (MuJoCo `mj_multiRay`), with its noise (depth error z^2 x 0.08 px / (f x 50 mm)). The cube's size is known; its place and turn are measured.
