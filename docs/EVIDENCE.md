# Evidence: what is claimed, where it was measured, and how to measure it again

Written by `little-world evidence --markdown` from `src/little_world/evidence.py`; a test keeps the two the same.

Every physical claim in this project has a number, a decision record that explains it and a test that holds
it. This page lists a dozen headline claims with the numbers recorded for them
(Linux x86_64, Python 3.13, MuJoCo 3.10.0, 10 Nov 2026) and the tolerance inside which a re-run still counts as holding. Run

```sh
little-world evidence            # all of them, about four minutes on two cores
little-world evidence --quick    # the five that take seconds
little-world evidence --only fetch tilt --json mine.json
```

and each number is measured again on your machine and printed beside the recorded one. A physics engine
is deterministic on one machine and build, not across processors, operating systems or MuJoCo releases:
a number that moves on your machine is a finding worth an issue, with the `--json` file attached.

One claim is a flaw recorded as it is, not something to be proud of; [the evaluation](EVALUATION.md) lists more.

## `sprint`

The kit cart covers the 5 m sprint in 11.8 s: its drive assist's 0.425 m/s sets the time, not its motors.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| 5 m from the start line | 11.85 s | 0.35 s |
| stayed upright | yes | the same |

Why: [docs/adr/0013-test-fields.md](adr/0013-test-fields.md). Held by `tests/test_fields.py::test_the_sprint_is_timed_by_the_drive_assist_speed`. Again: `little-world evidence --only sprint` (about 17 s).

## `curb`

On all four wheels the kit cart clears a 10 mm curb, slowly - at 10.4 s - and not a 20 or 35 mm one.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| 10 mm curb cleared at | 10.36 s | 1.5 s |
| 20 mm curb cleared | no | the same |
| 35 mm curb cleared | no | the same |

Why: [docs/adr/0041-the-cart-stands-on-all-four.md](adr/0041-the-cart-stands-on-all-four.md). Held by `tests/test_fields.py::test_on_all_four_wheels_the_cart_stalls_at_a_curb_and_gets_over_only_slewed_onto_a_drive_wheel`. Again: `little-world evidence --only curb` (about 14 s).

## `tilt`

On the tilt table the arm on its cart goes over at 54.6 deg, a degree before the 55.6 its design predicts.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| went over at | 54.61 deg | 1 deg |
| its design predicts | 55.58 deg | 0.05 deg |

Why: [docs/adr/0029-tilt-test-squares-the-machine.md](adr/0029-tilt-test-squares-the-machine.md). Held by `tests/test_tipping.py::test_on_the_tilt_table_the_angle_runs_out_as_the_arm_cart_goes_over`. Again: `little-world evidence --only tilt` (about 22 s).

## `tilt-cart`

The cart without its arm still stands at the table's 60 deg; its design predicts 72.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| held at the table's 60 deg | yes | the same |
| its design predicts | 71.95 deg | 0.05 deg |

Why: [docs/adr/0059-how-near-it-is-to-tipping.md](adr/0059-how-near-it-is-to-tipping.md). Held by `tests/test_tipping.py::test_the_cart_without_its_arm_keeps_twelve_degrees_at_the_tables_top`. Again: `little-world evidence --only tilt-cart` (about 20 s).

## `doorway`

The kit cart drives through a doorway and parks in the bay beyond without touching the frame.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| through the doorway at | 14.37 s | 1 s |
| parked in the bay at | 16.54 s | 1 s |
| door frame untouched | yes | the same |

Why: [docs/adr/0018-fetch-drive-to-a-point.md](adr/0018-fetch-drive-to-a-point.md). Held by `tests/test_more_fields.py::test_the_doorway_program_takes_the_platform_through_without_touching_the_frame`. Again: `little-world evidence --only doorway` (about 22 s).

## `pick-place`

The arm lab lifts its cube by finger contact and rests it in the tray.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| cube lifted at | 1.902 s | 0.2 s |
| resting in the tray at | 5.724 s | 0.5 s |

