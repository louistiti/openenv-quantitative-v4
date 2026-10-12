"""Offline corrections of recorded code, not new model attempts or gate changes."""
import ast
import hashlib
import json
import math
from pathlib import Path
from reference import solve
from server import calculate
from tasks import make_task

def main():
    rows=json.loads(Path('model-smoke.json').read_text())['episodes']
    checks=[]
    for ident,seed in [('constrained-schedule',794101),('selected-testing',794102)]:
        row=next(r for r in rows if (r['task_id'],r['seed'])==(ident,seed))
        assert row['outcome']=='wrong_answer'
        code=[t['action']['code'] for t in row['transcript'] if 'action' in t and t['action']['operation']=='python'][-1]
        if ident=='constrained-schedule':
            old='''        if prev is not None:
            t+=setup[jobs[prev]["family"]][jobs[j]["family"]]
        if t<jobs[j]["release"]:
            t=jobs[j]["release"]'''
            new='''        if t<jobs[j]["release"]:
            t=jobs[j]["release"]
        if prev is not None:
            t+=setup[jobs[prev]["family"]][jobs[j]["family"]]'''
            assert code.count(old)==1
            corrected=code.replace(old,new)
            oldprint='print(best[0],best[1])';assert corrected.count(oldprint)==1
            corrected=corrected.replace(oldprint,"print(dict([('weighted_tardiness',best[0][0]),('makespan',best[0][1])]+[('job_at_'+str(i),j) for i,j in enumerate(best[1])]))")
            mechanism='Release time must be reached before setup, not merely before processing.'
        else:
            old='''            if d==1:
                post+=joint
            pp=pattern_prob(d,z)'''
            new='''            pp=pattern_prob(d,z)
            if d==1:
                post+=joint*pp'''
            assert code.count(old)==1 and code.count('posterior=post/sel')==1
            corrected=code.replace(old,new).replace('posterior=post/sel','posterior=post/num')
            mechanism='Disease posterior must condition on selection AND observed test pattern, not selection alone.'
        result=calculate(corrected);assert result['ok'],result
        answer=ast.literal_eval(result['stdout'].strip());reference=solve(make_task(ident,seed))
        assert set(answer)==set(reference)
        assert all(math.isclose(answer[k],v,rel_tol=1e-5,abs_tol=1e-4) for k,v in reference.items()),(answer,reference)
        checks.append(dict(task_id=ident,seed=seed,mechanism=mechanism,all_required_values_match_independent_reference=True,original_code_sha256=hashlib.sha256(code.encode()).hexdigest(),corrected_code_sha256=hashlib.sha256(corrected.encode()).hexdigest(),correction_by_model=False))
    out=Path('failure-mechanisms.json');assert not out.exists()
    out.write_text(json.dumps(dict(offline_only=True,model_attempts_added=0,original_results_unchanged=True,checks=checks),indent=2)+'\n')
    print(json.dumps({'verified_offline_mechanisms':len(checks),'new_model_attempts':0}))

if __name__=='__main__':main()
