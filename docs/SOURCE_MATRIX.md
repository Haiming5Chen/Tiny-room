# Source matrix

Reviewed 2026-09-11. Links are upstream references; conceptual borrowing does not
mean copied source, imported assets, or an installed dependency.

| System / primary source | Borrow or reuse | Boundary / status |
| --- | --- | --- |
| [MuJoCo](https://mujoco.readthedocs.io/en/stable/python.html) | MjSpec construction, rigid bodies, contacts, joints, motors, cameras, viewer | Only initial solver; adapter owns native types |
| [Menagerie](https://github.com/google-deepmind/mujoco_menagerie) | Future high-quality robot assets | No assets imported; future wrapper must namespace IDs and record each model license |
| [robosuite](https://robosuite.ai/docs/modules/controllers.html) | Composition of controllers and robot parts | Conceptual; extend to primitive parts, no dependency |
| [RoboCasa](https://github.com/robocasa/robocasa) | Future household layouts and object assets | Keep task assumptions out of Scene; no import |
| [OmniGibson / BEHAVIOR](https://behavior.stanford.edu/omnigibson/object_states.html) | Explicit kinematic and semantic object states | Conceptual state extension; no NVIDIA dependency |
| [Isaac Lab Arena](https://isaac-sim.github.io/IsaacLab-Arena/release/0.1.0/pages/concepts/concept_overview.html) | Scene + Embodiment + Task separation | Conceptual only |
| [dm_control Composer](https://github.com/google-deepmind/dm_control) | Reusable composed entities | Conceptual; no dm_control dependency |
| [Genesis](https://github.com/Genesis-Embodied-AI/genesis-world) | Future multiphysics solver evaluation | Deferred; no initial dependency |
| [OpenFOAM](https://openfoam.org/) | Future CFD/heat reference | Deferred; evaluate when a concrete coupling is needed |
| [SOFA](https://www.sofa-framework.org/) | Future deformable/soft robotics reference | Deferred |
| [Project Chrono](https://projectchrono.org/) | Future multibody/vehicle/granular reference | Deferred |

Selection criteria: existing capability, wrapping cost, licensing, measurable
accuracy, portable deployment, and whether integration preserves Blueprint and
backend independence. Do not claim interchangeability without adapter conformance
tests. No solver implements all future state merely by satisfying PhysicsBackend.