Why: [docs/adr/0016-arm-tasks-tool-moves-poses-grasp-checks.md](adr/0016-arm-tasks-tool-moves-poses-grasp-checks.md). Held by `tests/test_arm_tasks.py::test_the_pick_and_place_template_meets_the_fields_goals`. Again: `little-world evidence --only pick-place` (about 2 s).

## `fetch`

The arm on its cart drives 1.8 m to a table, finds the cube with its camera, picks it up, brings it back and sets it in the bin: every goal met, the cube in the bin at 36.9 s, without looking twice.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| every goal met | yes | the same |
| cube in the bin at | 36.87 s | 1 s |
| looked again | 0 | the same |

Why: [docs/adr/0042-set-down-not-dropped.md](adr/0042-set-down-not-dropped.md). Held by `tests/test_fetch.py::test_the_mobile_manipulator_fetches_the_cube_by_itself`. Again: `little-world evidence --only fetch` (about 35 s).

## `fetch-felt`

The cube moved 5 cm just after the camera looked: a jaw comes down on it, the arm's servos feel it and the arm rises 0.2 s later, looks again and fetches it.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| every goal met | yes | the same |
| the arm rose off the cube at | 17.44 s | 0.5 s |
| why | felt it | the same |
| cube in the bin at | 40.83 s | 1.5 s |

Why: [docs/adr/0071-a-reach-that-feels-what-it-meets.md](adr/0071-a-reach-that-feels-what-it-meets.md). Held by `tests/test_felt_reach.py::test_the_cube_moved_under_a_jaw_is_felt_at_once_and_not_pressed_for_two_seconds`. Again: `little-world evidence --only fetch-felt` (about 45 s).

## `slope-creep`

A block resting on a slope inside its friction angle should stand still. It creeps: 0.2 mm/s on 5 deg, 1.4 mm/s on 15 deg.

*A known flaw:* MuJoCo's pyramidal friction cones let a resting contact creep (OPEN LW-039); every friction result here rests on them.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| creep on 5 deg | 0.21 mm/s | 0.1 mm/s |
| creep on 15 deg | 1.36 mm/s | 0.4 mm/s |

Why: [docs/adr/0061-how-close-to-slipping.md](adr/0061-how-close-to-slipping.md). Held by `tests/test_friction_use.py::test_a_block_on_a_slope_uses_tan_theta_over_mu_of_its_friction_until_it_slides`. Again: `little-world evidence --only slope-creep` (about 2 s).

## `conveyor`

A roller conveyor carries two pallets at 0.1 m/s to a stop: the first arrives at 1.7 s, the second queues behind it.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| first pallet at the stop at | 1.72 s | 0.15 s |
| second queued behind it at | 1.92 s | 0.15 s |
| the cube still on its pallet | yes | the same |

Why: [docs/adr/0067-a-roller-conveyor.md](adr/0067-a-roller-conveyor.md). Held by `tests/test_conveyor.py::test_pallets_ride_at_the_rollers_speed_to_the_stop_and_queue`. Again: `little-world evidence --only conveyor` (about 4 s).

## `cell`

In Real's factory cell the Panda puts each part within a millimetre of its slot and squares up one fed turned 10 deg, 12 to 14 s a part.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| both parts placed | yes | the same |
| furthest from its slot | 0.62 mm | 0.6 mm |
| most it was left turned | 1.6 deg | 1.4 deg |
| slowest part | 13.93 s | 1.5 s |

Why: [docs/adr/0065-the-panda-holds-itself-up.md](adr/0065-the-panda-holds-itself-up.md). Held by `tests/test_process_window.py::test_a_production_run_says_where_each_part_was_left_and_a_fed_part_off_centre_is_still_placed`. Again: `little-world evidence --only cell` (about 20 s).

## `twice`

A run repeated on the same machine is the same run, bit for bit: paired comparisons rest on it.

| Measured | Recorded | Holds within |
| --- | --- | --- |
| the two runs differ at | no step | the same |

Why: [docs/adr/0036-paired-runs.md](adr/0036-paired-runs.md). Held by `tests/test_paired_runs.py::test_the_two_runs_of_a_fetch_pair_are_one_run_until_the_cube_is_moved`. Again: `little-world evidence --only twice` (about 4 s).

