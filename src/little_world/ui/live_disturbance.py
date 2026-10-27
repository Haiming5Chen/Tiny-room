"""Watch what the sweeps measured: a disturbance that happens in the window, during a run (ADR 0055).

The sweeps disturb a field's runs in another process and report counts (ADR 0030); here the
same disturbance - the cube moved after the program looked, a shove, a camera that freezes -
happens in the window while the user watches, on the same trigger: after a goal is met, once
the machine has stood still that long, after its delay. Armed for the next run, it stays armed
until cleared, and the window says when it happened. A workshop mixin.
"""
from little_world.fields.disturbance import DEFAULTS, WEAK, Disturbing


class LiveDisturbance:
    def init_live_disturbance(self):
        self.live_disturbance = None    # the disturbance the next runs get, or None
        self.live_kick = None           # applying it, during a run
        self.live_note = ''             # what happened, said in the run panel

    def live_choices(self):
        """The field's own disturbances, the ones its sweeps try, and a motor run hot (ADR 0058)."""
        field = getattr(self, 'field_id', '')
        return tuple(DEFAULTS.get(field, ())) + tuple(WEAK.get(field, ()))

    def arm_disturbance(self, label):
        """Disturb the coming runs with the field's disturbance called `label`; None clears it."""
        if label is None:
            self.live_disturbance = self.live_kick = None
            self.live_note = ''
            return
        chosen = next((d for d in self.live_choices() if d.label == label), None)
        if chosen is None:
            raise ValueError(f'The {getattr(self, "field_id", "")} field has no disturbance called {label!r}')
        self.live_disturbance, self.live_kick, self.live_note = chosen, None, ''

    def tick_live_disturbance(self):
        """One physics step of a run: the armed disturbance, on its trigger."""
        d = self.live_disturbance
        tracker = getattr(self, 'goal_tracker', None)
        if d is None or tracker is None or self.state is None or tracker.start is None:
            return
        if self.live_kick is None:
            root = next((b.id for b in self.editor.bodies if b.parent is None), None)
            if root is None:
                return
            self.live_kick = Disturbing(d, 'machine/' + root)
        kick = self.live_kick
        if kick.camera is None:
            kick.camera = getattr(self, 'eye', None)     # the program's camera, once it has one
        was = kick.began
        kick.tick(self.backend, self.state, self.state.time - tracker.start, tracker.met)
        if was is None and kick.began is not None:
            self.live_note = f'{d.label} - at {kick.began:.1f} s'
            self.status = f'Disturbed: {d.label}. Watch what the machine does.'

    def end_live_disturbance(self):
        """A run ended: the next one is disturbed afresh."""
        self.live_kick = None
