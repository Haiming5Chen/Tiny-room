import json
import os
from pathlib import Path
import pytest
from little_world.testing.semantic import value_at


def test_semantic_paths_are_data_not_expressions():
    assert value_at({'positions':[[1,2]]},'positions.0.1')==2
    with pytest.raises(KeyError):value_at({},'__import__("os")')

@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires native window')
@pytest.mark.parametrize('file',sorted((Path(__file__).parent/'scenarios').glob('*.json')),ids=lambda p:p.stem)
def test_replay_agent_scenarios(file,tmp_path):
    from little_world.testing.semantic import run_scenario
    report=run_scenario(json.loads(file.read_text()))
    (tmp_path/'trace.json').write_text(json.dumps(report,indent=2))
    assert report['initial']['window_visible'] is False
    assert report['passed'],json.dumps(report.get('fatal') or [s for s in report['steps'] if not s['passed']],indent=2)

@pytest.mark.skipif(os.environ.get('LITTLE_WORLD_TEST_RENDER')!='1',reason='requires native window')
def test_wrong_expectation_reports_failure_and_stops():
    from little_world.testing.semantic import run_scenario
    report=run_scenario(dict(actions=[{'op':'expect','equals':{'revision':999}},{'op':'click','label':'Tall block'}]))
    assert not report['passed'] and len(report['steps'])==1
    assert report['steps'][0]['error']['type']=='AssertionError'
    assert report['final']['recipe']['product']=='Small block'
