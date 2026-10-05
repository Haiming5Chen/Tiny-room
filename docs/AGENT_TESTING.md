# Testing Little World through structured state

The test agent does not need to infer state from rendered pixels. It reads the
actual app's labeled controls, form values/errors, immutable recipe, proposal,
revision, history depths, physical product pose and controller outcome. It chooses
explicit actions and asserts observable results. This is a test-only interface;
it creates an isolated disposable app with a hidden window and cannot attach to personal unsaved work.

## Run a replay

```sh
.venv/bin/python -m little_world.testing.semantic \
  tests/scenarios/cell_edit_and_run.json \
  --report build/agent-tests/cell_edit_and_run.json
```

The command creates a hidden native test window (no popup or focus stealing), uses a temporary save directory, closes it
on completion, and writes JSON with every action, before/after state, expected
errors, failures and overall status. A failed scenario exits nonzero. Neither a
network model nor an API key is needed. Codex/Claude can author a scenario, execute
this command, inspect the report, then revise or extend the scenario. Reports can
contain full state, so keep console output to summaries and failing steps.

## Supported actions

- `observe`: read detached JSON state.
- `click` with exact `label`: call exactly one visible enabled control's actual
  callback. Ambiguous/missing labels and disabled controls fail.
- `fill` with exact `field` and text `value`: send characters through the actual
  form input handler; verify that all requested text was accepted.
- `propose` with a complete `request` or a `changes` array: use the production
  request parser and review operation. An optional `revision` tests stale edits.
- `advance` with `seconds` (0 < value <= 60): step actual MuJoCo and production
  controllers deterministically, stopping when the app pauses. No wall-time sleep,
  pose assignment or fake success result is used.
- `expect` with an `equals` mapping and/or a `between` mapping: assert dotted paths
  in the snapshot. Array indices are numeric path segments. These are deterministic
  assertions, not a language model's opinion of whether its action succeeded.

Actions can include `error_contains` for a specifically expected rejection.
Unexpected errors or failed assertions stop the scenario and retain a failing
trace. A deliberate wrong-expectation regression checks that the harness really
fails and does not execute later actions.

Example:

```json
{"name":"Reject a disabled control", "actions":[
  {"op":"click", "label":"Undo", "error_contains":"disabled"},
  {"op":"expect", "equals":{"revision":0,"undo_depth":0}}
]}
```

Snapshots follow the active workspace. Layout snapshots expose station/link records,
selection, revision and undo/redo availability; Anime snapshots expose the authored
Blueprint. `propose` remains specific to Robot lab. The
`tests/scenarios/layout_edit_and_reuse.json` replay exercises precise station poses,
mode switching, machine reuse, flow links, linked deletion, undo and saving.

## Coverage and interpretation

The supplied agent-authored scenarios exercise editable forms, review before apply,
undo/redo, invalid requests, ambiguous object IDs, stale proposals, teaching names,
saved positions, physical lift and observed placement in the target bin. Physical
placement is checked against coordinates independently of the completion label.
Seeded adversarial tests add 1,200 valid edit transactions, 80 invalid batches,
malformed wire formats, invalid units/frames and numerically extreme input.
An integer overflow found by those tests now returns a controlled ValueError.

The native driver invokes UI callbacks, not operating-system mouse events. Existing
native drag tests separately cover projection, cursor movement and drops. Screenshots
remain necessary for appearance, readability and visual artifacts. Deterministic
stepping also does not measure interactive frame rate or latency. No natural-language
provider is connected: these results are NOT evidence of prompt comprehension or
arbitrary factory generation. When an AI authoring provider exists, its output must
run through this same parser and independent assertions; do not grade it by its own
explanation. Exported scenarios and reports make failures reproducible by either
agent without assigning work or changing the user's live app.

## Regression commands

```sh
.venv/bin/python -m pytest tests/test_adversarial_changes.py -q
LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest tests/test_semantic_testing.py -q
LITTLE_WORLD_TEST_RENDER=1 .venv/bin/python -m pytest -q
```

Native tests use hidden windows by default and need a working GLFW/OpenGL desktop. They are opt-in on headless CI.
