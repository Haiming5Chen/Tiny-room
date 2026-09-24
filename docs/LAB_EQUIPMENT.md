# Lab equipment and assembled workcells

In **Anime → Build**, search the component library for equipment. It includes 26 assemblies,
with rendered pictures, searchable names, dimensions and purpose descriptions.
The four standalone sourced arms are selected through the **Real → Robot** picker.
The full catalog now contains 115 entries.

| Equipment | Use and behavior |
| --- | --- |
| Mobile manipulation platform | Four powered wheels; clear arm deck; WASD drive assistance |
| Six-wheel research platform | Longer deck; six powered wheels sharing drive commands |
| Robot workbench | Anchored 1200 × 800 mm tabletop |
| Compact experiment table | Anchored 800 × 600 mm tabletop |
| Robot mounting pedestal | Anchored column for a separately selected arm |
| Powered indexing table | Rotary platen, ±180° travel, 12 Nm ideal motor; default Q/E |
| Passive roller conveyor | Twelve free rollers; move cargo by pushing, no powered belt |
| Open parts bin | Hollow rigid container, movable when placed on the floor |
| Small logistics pallet | Wooden slats and open fork entries; movable cargo support |
| Small handling box | Rigid carton-shaped test object, estimated 0.45 kg |
| V-block workholding fixture | Passive cradle for cylindrical workpieces |
| Overhead camera gantry | Fixed downward RGB camera; no object recognition |
| Panda mobile manipulator | Sourced Panda arm and gripper on the generic powered platform |
| Panda tabletop workcell | Sourced Panda arm and gripper on the anchored workbench |
| Wide six-wheel equipment base | Wider deck, six ideal 18 Nm drives; not a certified higher payload |
| Cargo delivery platform | Four-wheel base with cargo-retaining rails |
| Powered tilting table | Horizontal tilt axis, ±45°, 20 Nm ideal motor; default R/V |
| Peg locating fixture | Four passive locating posts; no active clamping |
| Four-compartment sorting tray | Loose open tray with four pockets |
| Three-level storage rack | Anchored open shelves |
| Traction test ramp | Anchored 12° inclined surface |
| Cylindrical grasp sample | Loose plastic cylinder, 60 mm diameter × 140 mm long |
| Rubber grasp ball | Loose solid rubber sphere, 80 mm diameter |
| Overhead inspection station | Workbench with an actual downward RGB camera |
| UR5e pedestal workcell | Sourced six-axis arm on a fixed pedestal; no gripper |
| Kinova mobile manipulator | Sourced seven-axis arm, wrist camera, powered base; no gripper |

Drag assemblies into the build area. Complete platforms, tables, pedestals and
conveyors require floor placement. Mount arms and small fixtures on compatible
top faces. Placing loose cargo on the floor leaves it dynamic; attaching it to a
face creates a rigid connection. The builder does not yet provide a separate
“place loose on this shelf” snap mode. Keyboard lists current joint bindings;
conflicting defaults are reassigned automatically. Every addition is undoable.

Linear slides and lifts are not included: the portable joint model currently supports
rotary hinges. The inspection station captures RGB images but does not recognize
objects or perform automated inspection. UR5e and Kinova have no gripper, and
attaching tools to their internal native links is not supported yet. For a moving
fixture on the tilting table, select its tilt deck in Assembly and mount there.

The new equipment is original generic geometry with estimated material masses
and ideal torque limits. Mobile bases are differential drive, not omnidirectional.
Grid markers are visual placement references, not tapped holes. Assemblies do not
certify payload, commercial compatibility, wiring, safety or real-world accuracy.
Panda retains the registered Menagerie meshes, inertias, joint limits and servos.

## Research and provenance

Equipment categories were informed by these primary sources, accessed 2026-09-20:

- [Clearpath Ridgeback](https://clearpathrobotics.com/ridgeback-indoor-robot-platform/)
  and its [integration guide](https://docs.clearpathrobotics.com/docs_robots/indoor_robots/ridgeback/integration_ridgeback/):
  mobile manipulation platforms and arm integration. Our geometry, drive layout
  and ratings do not reproduce Ridgeback.
- [Universal Robots applications](https://www.universal-robots.com/applications/)
  and [palletizing](https://www.universal-robots.com/applications/palletizing/):
  handling, workcells and pallet-related workflows.
- [Thorlabs breadboards](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_ID=1861):
  reusable laboratory mounting surfaces. No vendor mounting standard is claimed.

No geometry or textures were downloaded from those sources. Lab thumbnails are
renders of our own Blueprint assemblies; Panda meshes retain the upstream license
and provenance under `src/little_world/assets/robots/panda/`.
Regenerate previews with `.venv/bin/python scripts/render_lab_thumbnails.py`.
