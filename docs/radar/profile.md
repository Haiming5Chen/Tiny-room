# Radar profile

What the frontier radar looks for besides the decision records, which it reads by itself
(`python -m little_world.radar topics` lists every topic). Each `##` heading is a topic:

- `ADR nnnn` adds words to that decision: the terms papers use for what the record
  solved in its own words.
- `Next: ...` is a step the project plans to take.
- `Learn: ...` is something its builder wants to understand.

Words are matched by stem and by adjacent pairs, so a phrase written here also matches
the same phrase in an abstract. Keep each topic to what would change a decision; a
topic that matches everything ranks nothing.

## ADR 0001
simulation architecture; physics engine abstraction; scene description format; MJCF; URDF; USD; digital twin data model

## ADR 0003
kinematic chain assembly; joint axis; revolute joint; mechanism design; CAD assembly constraints

## ADR 0006
teleoperation; joint space control; gripper control; manual robot control interface

## ADR 0007
DC motor model; servo motor model; torque speed curve; stall torque; gearbox efficiency; actuator model; motor datasheet; back-EMF; cogging torque; actuator delay

## ADR 0010
contact friction coefficient; friction model; material pairs; tire friction; rubber on concrete; tribology

## ADR 0011
rolling resistance; gearbox friction; drivetrain losses; wheel slip; wheeled robot dynamics

## ADR 0013
simulation benchmark; robot evaluation; task success metric; test scenarios; sim evaluation of policies

## ADR 0014
PD controller stability; PID controller; position servo; position actuator gains; stiff actuators; implicit integration; actuator damping; time step stability; joint chatter

## ADR 0015
static stability; tip-over stability; support polygon; center of mass; stability margin; mobile manipulator stability

## ADR 0016
inverse kinematics; end-effector control; operational space control; pick and place; grasp planning; teach pendant

## ADR 0017
grasp slip; contact creep; soft contact model; friction cone; complementarity; contact solver; grasp stability

## ADR 0018
mobile manipulation; differential drive control; point stabilization; nonholonomic robot; wheeled mobile robot navigation

## ADR 0019
industrial robot cell; production line simulation; throughput; bin picking; manufacturing automation; digital twin factory
<!-- The registered robots (Panda, FR3, Gen3, UR5e) are MuJoCo Menagerie models (OPEN LW-013). -->
MuJoCo Menagerie; Menagerie robot models; Franka Emika Panda; Franka FR3; Kinova Gen3; Universal Robots UR5e; robot arm models; gripper models; MJCF robot description

## Next: conveyor and feeder
conveyor belt simulation; part feeder; material flow; moving surface contact; logistics automation

## Next: grasping from a camera
vision-based grasping; object pose estimation; grasp detection; RGB-D perception; camera calibration; visual servoing

## Next: paths through clutter
motion planning; path planning; collision avoidance; corridor navigation; local planner; costmap

## Next: closer to the real machine
system identification; sim-to-real transfer; reality gap; actuator identification; friction identification; domain randomization; parameter estimation

## Learn: robot learning
imitation learning; behavior cloning; diffusion policy; vision-language-action model; VLA; robot foundation model; reinforcement learning for robots; teleoperation datasets

## Learn: physics simulation
rigid body simulation; contact dynamics; differentiable simulation; GPU physics; MuJoCo; simulation accuracy

## Learn: language models that program robots
code generation for robots; LLM robot programming; language to robot program; agent writes robot code; task planning with language models
