"""Beginner explanations and honest model scope for the original mechanical kit."""


def part_guide(item):
    v=item.variant
    level='Component'
    purpose=item.description
    connection='Mount on a structural face. Fixed parts move with the body they attach to.'
    example='Use with a chassis, frame, or another compatible structural part.'
    limits='Original procedural model. Dimensions and material density determine mass; vendor fit is not verified.'
    related=''
    if v=='real_robot':
        level='Real robot model'
        purpose=item.title+', sourced from MuJoCo Menagerie. '+('Includes a coupled gripper.' if item.id=='franka_panda' else 'Arm only; no gripper included.')
        connection='Drag into the build area for an anchored arm, or onto a compatible deck to mount it. Model mass is shown on its card.'
        example='Arm controls lists editable joint keys. Panda includes a G/H gripper; the other real models are arm-only.'
        limits='Original meshes, inertias, joint limits and force-limited servos retained. Fixed-size complete assembly; upstream approximation, not calibrated hardware or a payload guarantee.'
    elif v.startswith('lab_'):
        level='Generic lab assembly'
        connection='Place on the floor; fixed tables and supports stay anchored.' if item.mount=='Floor' else 'Attach to a structural top face.'
        example='Combine platforms, tables, arms and handling objects to build a workcell.'
        if v in ('lab_mobile','lab_mobile_cell','lab_delivery','lab_gen3_cell'):example='WASD drives all wheels together. Mount an arm on the deck; open Keyboard for joint controls.'
        if v=='lab_fixed_cell':example='Arm and gripper are already mounted. Open Keyboard for the joint bindings.'
        if v=='lab_tilt':example='R/V tilts the deck through +/-45 degrees. Select the deck in Assembly to attach a fixture that moves with it.'
        if v=='lab_inspection':example='An RGB camera looks down onto the table; it does not recognize or sort objects automatically.'
        if v=='lab_ramp':example='Drive or slide a loose object over the anchored 12-degree incline.'
        if v=='lab_index':example='Q/E rotates the platen. Bindings are reassigned if already used; check Keyboard.'
        if v=='lab_rollers':example='Push a loose object along the freely rotating rollers. There is no powered belt.'
        if v=='lab_gantry':example='The downward RGB camera renders a view; it does not recognize objects or plan grasps.'
        if v in ('lab_bin','lab_pallet','lab_box','lab_sorting','lab_cylinder','lab_ball'):connection='Drop as a loose movable object on the floor, or attach rigidly to a structural face.'
        limits='Original geometry with estimated materials and actuator limits. No verified vendor payload, mounting standard, electronics or calibration.'
        if v in ('lab_ur_cell','lab_gen3_cell'):limits+=' Sourced arm without gripper; internal tool attachment is not yet supported.'
        if v in ('lab_mobile_cell','lab_fixed_cell'):limits+=' Panda retains its sourced Menagerie meshes, inertias and servos.'
    elif v.startswith('ready_'):
        level='Ready assembly';purpose=item.description
        connection='Place on the floor to start a new robot.' if v=='ready_base' else 'Attach to a chassis top.' if v in ('ready_arm','ready_camera','ready_tray') else 'Attach to the front of a chassis.'
        example='Includes the motors and default controls. Add the assembly, then open Keyboard to see its keys.'
        if v=='ready_base':example='WASD drives the assembled base. Add an arm, camera or cargo attachment to its chassis.'
        if v=='ready_arm':example='Arm and gripper are already connected. Use joint keys to move and G/H to close/open the first gripper.'
        limits='Rigid contact and torque-limited joints. This is an original procedural assembly, not calibrated vendor hardware.'
        if v=='ready_scoop':limits+=' Intended for rigid objects; loose soil and granular materials are not modeled.'
        if v=='ready_fork':limits+=' Forks tilt around a hinge; this is not a vertical forklift mast.'
    elif v=='drive':
        level='Assembly'
        purpose='A wheel and ideal axle motor in one ready-to-drive unit. You do not need to add another motor.'
        connection='Use left/right center mounts for two wheels, or front/rear side mounts for four. Both sides face outward automatically.'
        example='Pair left and right powered wheels to drive with WASD. Each additional pair receives the same controls.'
        limits='Ideal torque-limited drive; no motor housing, gearbox losses, battery or wiring simulation.'
    elif v in ('wheel','hw_tread'):
        purpose='A passive wheel: it supports a robot and rolls, but cannot drive itself.'
        connection='On a chassis side it gets a free axle. On a motor output it is rigidly attached to the powered shaft.'
        example='Chassis -> gearmotor -> output -> wheel. A complete powered wheel is the quicker alternative.'
        related='gearmotor'
    elif v in ('hw_gearmotor','hw_motor','hw_servo'):
        level='Assembly'
        purpose='Creates torque at its moving output. The casing stays attached while the shaft or horn turns.'
        connection='Select the motor, then choose a wheel, crank, roller, hub or arm link. Its output socket is found automatically.'
        example='Motor -> crank arm for a rotating lever; motor -> drive roller to push objects by contact. Bind its joint in Program / keyboard controls.'
        limits='Ideal torque limits and native joint motion. Servo travel is limited; electronics, current draw and gearbox backlash are not simulated.'
        related='shaft-driven'
    elif v=='shaft_load':
        purpose={
            'crank':'A rotating lever: turns motor rotation into an end point moving in a circle.',
            'drive_roller':'A rubber roller that can push touching objects through friction.',
            'flywheel':'A rotating mass that increases inertia, resisting changes in motor speed.',
            'spool':'A drum shape for a future winch. It rotates now, but there is no cable simulation.',
            'turntable':'A flat rotating plate, useful for a simple rotating platform.'
        }[next(k for k in ('crank','drive_roller','flywheel','spool','turntable') if item.id.startswith(k))]
        connection='Attach to a motor output or a hub/coupler output. This part adds no motor and no extra free joint.'
        example='Mount a gearmotor first, select its casing, then drag this part onto output.'
        limits='Rigid contact and inertia are simulated. No cables, belts, gearing or automatic closed-loop linkages.'
        related='gearmotor'
    elif v in ('hw_hub','hw_coupler'):
        purpose='A hub provides a flange for attaching a load to a shaft.' if v=='hw_hub' else 'A coupler carries rotation from one shaft connection to the next.'
        connection='Attach to a motor output; then attach a passive wheel or driven part to this component\'s output.'
        example='Motor -> hub -> wheel. All three share the existing powered joint.'
        limits='Rigid connection only. No bore fit checks, flexible coupling compliance or slip under overload.'
        related='shaft-driven'
    elif v.startswith('hw_arm') and v not in ('hw_arm_link','hw_arm_deck'):
        level='Assembly';purpose='A complete arm with four powered joints: base yaw, shoulder, elbow and wrist.'
        connection='Attach the base to a chassis top or arm deck. A separate gripper fits its tool socket.'
        example='Chassis -> arm -> gripper. Use keyboard joint bindings or a Program sequence to move it.'
        related='gripper';limits='Procedural articulated mechanism with torque limits, not a calibrated industrial arm.'
    elif 'gripper' in v:
        level='Assembly';purpose='Two powered jaws grasp an object through physical contact and friction.'
        connection='Requires an arm tool socket; jaw shape, pad material and motor power can be adjusted.'
        example='Arm -> gripper. Close the jaws around an object, then lift; inadequate grip can slip.'
        related='arm'
    elif v=='hw_arm_link':
        purpose='A rigid arm segment without a motor. It becomes a lever when attached to a rotating output.'
        connection='Its proximal end mates to a motor output. It does not create another powered joint.'
        example='Servo -> arm link. The servo turns the link as one rigid load.'
        related='servo'
    elif v=='hw_bearing':
        level='Hardware';purpose='A support that lets its inner race turn while its housing remains mounted.'
        connection='Mount the housing to structure; use precision connections to attach a shaft to the inner race.'
        limits='Free rotational joint. Automatic shaft alignment and two-support closed loops are not implemented.'
    elif v=='hw_clamp':
        level='Hardware';purpose='A bracket intended to hold a motor casing in a frame.'
        limits='Structural geometry. Clamping force and automatic bore-size matching are not simulated; use precision placement.'
    elif v in ('hw_bolt','hw_standoff','standoff'):
        level='Hardware';purpose='A spacer creates room between layers.' if 'standoff' in v else 'A fastener represents the mounting hardware of an assembly.'
        limits='Rigid geometry only. Connections are made by the builder, not by tightening simulated screw threads.'
    elif v=='hw_caster':
        level='Assembly';purpose='An unpowered support wheel that swivels to follow a robot\'s direction.'
        connection='Mount underneath a chassis and check ground height with the main wheels.'
        example='Two driven wheels plus a caster give a stable three-point base.'
    elif item.category=='Structure':
        purpose=item.description+' Structural pieces hold other components in position; they do not move by themselves.'
    return dict(level=level,purpose=purpose,connection=connection,example=example,limits=limits,related=related)
