import hashlib
import json
from pathlib import Path
import pytest
from server import calculate
from budget import Budget,CAP,FRAMING_RESERVE

@pytest.mark.parametrize('code,expected',[
 ('from itertools import permutations; print(len(list(permutations(range(4)))))','24'),
 ('import itertools; print(list(itertools.product([1,2],repeat=2)))','[(1, 1), (1, 2), (2, 1), (2, 2)]'),
 ('from itertools import chain; print(list(chain.from_iterable([[1],[2]])))','[1, 2]'),
 ('def f():\n x=0\n def g():\n  nonlocal x\n  x+=1\n g()\n return x\nprint(f())','1')])
def test_numerical_repairs(code,expected):
    result=calculate(code);assert result['ok'] and result['stdout'].strip()==expected,result

@pytest.mark.parametrize('code',[
 'import itertools as _it','from itertools import __loader__',
 'print(itertools.__dict__)','from itertools import os','from math import from_iterable',
 'def f():\n nonlocal _secret',
 'from itertools import chain; print(chain.__call__)',
 'from itertools import count; print(count().__reduce__())',
 'from itertools import repeat; print(next(repeat(open)))'])
def test_new_capabilities_do_not_expose_private_or_host(code):
    result=calculate(code);assert not result['ok'],result
    assert len(result.get('detail',''))<=240
    assert '/Users/' not in json.dumps(result) and 'Traceback' not in json.dumps(result)

@pytest.mark.parametrize('code,detail',[
 ('print(1/0)','division by zero'),
 ('import os','Only math, statistics and itertools imports available'),
 ('class A: pass','Unsupported Python syntax: ClassDef'),
 ("raise ValueError('a'*500)",'a'*240)])
def test_safe_actionable_errors(code,detail):
    result=calculate(code);assert not result['ok'] and result['detail']==detail,result
    assert set(result)=={'ok','error','detail','stdout'}

def test_budget_guard():
    b=Budget();assert b.remaining==CAP-FRAMING_RESERVE
    n=len(b.tokenizer.encode('{"done":false}',add_special_tokens=False).ids)
    b.generation(3000);b.observation('{"done":false}')
    assert b.used==3000+n+FRAMING_RESERVE
    assert b.remaining==CAP-b.used-FRAMING_RESERVE
    assert b.remaining>2048
    with pytest.raises(ValueError):b.generation(b.remaining+1)
    with pytest.raises(ValueError):b.generation(-1)
    b.generation(b.remaining);assert b.used==CAP and b.remaining==0
    b.observation('terminal');assert b.used>CAP and b.snapshot()['budget_exhausted']

def test_v2_preserved_and_task_sources_unchanged():
    here=Path(__file__).resolve().parent;v2=here.parent/'v2'
    for name,digest in json.loads((here/'v2-preservation.json').read_text()).items():
        assert hashlib.sha256((v2/name).read_bytes()).hexdigest()==digest,name
    for name in ('tasks.py','reference.py','requirements.txt','live_replay.py','test_environment.py'):
        assert (here/name).read_bytes()==(v2/name).read_bytes(),name
    # Reward function is unchanged, while the action description intentionally differs.
    import ast
    def grade_source(path):
        tree=ast.parse(path.read_text());return ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='grade'))
    assert grade_source(here/'server.py')==grade_source(v2/'server.py')
