import ast
import hashlib
import json
import math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from pydantic import ValidationError
from tasks import TASK_IDS,HELDOUT_IDS,EXCLUDED_IDS,make_task,Problem,schedule_target,cash_target,selection_target,reactor_target,parallel_target,option_target
from reference import solve,program
from server import QuantEnvironment,QuantAction,calculate,grade,MAX_STEPS

@pytest.mark.parametrize('ident',TASK_IDS+HELDOUT_IDS+EXCLUDED_IDS)
@pytest.mark.parametrize('seed',range(20))
def test_independent_reference(ident,seed):
    p=make_task(ident,seed);ref=solve(p)
    assert set(ref)==set(p.targets)
    for key,value in p.targets.items(): assert math.isclose(ref[key],value,rel_tol=1e-9,abs_tol=1e-7),(ident,seed,key,ref[key],value)
    assert grade(p,json.dumps(ref))==1
    assert make_task(ident,seed)==p
    assert make_task(ident,seed+1).inputs!=p.inputs

@pytest.mark.parametrize('ident',TASK_IDS+HELDOUT_IDS+EXCLUDED_IDS)
def test_real_worker_reference(ident):
    p=make_task(ident,7105);result=calculate(program(p))
    assert result['ok'],result
    assert grade(p,json.dumps(ast.literal_eval(result['stdout'])))==1

@pytest.mark.parametrize('ident',TASK_IDS+HELDOUT_IDS+EXCLUDED_IDS)
def test_reward(ident):
    p=make_task(ident,707);truth=p.targets
    assert grade(p,json.dumps(truth))==1
    assert grade(p,json.dumps({k:v+1+abs(v) for k,v in truth.items()}))==0
    first=next(iter(truth));assert 0<grade(p,json.dumps({first:truth[first]}))<=.15
    assert grade(p,json.dumps({**truth,'extra':0}))==0
    bad=dict(truth);bad[first]+=1+abs(bad[first]);assert grade(p,json.dumps(bad))<=.15

@pytest.mark.parametrize('answer',['','null','[]','true','{"equity_npv":true}','{"equity_npv":"1"}', '{"equity_npv":NaN}','{"equity_npv":Infinity}','{"equity_npv":1,"equity_npv":2}','{"bogus":0}','{"equity_npv":{}}','{"equity_npv":[1]}'])
def test_invalid(answer): assert grade(make_task('leveraged-cashflows',5),answer)==0

@pytest.mark.parametrize('code',[
    'import os; print(os.environ)','import sys; print(sys.modules)','import socket','import subprocess','import pathlib',
    'import tasks','import server','import reference',"print(open('/app/tasks.py').read())", "print(__import__('tasks'))",
    'print(globals())','print(locals())',"print(eval('1+1'))","exec('print(42)')",'print(getattr(math,"pi"))',
    'print((1).__class__.__mro__)','print(print.__globals__)','print((lambda:0).__globals__)',
    "print('{0.__class__}'.format(1))",'print(f"{1}")','from math import __loader__','import math as __builtins__',
    'from math import *','print(task)','print(problem)','print(targets)','class A: pass','@print\ndef f(): pass',
    'print("a"*5000)','while True: pass'])
def test_blocked_or_bounded(code):
    result=calculate(code);assert not result['ok'],result
    assert '/Users/' not in str(result)


def test_hand_schedule_setup_release_ties():
    d=dict(jobs=[dict(duration=2,release=0,due=3,weight=2,family=0,after=[]),dict(duration=1,release=5,due=6,weight=1,family=1,after=[0])],setup=[[0,3],[2,0]])
    assert schedule_target(d)==dict(weighted_tardiness=3,makespan=9,job_at_0=0,job_at_1=1)
    d['jobs'][1].update(release=0,due=20,after=[]);d['setup']=[[0,0],[0,0]]
    assert schedule_target(d)['job_at_0']==0


def test_hand_cash_loss_revolver_final_distribution():
    d=dict(plant=120,working_capital=10,reserve=5,loan=60,loan_monthly_rate=0,revolver_monthly_rate=0,tax_rate=.25,annual_equity_discount=0,salvage=0,months=[dict(revenue=0,cost=10),dict(revenue=200,cost=10)])
    # First month: loss70, debt repayment30, draw40. Final taxable130 less carry70 => tax15.
    # Final available190-15-30+10=155; repay40; dividend115 plus reserve5.
    assert cash_target(d)==dict(equity_npv=45,total_tax=15,peak_revolver=40,total_net_distributions=120,ending_loss_carry=0)


