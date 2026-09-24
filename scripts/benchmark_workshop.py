"""Bounded real-window responsiveness check; reports measurements, not guarantees."""
import json
import statistics
import time
from little_world.ui.workshop import Workshop

import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--hardware',action='store_true')
args=parser.parse_args()
from little_world.robots.mobile_platform import mobile_platform_blueprint
app=Workshop('/tmp/little-world-benchmark-unused.json',mobile_platform_blueprint() if args.hardware else None)
if args.hardware:
    app.open_bench()
draw=app.draw
frames={'build':[], 'simulate':[]}
draw_times=[]
edits=[]
starts=[]
count=0


def measured_draw():
    global count
    count+=1
    app.last_input=time.monotonic()
    (app.bench_camera if app.bench_open else app.camera).azimuth+=.15
    if count in (50,70,90):
        before=time.perf_counter()
        app.edit(lambda:app.editor.move((.01,0,0)))
        edits.append((time.perf_counter()-before)*1000)
    if count==120:
        before=time.perf_counter()
        app.close_bench()
        app.simulate()
        starts.append((time.perf_counter()-before)*1000)
        app.controls.press('W')
    if count>10:
        frames['build' if app.building else 'simulate'].append(time.perf_counter())
    before=time.perf_counter()
    draw()
    draw_times.append((time.perf_counter()-before)*1000)


app.draw=measured_draw
app.run(seconds=7)
result={'median_draw_ms':round(statistics.median(draw_times[10:]),2),
        'edit_ms':[round(v,2) for v in edits],'start_ms':[round(v,2) for v in starts]}
for mode,values in frames.items():
    intervals=[(b-a)*1000 for a,b in zip(values,values[1:])]
    if intervals:
        result[mode]={'frames':len(values),'fps':round(1000/statistics.mean(intervals),1),
                      'median_frame_ms':round(statistics.median(intervals),2),
                      'p95_frame_ms':round(sorted(intervals)[int(.95*len(intervals))],2)}
print(json.dumps(result,indent=2))
