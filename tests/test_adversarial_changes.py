"""Deterministic adversarial cases with independent expectations and invariants."""
import json
import random
import pytest
from little_world.factory.changes import CellChange,CellRequest,preview_changes
from little_world.factory.recipe import CellRecipe

@pytest.mark.parametrize('seed',range(80))
def test_random_valid_edit_sequences_preserve_unrelated_fields(seed):
    rng=random.Random(seed);original=CellRecipe();recipe=original;revision=0
    for _ in range(15):
        point=(rng.uniform(.36,.50),rng.uniform(-.025,.025))
        req=CellRequest(recipe,revision,(CellChange('tray','input',point),))
        frozen=recipe.to_json();p=preview_changes(recipe,revision,CellRequest.from_json(req.to_json()))
        assert recipe.to_json()==frozen
        changed=p.apply(recipe,revision)
        assert changed.point('input')==point
        assert changed.positions[1:]==original.positions[1:]
        assert (changed.source,changed.destination,changed.product)==(original.source,original.destination,original.product)
        with pytest.raises(ValueError):p.apply(changed,revision+1)
        recipe=changed;revision+=1

@pytest.mark.parametrize('seed',range(80))
def test_invalid_batch_cannot_partially_apply(seed):
    rng=random.Random(seed);recipe=CellRecipe()
    point=(rng.uniform(1,50),rng.uniform(-50,50))
    request=CellRequest(recipe,0,(CellChange('product','product','Tall block'),CellChange('tray','input',point)))
    with pytest.raises(ValueError):preview_changes(recipe,0,request)
    assert recipe==CellRecipe()

@pytest.mark.parametrize('value',[None,True,False,0,1.2,'input',{},[],[1],[1,2,3],['0.4',0],[[1],0],[float('inf'),0],[float('nan'),0],[10**500,0]])
def test_malformed_coordinates_are_controlled_errors(value):
    recipe=CellRecipe();request=CellRequest(recipe,0,(CellChange('tray','input',value),))
    with pytest.raises(ValueError):preview_changes(recipe,0,request)

@pytest.mark.parametrize('target',['left','that tray','blue','INPUT','conveyor','robot',None,{},0])
def test_ambiguous_or_unknown_targets_are_not_guessed(target):
    recipe=CellRecipe()
    with pytest.raises(ValueError):preview_changes(recipe,0,CellRequest(recipe,0,(CellChange('tray',target,(.4,0)),)))

@pytest.mark.parametrize('field,value',[('changes',None),('changes',{}),('changes',[None]),('changes',[{}]),('base',None),('base',[]),('revision',True),('revision',1.5),('revision',-1),('frame','local'),('units','cm')])
def test_malformed_wire_requests_rejected(field,value):
    wire=json.loads(CellRequest(CellRecipe(),0,()).to_json());wire[field]=value
    with pytest.raises(ValueError):CellRequest.from_json(json.dumps(wire))
