"""OpenEnv quantitative calculation workbench with terminal outcome verification."""
import json
import math
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from typing import Literal
from uuid import uuid4

from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field
from tasks import TASK_IDS, make_task

MAX_STEPS=16
WORKER=Path(__file__).with_name('worker.py').resolve()

class QuantAction(Action):
    operation: Literal['python','submit'] = Field(description='python executes a fresh bounded calculation; submit grades answer once and ends. No intermediate correctness feedback.')
    code: str = Field(default='',max_length=16000,description='Python code for python operation, print numeric results. Fresh process every call. math/statistics imports, loops, comprehensions, functions and common numeric/list/dict builtins available. No filesystem/network, introspection, eval/exec, numpy, scipy, json, f-strings, string formatting, classes or private attributes. Limit 3 CPU seconds and 4000 output characters. Use print(dict(...)) to inspect results; variables do not persist.')
    answer: str = Field(default='',max_length=6000,description='For submit: JSON object text with exactly the required numeric keys and finite numeric values. No strings, booleans, lists or extra keys. Do not round aggressively. Empty answer submits no solution. All required correct => reward 1; otherwise at most 0.15 proportional numeric credit.')

class QuantObservation(Observation):
    task_id: str = ''
    message: str = ''
    steps_left: int = MAX_STEPS


def calculate(code):
    with tempfile.TemporaryDirectory(prefix='quant-calc-') as cwd:
        try:
            p=subprocess.run([sys.executable,'-I',str(WORKER)],input=code,text=True,capture_output=True,
                             cwd=cwd,timeout=5,env={'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'})
            if p.returncode or len(p.stdout)>12000: return {'ok':False,'error':'Calculation resource limit or process failure'}
            result=json.loads(p.stdout)
            if not isinstance(result,dict): raise ValueError('Invalid worker result')
            return result
        except (subprocess.TimeoutExpired,ValueError,OSError):
            return {'ok':False,'error':'Calculation timeout or unavailable result'}


def unique_pairs(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValueError('Duplicate key')
        d[k]=v
    return d


def grade(problem,answer):
    try:
        obj=json.loads(answer,object_pairs_hook=unique_pairs,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite')))
        if not isinstance(obj,dict) or not obj or set(obj)-set(problem.targets): return 0.0
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in obj.values()): return 0.0
        correct=sum(k in obj and math.isclose(obj[k],v,rel_tol=1e-5,abs_tol=1e-4) for k,v in problem.targets.items())
        if correct==len(problem.targets) and set(obj)==set(problem.targets): return 1.0
        return 0.15*correct/len(problem.targets)
    except (ValueError,TypeError,OverflowError,RecursionError): return 0.0

class QuantEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS=True
    def __init__(self):
        self.problem=None;self.ended=False;self.last_reward=0.0
        self._state=State(episode_id=str(uuid4()),step_count=0)
    @property
    def state(self): return self._state
    def close(self): pass
    def reset(self,seed=None,task_id=None,**kwargs):
        actual_seed=secrets.randbits(63) if seed is None else seed
        if task_id is None: task_id=TASK_IDS[actual_seed%len(TASK_IDS)]
        self.problem=make_task(task_id,actual_seed)
        self.ended=False;self.last_reward=0.0
        self._state=State(episode_id=str(uuid4()),step_count=0)
        return QuantObservation(task_id=task_id,message=self.problem.instruction,reward=0.0,done=False)
    def step(self,action,**kwargs):
        if self.problem is None: self.reset()
        if self.ended: return QuantObservation(task_id=self.problem.task_id,message='Episode ended; reset required',reward=self.last_reward,done=True,steps_left=0)
        self._state.step_count+=1
        if action.operation=='python': message=json.dumps(calculate(action.code))
        else: message=''
        self.ended=action.operation=='submit' or self._state.step_count>=MAX_STEPS
        if self.ended:
            self.last_reward=grade(self.problem,action.answer) if action.operation=='submit' else 0.0
            message='Final answer graded. Episode ended; no target values or per-key feedback.'
        return QuantObservation(task_id=self.problem.task_id,message=message,reward=self.last_reward if self.ended else 0.0,
                                done=self.ended,steps_left=max(0,MAX_STEPS-self._state.step_count))

app=create_app(QuantEnvironment,QuantAction,QuantObservation,env_name='quantitative_reasoning_lab',max_concurrent_envs=5)
