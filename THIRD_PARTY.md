# Third-party register

Four robot models from MuJoCo Menagerie and two CC0 surface textures from
Poly Haven are bundled, with sources and licenses listed below. Other robot/room
geometry is procedural. Conceptual sources and planned integrations are in docs/SOURCE_MATRIX.md.

| Dependency | Use | License / source |
| --- | --- | --- |
| MuJoCo Python package | Optional mechanical adapter, renderer, viewer | Apache-2.0, https://github.com/google-deepmind/mujoco/blob/main/LICENSE |
| pytest | Development tests only | MIT, https://github.com/pytest-dev/pytest/blob/main/LICENSE |
| setuptools | Build tooling | MIT, https://github.com/pypa/setuptools |

Transitive dependencies remain separately distributed with their own notices.
The tested environment is recorded by requirements-lock.txt. Before redistributing
an external asset record its source URL, exact revision, files, per-asset license,
required notices, modifications, and redistribution restrictions here. Menagerie
model licenses vary; a repository-level license is not sufficient for every asset.
The project owner has not selected a license for original Little World code.

The inspection window directly uses `glfw`, already installed as a MuJoCo dependency,
for window/input handling, and MuJoCo for rendering. Upstream:
https://github.com/FlorianRhiem/pyGLFW (Python binding, MIT) and
https://www.glfw.org/license.html (GLFW, zlib/libpng license). No upstream viewer
source was copied into Little World.

The workshop extra uses Pillow (HPND license; https://python-pillow.org/) to rasterize
its bundled default font once into a GPU atlas, and PyOpenGL (BSD-style license;
https://pyopengl.sourceforge.net/) for batched 2D drawing. Pillow's bundled font
and dependency notices remain in its separately installed distribution. No font
files or GUI source are copied into this repository. The core has no dependency
on these UI packages.


## Bundled surface assets (2026-09-12)

| Asset | Author | License | Upstream |
| --- | --- | --- | --- |
| Wood Floor | Dimitrios Savva | CC0-1.0 | https://polyhaven.com/a/wood_floor |
| Fine Grained Wood | Rob Tuytel | CC0-1.0 | https://polyhaven.com/a/fine_grained_wood |

Only the 1K diffuse/color JPGs were downloaded. Upstream MD5 values were verified;
the images were decoded to RGB, resized to 512x512 using Lanczos, and stored as
gzip-compressed raw RGB for loading without Pillow in the physics package.
Exact URLs, authors, upstream checksums, output SHA-256 hashes and transformations
are recorded in `src/little_world/assets/data/SOURCES.json`. Assets are packaged
with the Python wheel. CC0: https://creativecommons.org/publicdomain/zero/1.0/

Brushed metal, rubber tread and plastic textures are original procedural patterns.
The procedural kit modules are original designs, not commercial CAD or
manufacturer-calibrated components. The separately sourced Panda model is listed below.


## Hardware reference pages (2026-09-13)

Original hardware geometry was informed by the forms and dimensions shown at:

- Pololu 37D gearmotors: https://www.pololu.com/category/116/37d-metal-gearmotors
- goBILDA structural system: https://www.servocity.com/gobilda

These are reference-only sources. No vendor CAD, photographs, logos, source code
or drawings are redistributed, and these modules are not accurate vendor replicas.
The ideal motor limits and inferred masses are not copied product specifications.

The batched body-velocity observation matches MuJoCo's `mj_objectVelocity`
world-oriented body-inertial convention (written against 3.3.7, tested on 3.10.0).
Reference implementation:
https://github.com/google-deepmind/mujoco/blob/3.3.7/src/engine/engine_core_util.c
and `mju_transformSpatial` in `engine_util_spatial.c` (MuJoCo, Apache-2.0).
The vectorized NumPy implementation is independently written and tested against the
installed MuJoCo function, including rotating bodies and shaft subparts.


## Franka Emika Panda model (2026-09-19)

- Source: https://github.com/google-deepmind/mujoco_menagerie/tree/8161bba264d7fa7c99ca301e91e7fb44737676ad/franka_emika_panda
- Exact revision: `8161bba264d7fa7c99ca301e91e7fb44737676ad`.
- Asset license: Apache-2.0, copied verbatim to
  `src/little_world/assets/robots/panda/LICENSE`.
- Upstream description credits Franka Emika and derives from `franka_ros` robot
  descriptions. Original mesh headers, README and CHANGELOG are retained.
- Bundled files: `panda.xml`, all files in its `assets/` directory, and the above
  notices/docs. `SOURCE.json` records the source revision and SHA-256 of every
  downloaded file. No source mesh or XML files were modified.
- Local additions: `metadata.json` records the upstream home pose, bounds, mass and
  ranges; `thumbnail.png` is rendered locally from this model. The adapter namespaces
  model elements, removes copied keyframes in memory and restores the source home
  pose explicitly after composition. It hides collision-only geometry in normal
  rendering without changing its contact properties.
- Physics: original inertias, joint limits, damping/armature, servos, force caps,
  tendon and equality coupling remain in MuJoCo. This model is an upstream
  approximation; it is not a calibrated digital twin or a hardware purchase promise.


## Additional registered arms (2026-09-19)

All are pinned to Menagerie revision `8161bba264d7fa7c99ca301e91e7fb44737676ad`.
Each model directory under `src/little_world/assets/robots/` contains its original
LICENSE, README, CHANGELOG, XML and meshes, plus SOURCE.json with per-file hashes.
Upstream files are unmodified. Locally generated metadata and thumbnail PNGs follow
the same pipeline described for Panda. The new entries are arm-only; no gripper is
invented or implied. Original actuator gains, source force/joint limits and inertias
are retained. Free-turning Gen3 axes keep their original joint behavior; the keyboard
interface limits their target to +/-360 degrees as an interface travel window.

| Entry | Menagerie directory | License / copyright |
| --- | --- | --- |
| Franka Research 3 | franka_fr3 | Apache-2.0; upstream Franka Robotics description |
| Kinova Gen3 | kinova_gen3 | BSD-3-Clause; Copyright 2018 Kinova inc. |
| UR5e | universal_robots_ur5e | BSD-3-Clause; Copyright 2018 ROS Industrial Consortium |

Sources: https://github.com/google-deepmind/mujoco_menagerie/tree/8161bba264d7fa7c99ca301e91e7fb44737676ad
