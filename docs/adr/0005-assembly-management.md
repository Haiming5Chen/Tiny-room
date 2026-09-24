# Assembly management in the workbench

The detailed hardware kit needs hierarchy selection and complete-module duplication.
Reuse the existing Body parent graph, immutable Blueprint and transactional editor.
A collapsible assembly browser and module/detail picking are UI concerns; cloning
resolves new stable IDs for descendants, joints, motors, cameras and fully contained
controller descriptors in the construction layer. No new solver or asset format.

Duplicate offsets the copied root in its parent frame. It preserves internal joints
and attachment frames, while controllers spanning outside the copied subtree are
not copied. Each duplicate/delete remains one undo operation. Workbench focus and
hierarchy expansion affect only presentation, never saved physics data.
