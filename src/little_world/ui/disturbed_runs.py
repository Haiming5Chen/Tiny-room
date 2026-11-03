"""Repeat a field run with disturbances, from its run report (ADR 0030, OPEN LW-018).

A workshop mixin beside `VariedRuns`. The design and the set-ups its sweep draws are run
undisturbed and under each of the field's disturbances - a shove, a part moved - in another
Python process (`little_world.inventory.sweep --disturb`), so the window stays live; the
report then shows, per disturbance, in how many set-ups every goal was met, how much later,
and how many of the drawn set-ups that succeeded undisturbed it broke (ADR 0036). The design
is copied into the other process; nothing here edits it.
"""
from pathlib import Path
import sys
import tempfile

from little_world.fields.disturbance import DEFAULTS
from little_world.inventory.sweep import PROTOCOLS, disturbed_from_json, disturbed_markdown, ranges_for, setups, summaries
from .varied_runs import ACCENT, JOBS, LIGHT, MUTED, WARN, finished, halt, launch


class DisturbedRuns:
    def init_disturbed_runs(self):
        # One set of disturbed repeats: field, the design they were made from, the process
        # and its progress, then what it wrote - or why it stopped.
        self.disturbing = None

    def disturbable(self, field):
        return field in PROTOCOLS and field in DEFAULTS

    def disturb_command(self, field, design, out, name):
        return [sys.executable, '-m', 'little_world.inventory.sweep', field, '--design', str(design), '--disturb',
                '--json', str(out), '--name', name, '--jobs', str(JOBS)]

    def start_disturbances(self):
        record = self.run_report
        if record is None or not self.disturbable(record.field):
            raise ValueError('Nothing is defined to disturb this field')
        self.stop_disturbances()            # one set at a time
        folder = Path(tempfile.mkdtemp(prefix='little-world-disturbed-'))
        design = folder / 'design.json'
        design.write_text(self.editor.blueprint.to_json(), encoding='utf-8')
        out = folder / 'disturbed.json'
        name = self.path.stem if getattr(self, 'path', None) else 'design'
        total = len(setups(ranges_for(record.field))) * (1 + len(DEFAULTS[record.field]))
        state = launch(self.disturb_command(record.field, design, out, name), total)
        state.update(field=record.field, run=record.number, blueprint=self.editor.blueprint, out=out)
        self.disturbing = state
        self.status = (f'Repeating run {record.number} with {len(DEFAULTS[record.field])} disturbances '
                       f'({total} runs) in the background.')

    def stop_disturbances(self):
        halt(self.disturbing)
        self.disturbing = None

    def poll_disturbances(self):
        d = self.disturbing
        if finished(d, disturbed_from_json, 'disturbed repeats'):
            groups = summaries(d['result'])
            held = sum(1 for g in groups[1:] if g.met == g.runs)
            self.status = (f'Disturbed run {d["run"]}: every goal met through {held} of {len(groups) - 1} '
                           'disturbances in every set-up.')

    def copy_disturbances_report(self):
        import glfw
        glfw.set_clipboard_string(None, disturbed_markdown(self.disturbing['result']))
        self.status = 'The report of the disturbed repeats is on the clipboard (Markdown).'

    def draw_disturbances(self, ui, button, text, section, y, wh):
        """Below the variations: the button, then progress, then a line per disturbance -
        drawn only while there is room above the session's list."""
        record = self.run_report
        d = self.disturbing
        if record is None or not self.disturbable(record.field):
            return y
        if d is None or d['field'] != record.field or d['blueprint'] is not self.editor.blueprint:
            if y + 54 > wh - 40:
                return y
            chosen = setups(ranges_for(record.field))
            drawn = sum(1 for v in chosen if v.label.startswith('repeat'))      # the pairs a test can read (ADR 0036)
            total = len(chosen) * (1 + len(DEFAULTS[record.field]))
            button(f'Repeat with disturbances ({total} runs)', 12, y, 264, self.start_disturbances, h=28)
            text('shoved, or a part moved, partway', 16, y + 34, 10, MUTED, 256)
            # What the pairs can show before they are run (FR-039): each set-up against itself.
            from little_world.inventory.power import to_show
            need = to_show(drawn)
            text(f'to be sure it breaks runs, it must break {need} of the {drawn} drawn' if need else
                 f'{drawn} drawn set-ups are too few to be sure of any', 16, y + 48, 10, MUTED, 256)
            return y + 68
        section(f'RUN {d["run"]} DISTURBED  /  shoved, moved', y)
        y += 22
        if d['error']:
            text('Could not repeat: ' + d['error'], 16, y, 11, WARN, 256)
            button('Try again', 12, y + 18, 264, self.start_disturbances, h=26)
            return y + 52
        if d['result'] is None:
            done, total = d['done'], max(1, d['total'])
            text(f'{done} of {total} runs', 16, y, 12, LIGHT, 256)
            ui.rect(16, y + 20, 256, 6, (.14, .19, .23))
            ui.rect(16, y + 20, 256 * done / total, 6, ACCENT)
            button('Stop disturbing', 12, y + 34, 264, self.stop_disturbances, h=26, tone='danger')
            return y + 70
        for g in summaries(d['result']):
            if y > wh - 110:
                break
            later = '' if g.change is None or abs(g.change) < .05 else f'  {g.change:+.1f} s'
            # Each drawn set-up against itself undisturbed (ADR 0036): what the event broke.
            broke = f'  broke {g.broke} of {g.held}' if g.broke else ''
            text(f'{g.met}/{g.runs}', 16, y, 11, ACCENT if g.met == g.runs else WARN)
            text(g.label + later + broke, 52, y, 11, LIGHT, 220)
            y += 17
            for said in g.where.split('; ') if g.where else ():
                if y > wh - 110:
                    break
                text(said, 52, y - 3, 10, MUTED, 220)       # where its runs failed (FR-038)
                y += 13
        button('Copy the disturbances report', 12, y + 4, 264, self.copy_disturbances_report, h=26)
        return y + 38
