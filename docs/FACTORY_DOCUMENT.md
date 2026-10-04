# Shared factory scene document

This is the shared Python/data layer for future manual scene editing and AI
proposals. It does not replace the existing Panda cell UI and does not connect a
language model. Existing machine building continues to produce the same Blueprint
files used by this document.

## What is stored

- **MachineAsset**: a stable asset ID and embedded, immutable Blueprint. A custom
  machine saved from Anime mode can be used directly; no native solver handles or
  executable code are stored.
- **Station**: a stable instance ID, an asset ID, a human-readable label and world
  transform. Two stations may share an asset without duplicating its definition.
  Labels can change without breaking process references.
- **ProcessLink**: an ID and source/destination station IDs. It records intended
  flow only, not a working transport, robot program or manufacturing process.

JSON schema version 1 uses metres, world coordinates and scalar-first unit
quaternions. IDs are unique within each collection. Unknown references, duplicate
connections, invalid transforms and extra top-level/record fields are rejected.
Collections are stored in ID order, so reordering input does not invent an edit.

## Reuse a saved machine without opening a window

```sh
.venv/bin/python examples/factory_layout.py \
  --machine path/to/saved-machine.json \
  --output path/to/new-factory.json \
  --check-physics
```

Omit `--machine` to use the existing powered indexing-table assembly. The example
includes a floor, passive roller table and two instances of the machine. Output
files are created exclusively: an existing file is not overwritten. The optional
physics check compiles the ordinary Scene in MuJoCo, without rendering or opening
windows. Compilation does not check working height alignment, collision clearance,
reach, grasp success, process execution or throughput. Blueprint root poses,
actuation and dynamic/anchored settings are preserved exactly; mounting or grounding
is not silently inferred.

## Review an edit

```python
from pathlib import Path
from little_world.core.component import Transform
from little_world.factory.document import FactoryDocument
from little_world.factory.document_editor import FactoryEditor

layout = FactoryDocument.from_json(Path('factory.json').read_text())
editor = FactoryEditor(layout)
candidate = layout.move_station('work', Transform((0.4, 0.2, 0)))
proposal = editor.preview(candidate)
print(proposal.report())       # Exact station before/after and affected IDs
editor.apply(proposal)         # One transaction
editor.undo()
editor.redo()
```

Proposals can also be serialized with `to_json()` and read with
`DocumentProposal.from_json()`. Their base document and revision must still match;
manual edits, undo and redo invalidate older proposals. Preview never mutates the
current scene. No-op changes do not create history. History/revision is session
state; the saved document stores the authored layout.

`with_asset`, `with_station` and `with_link` add or update by stable ID. Replacing a
shared asset intentionally changes every referencing station; the review reports
all affected IDs and Blueprint content hashes. For a one-instance customization,
create a new asset ID and update only that station's reference. Asset removal is
blocked while referenced. Station removal is blocked while linked unless the caller
explicitly uses `remove_station(id, remove_links=True)`. Removal of links and the
station then occurs in the same immutable candidate and undo transaction.

`to_scene()` emits existing Entity objects with station IDs and embedded Blueprints.
It intentionally contains geometry and controls described by those Blueprints;
process links have no executor. The core, native physics adapter, fixed-cell editor,
and builder formats remain independent. The next UI step is to expose these same
transactions through station selection, drag placement and reviewed proposals.
