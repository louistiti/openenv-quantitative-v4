import ast
import hashlib
import json
from pathlib import Path
import pytest
from tasks import TASK_IDS,HELDOUT_IDS,EXCLUDED_IDS,make_task
from server import QuantEnvironment,calculate
from budget import Budget,CAP
from qualify_model import gate
from smoke_model import WORKLIST

def test_narrowed_default_only_and_preservation():
    here=Path(__file__).resolve().parent;v3=here.parent/'v3'
    for name,digest in json.loads((here/'v3-preservation.json').read_text()).items():assert hashlib.sha256((v3/name).read_bytes()).hexdigest()==digest,name
    def tree_without_sampling(path):
        text=path.read_text()
        old_guard="if task_id not in TASK_IDS+HELDOUT_IDS: raise ValueError('Unknown task_id')"
        new_guard="if task_id not in TASK_IDS+HELDOUT_IDS+EXCLUDED_IDS: raise ValueError('Unknown task_id')"
        assert text.count(new_guard if path.parent==here else old_guard)==1
        tree=ast.parse(text.replace(new_guard,old_guard))
        tree.body=[n for n in tree.body if not (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('TASK_IDS','EXCLUDED_IDS'))]
        return ast.dump(tree)
    assert tree_without_sampling(here/'tasks.py')==tree_without_sampling(v3/'tasks.py')
    for name in ('server.py','worker.py','reference.py','requirements.txt','budget.py'):assert (here/name).read_bytes()==(v3/name).read_bytes(),name
    assert TASK_IDS==('constrained-schedule','selected-testing')
    assert not set(TASK_IDS)&(set(HELDOUT_IDS)|set(EXCLUDED_IDS))
    env=QuantEnvironment()
    for seed in range(100):
        env.reset(seed=seed);assert env.problem.task_id in TASK_IDS
    prior_ids=ast.literal_eval(next(n.value for n in ast.parse((v3/'tasks.py').read_text()).body if isinstance(n,ast.Assign) and n.targets[0].id=='TASK_IDS'))
    assert set(TASK_IDS+EXCLUDED_IDS)==set(prior_ids)
    for ident in TASK_IDS+HELDOUT_IDS+EXCLUDED_IDS:env.reset(task_id=ident,seed=9)
    env.close()

def test_worklist_and_freshness():
    assert len(WORKLIST)==len(set(WORKLIST))==12
    prior=json.loads((Path(__file__).resolve().parent.parent/'v3'/'generalization-smoke.json').read_text())['worklist']
    assert not set(WORKLIST)&set(map(tuple,prior))
    assert all(sum(t==i for t,s in WORKLIST)==4 for i in TASK_IDS)
    assert all(sum(t==i for t,s in WORKLIST)==2 for i in HELDOUT_IDS)

def base_rows():
    return [dict(task_id=t,seed=s,heldout=t in HELDOUT_IDS,outcome='success' if (t in TASK_IDS and s<794121) or (t==HELDOUT_IDS[0] and s==894101) else 'wrong_answer',answer_delivered=True,completion_accounted=2000) for t,s in WORKLIST]

def test_gate_valid():assert gate(base_rows())['gate_passed']

@pytest.mark.parametrize('mode',['incomplete','allcorrect','nonmixed','heldoutnone','resources'])
def test_gate_rejects(mode):
    rows=base_rows()
    if mode=='incomplete':rows.pop()
    elif mode=='allcorrect':
        for r in rows:r['outcome']='success'
    elif mode=='nonmixed':
        for r in rows:
            if not r['heldout'] and r['task_id']==TASK_IDS[0]:r['outcome']='success'
    elif mode=='heldoutnone':
        for r in rows:
            if r['heldout']:r['outcome']='wrong_answer'
    elif mode=='resources':
        for r in rows[-2:]:r['outcome']='wall_time';r['answer_delivered']=False
    assert not gate(rows)['gate_passed']

@pytest.mark.parametrize('code,expected',[
 ('from itertools import permutations; print(len(list(permutations(range(4)))))','24'),
 ('def f():\n x=0\n def g():\n  nonlocal x\n  x+=1\n g()\n return x\nprint(f())','1')])
def test_repaired_calculator(code,expected):
    result=calculate(code);assert result['ok'] and result['stdout'].strip()==expected

def test_budget_guard():
    b=Budget();assert b.remaining==8152
    b.generation(3000);b.observation('{"done":false}')
    assert b.remaining>2048
    with pytest.raises(ValueError):b.generation(b.remaining+1)
    b.generation(b.remaining);assert b.used==CAP and b.remaining==0
    b.observation('terminal');assert b.used>CAP
