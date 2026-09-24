# Component catalog and surface appearance

The catalog contains 115 entries: 85 editable kit modules, 26 generic lab
assemblies and four sourced robot models. See [lab equipment](LAB_EQUIPMENT.md). Each entry states its capability, dimensions and default mounting face.
The preview is a separate cached MuJoCo scene and does not insert or simulate the
part until Add is clicked. Drag/zoom the preview independently of the main room.

Instances receive unique namespaces for bodies, attachments, hinges, motors and
cameras. Subparts remain individually editable. A wheel's hub/spokes are actual
fixed children, with mass/inertia; they are not just a texture. Motorized wheel
modules gain an ideal torque actuator when attached to a parent. The left/right
naming resolves differential-drive control independently of insertion order.

Catalog mounting uses face offsets derived from the parent geometry and the full
initial module geometry envelope, including rotated and offset children.
It is not arbitrary snapping or a collision-free assembly guarantee. Modules can
intersect if repeatedly placed on the same face; users can move them and observe
the result. Deletion cascades through descendant bodies and referenced devices.

## Functional boundaries

Structural parts: fixed rigid attachments. Free wheels/hinged arm: passive hinges.
Powered wheels: ideal torque motors, with two-channel differential control when
paired on left/right. Cameras: actual rendered RGB observations. Sensor plates,
electronics enclosures and battery trays do not simulate sensors, electronics or
batteries. The bumper is rigid and the support foot slides; neither deforms nor
rolls like a caster. No vendor model accuracy is claimed.

## Surface assets

Material's optional texture ID and roughness fields serialize as additive version-1
fields. Older designs still load with texture=None. Reapplying a library material
adds its visual surface while preserving the existing material's density/friction.
Materials are shared by ID within an assembly, so this refresh affects other parts
using that same material. Appearance never changes the collision shape.

The backend registers a fixed, deterministic five-texture library in stable order,
including unused entries. GPU contexts can therefore remain alive across edits:
the texture IDs, sizes and pixels do not change between compilations. Unknown IDs
are rejected. Future external assets require explicit resource invalidation.

Wood Floor and Fine Grained Wood are CC0 textures from Poly Haven, resized for this
lightweight renderer. Metal brushing, rubber tread and plastic are procedural RGB
patterns. Scalar roughness maps approximately to the legacy renderer's specular
and shininess settings. Normal/displacement maps and full PBR lighting are not
implemented. The reference is MuJoCo's material/texture interface:
https://mujoco.readthedocs.io/en/3.3.7/XMLreference.html#asset-material

Selection is a visual-only edge cage. It no longer overwrites material colors.
The catalog substantially broadens construction; realism still requires measured
physical parameters, more accurate geometry/contact models and richer rendering.


## Advanced hardware and focused workbench

Fourteen added modules are defined in `assets/hardware.py`. Motors expose shaft/horn
frames on the actual moving bodies. The caster has two passive hinges; the bearing
block has a freely rotating inner race. Other hardware attachments remain rigid.
The mobile platform example fastens its wheels to powered output shafts and uses
mirrored hinge axes so the same-sign drive command moves both wheels forward.

Geometry uses original compound primitives with separate ring segments, fork walls,
profile webs and fastener heads. It remains editable and contributes mass/inertia.
Generic aluminium/steel/copper material values are illustrative; no vendor mass,
backlash, electrical characteristics or thread/rolling-bearing mechanics are claimed.
Normal/displacement/PBR rendering, flexible couplers and vendor CAD imports remain
outside this slice. The 37 mm-class motor and modular hardware proportions were
informed by primary manufacturer reference pages (see THIRD_PARTY.md); no models
or product imagery were copied into the project.

The workbench is an in-window build workspace with a persistent parts browser,
independent assembly and component-preview cameras, searchable mounting target,
and links to dimension/joint editing. It shares the editor, texture registry and
GPU context with the room. Opening/closing it never changes the saved design. The
assembly viewport reuses the already-compiled world model with a separate room-hiding
view option; it does not compile the design a second time on edits. Room simulation runs only after
returning to the room and pressing Simulate.

## Ready-to-build assemblies

The default library prioritizes complete drive bases, picking arms with grippers,
powered cargo tools and a pan-tilt camera. Ten assemblies in
`assets/ready_assemblies.py` bring the catalog to 85 entries. Each emits ordinary
editable Blueprint components and receives default keyboard controls on insertion.
Bare actuators and small hardware remain accessible in Advanced. Search stays
inside the selected library. These are illustrative mechanisms, not calibrated
models of commercial robots.


## Real robot model

Entry 86 is **Franka Panda + gripper** (`franka_panda`). It is a pinned Menagerie
assembly with actual mesh assets, seven revolute arm joints, two coupled sliding
fingers and eight position actuators. The default is an anchored floor placement;
a Top mount attaches the base to a deck. Its bounds proxy is invisible, massless
and noncolliding. The source model determines the physics and appearance. Internal
parts and dimensions are intentionally fixed in this integration; whole-assembly
placement, save/load, copy, deletion and undo are supported. See THIRD_PARTY.md.


The Real robots tab now contains Panda, Franka Research 3, Kinova Gen3 and UR5e.
FR3 and Gen3 provide seven arm joints; UR5e provides six. These three models do not
include a gripper. The Anime / kit tab retains 85 editable procedural modules,
for 89 catalog entries overall. These are library styles, not physics modes.
