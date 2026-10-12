import ast
from concurrent.futures import ThreadPoolExecutor
import json
import math
import pytest
from pydantic import ValidationError
from tasks import TASK_IDS,HELDOUT_IDS,make_task
from oracle import solve,program
from server import QuantEnvironment,QuantAction,calculate,grade,MAX_STEPS

@pytest.mark.parametrize('ident',TASK_IDS+HELDOUT_IDS)
@pytest.mark.parametrize('seed',range(20))
def test_independent_reference(ident,seed):
    p=make_task(ident,seed);reference=solve(ident,p.inputs)
    assert set(reference)==set(p.targets)
    for k,v in p.targets.items(): assert math.isclose(reference[k],v,rel_tol=1e-9,abs_tol=1e-7),(ident,seed,k,reference[k],v)
    assert grade(p,json.dumps(reference))==1
    assert make_task(ident,seed)==p
    assert make_task(ident,seed+1).inputs!=p.inputs

@pytest.mark.parametrize('ident',TASK_IDS+HELDOUT_IDS)
def test_reference_through_real_calculation_worker(ident):
    p=make_task(ident,7123);result=calculate(program(p))
    assert result['ok'],result
    assert grade(p,json.dumps(ast.literal_eval(result['stdout'])))==1

@pytest.mark.parametrize('code',[
    'import os; print(os.environ)', 'import sys; print(sys.modules)', 'import socket',
    'import subprocess', 'import pathlib', 'import tasks', 'import server',
    "print(open('/app/tasks.py').read())", "print(__import__('tasks'))", 'print(globals())',
    'print(locals())', "print(eval('1+1'))", "exec('print(42)')", 'print(getattr(math,"pi"))',
    'print((1).__class__.__mro__)', 'print(print.__globals__)', 'print((lambda:0).__globals__)',
    "print('{0.__class__}'.format(1))", 'print(f"{1}")', 'from math import __loader__',
    'import math as __builtins__', 'from math import *', 'print(task)', 'print(problem)',
    'print(targets)', 'class A: pass', '@print\ndef f(): pass',
    'print("a"*5000)', 'while True: pass',
])
def test_blocked_or_bounded(code):
    result=calculate(code)
    assert not result['ok'],result
    assert 'targets' not in result.get('stdout','')
    assert '/Users/' not in str(result)

@pytest.mark.parametrize('answer',['','null','[]','true','{"x":true}','{"x":"1"}',
    '{"x":NaN}','{"x":Infinity}','{"x":1,"x":2}','{"x":1,"bogus":0}','{"x":{}}','{"x":[1]}'])
def test_invalid_answer(answer):
    assert grade(make_task('resource-allocation',5),answer)==0

@pytest.mark.parametrize('ident',TASK_IDS+HELDOUT_IDS)
def test_reward_separation(ident):
    p=make_task(ident,4);truth=p.targets
    assert grade(p,json.dumps(truth))==1
    assert grade(p,json.dumps({k:v+1+abs(v) for k,v in truth.items()}))==0
    first=next(iter(truth));partial={first:truth[first]}
    assert 0<grade(p,json.dumps(partial))<=.15
    assert grade(p,json.dumps({**truth,'extra':0}))==0
    changed=dict(truth);changed[first]+=1+abs(changed[first]);assert grade(p,json.dumps(changed))<=.15


def test_worker_state_isolation_and_math():
    assert calculate('x=13; print(sum(i*i for i in range(5)))')['stdout']=='30\n'
    assert not calculate('print(x)')['ok']
    assert calculate('import math; math.pi=999; print(math.pi)')['stdout']=='999\n'
    assert float(calculate('from math import pi; print(pi)')['stdout'])==math.pi
    assert calculate('import statistics; print(statistics.mean([1,2,3]))')['stdout']=='2\n'
    with ThreadPoolExecutor(max_workers=5) as pool:
        assert all(x['ok'] for x in pool.map(calculate,['print(sum(range(10)))']*5))


def test_lifecycle_and_no_feedback():
    env=QuantEnvironment();initial=env.reset(task_id=TASK_IDS[0],seed=7)
    assert not initial.done and initial.reward==0 and env.state.step_count==0
    assert 'targets' not in initial.model_dump_json()
    out=env.step(QuantAction(operation='python',code='print(2+3)'))
    assert not out.done and out.reward==0 and env.state.step_count==1
    out=env.step(QuantAction(operation='submit',answer=json.dumps(env.problem.targets)))
    assert out.done and out.reward==1 and str(env.problem.targets) not in out.message
    assert env.step(QuantAction(operation='submit')).reward==1 and env.state.step_count==2
    env.reset(task_id=TASK_IDS[1],seed=5)
    for _ in range(MAX_STEPS): out=env.step(QuantAction(operation='python',code='pass'))
    assert out.done and out.reward==0 and out.steps_left==0
    assert env.reset().reward==0
    env.close();env.close()


def test_reset_isolation_and_schema():
    a=QuantEnvironment();b=QuantEnvironment();a.reset(task_id=TASK_IDS[0],seed=1);b.reset(task_id=TASK_IDS[1],seed=1)
    assert a.problem.task_id!=b.problem.task_id
    a.step(QuantAction(operation='submit',answer=json.dumps(a.problem.targets)));assert not b.ended
    seeds=[a.reset(task_id=TASK_IDS[0]).message for _ in range(6)];assert len(set(seeds))==6
    with pytest.raises(ValueError): a.reset(task_id='unknown')
    with pytest.raises(ValidationError): QuantAction(operation='read')
    with pytest.raises(ValidationError): QuantAction(operation='python',code='a'*16001)
    assert len(TASK_IDS)==16 and not set(TASK_IDS)&set(HELDOUT_IDS)
