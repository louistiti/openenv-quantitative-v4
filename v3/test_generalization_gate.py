import copy
import json
from pathlib import Path
import pytest
from generalization_screen import WORKLIST,gate
from tasks import TASK_IDS,HELDOUT_IDS

def rows():
    return [dict(task_id=t,seed=s,heldout=t in HELDOUT_IDS,outcome='success' if ((t in TASK_IDS[:2] and s<594121) or (t==HELDOUT_IDS[0] and s==694101)) else 'wrong_answer',answer_delivered=True,completion_accounted=2000) for t,s in WORKLIST]

def test_fixed_scope_and_freshness():
    assert len(WORKLIST)==len(set(WORKLIST))==20
    assert all(sum(t==ident for t,s in WORKLIST)==4 for ident in TASK_IDS)
    assert all(sum(t==ident for t,s in WORKLIST)==2 for ident in HELDOUT_IDS)
    diagnostic=json.loads(Path('model-smoke.json').read_text())['worklist']
    assert not set(WORKLIST)&set(map(tuple,diagnostic))
    assert [t for t,s in WORKLIST[:6]]==list(TASK_IDS)+list(HELDOUT_IDS)

def test_gate_valid():
    result=gate(rows());assert result['gate_passed'] and result['training_solved']==4 and result['mixed_training_families']==2

@pytest.mark.parametrize('mode',['incomplete','all_correct','one_mixed','no_heldout','infrastructure','budget'])
def test_gate_rejects_unqualified(mode):
    r=rows()
    if mode=='incomplete':r.pop()
    elif mode=='all_correct':
        for x in r:x['outcome']='success'
    elif mode=='one_mixed':
        for x in r:
            if not x['heldout']:x['outcome']='success' if x['task_id']==TASK_IDS[0] or (x['task_id']==TASK_IDS[1] and x['seed']<594121) else 'wrong_answer'
    elif mode=='no_heldout':
        for x in r:
            if x['heldout']:x['outcome']='wrong_answer'
    elif mode=='infrastructure':
        for x in r[-3:]:x['outcome']='wall_time';x['answer_delivered']=False
    elif mode=='budget':
        for x in r[-3:]:x['completion_accounted']=8193
    assert not gate(r)['gate_passed']