def test_hand_selection_no_correlation():
    d=dict(groups=[dict(weight=1,disease=.2,z_if_disease=.5,z_if_healthy=.5,include_disease=.5,include_healthy=.5)],test_positive=[[.1,.1],[.9,.9]],observed=[1,1])
    out=selection_target(d)
    assert math.isclose(out['pattern_probability_among_selected'],.17)
    assert math.isclose(out['posterior_disease'],.162/.17)
    assert math.isclose(out['selection_probability'],.5)


def test_hand_reactor_reaction_conservation_and_replacement():
    d=dict(initial_volume_L=100,initial_A_mol=10,initial_B_mol=5,segments=[dict(minutes=10,in_L_min=0,out_L_min=0,feed_A_mol_L=0,k_per_min=.1,replace_fraction=.2,replace_A_mol_L=.3)])
    out=reactor_target(d);before_a=10/math.e;before_b=15-before_a
    assert math.isclose(out['final_A_mol'],.8*before_a+6,rel_tol=1e-10)
    assert math.isclose(out['final_B_mol'],.8*before_b,rel_tol=1e-10)
    assert math.isclose(out['total_B_discharged_mol'],.2*before_b,rel_tol=1e-10)
    assert math.isclose(sum((out['final_A_mol'],out['final_B_mol'],out['total_B_discharged_mol'])),21-.2*before_a)


def test_hand_parallel_dependencies():
    d=dict(jobs=[dict(duration=3,release=0,after=[]),dict(duration=4,release=0,after=[]),dict(duration=2,release=0,after=[0,1])])
    assert parallel_target(d)==dict(minimum_makespan=6,total_processing=9)


def test_hand_option_single_step():
    d=dict(spot=80,strike=100,rate=.08,**{'yield':0},volatility=.2,years=1,steps=1)
    out=option_target(d)
    assert out['american_put']>=20
    assert out['european_put']<=out['american_put']
    assert math.isclose(out['early_exercise_premium'],out['american_put']-out['european_put'])


def test_isolation_schema_lifecycle():
    a=QuantEnvironment();b=QuantEnvironment();obs=a.reset(task_id=TASK_IDS[0],seed=16);b.reset(task_id=TASK_IDS[1],seed=16)
    assert not obs.done and obs.reward==0 and a.state.step_count==0
    assert 'targets' not in obs.model_dump_json()
    assert calculate('x=5;print(x)')['stdout']=='5\n'
    assert not calculate('print(x)')['ok']
    assert calculate('import math; math.pi=999; print(math.pi)')['stdout']=='999\n'
    assert float(calculate('from math import pi; print(pi)')['stdout'])==math.pi
    with ThreadPoolExecutor(max_workers=5) as pool: assert all(v['ok'] for v in pool.map(calculate,['print(sum(range(10)))']*5))
    out=a.step(QuantAction(operation='python',code='print(2+3)'));assert not out.done and out.reward==0
    out=a.step(QuantAction(operation='submit',answer=json.dumps(a.problem.targets)))
    assert out.done and out.reward==1 and str(a.problem.targets) not in out.message
    assert a.step(QuantAction(operation='submit')).reward==1 and a.state.step_count==2 and not b.ended
    a.reset(task_id=TASK_IDS[1],seed=16)
    for _ in range(MAX_STEPS): out=a.step(QuantAction(operation='python',code='pass'))
    assert out.done and out.reward==0 and out.steps_left==0
    seeds=[a.reset().message for _ in range(6)];assert len(set(seeds))==6
    with pytest.raises(ValueError): a.reset(task_id='unknown')
    with pytest.raises(ValidationError): QuantAction(operation='read')
    with pytest.raises(ValidationError): QuantAction(operation='python',code='a'*16001)
    assert not set(TASK_IDS)&set(HELDOUT_IDS)
    a.close();b.close()


def test_v1_preserved():
    root=Path(__file__).resolve().parent.parent
    for path,digest in json.loads(Path('v1-preservation.json').read_text()).items(): assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
