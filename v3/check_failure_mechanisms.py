"""Offline counterfactual code checks. NOT model successes, retries, or training data."""
import ast
import json
import math
from pathlib import Path
from server import calculate
from tasks import make_task
from reference import solve

def main():
    data=json.loads(Path('model-smoke.json').read_text());out=[]
    for ident in ('leveraged-cashflows','selected-testing','piecewise-reactor'):
        row=next(r for r in data['episodes'] if r['task_id']==ident)
        assert row['outcome']=='wrong_answer'
        code=[t['action']['code'] for t in row['transcript'] if 'action' in t and t['action']['operation']=='python'][-1]
        def replace(old,new,count=1):
            nonlocal code
            assert code.count(old)==count,(ident,old,code.count(old))
            code=code.replace(old,new)
        if ident=='leveraged-cashflows':
            replace('cash=0.0','cash=reserve')
            replace('taxable=op-carry','if i==n-1: op+=salvage\n    taxable=op-carry')
            replace('carry+= -taxable','carry= -taxable')
            replace('        sal_tax=tax*salvage\n        total_tax+=sal_tax\n        cash-=sal_tax\n','')
            mechanisms=['Initial funded reserve was omitted from cash ledger','Negative taxable balance double-counted existing loss carry','Terminal salvage was taxed separately without applying loss carry']
            result=calculate(code);assert result['ok'],result
            actual=ast.literal_eval(result['stdout'].strip())
        elif ident=='selected-testing':
            old="pz = g['z_if_disease'] if d==1 else g['z_if_healthy']"
            replace(old,"pz = (g['z_if_disease'] if d==1 else g['z_if_healthy']) if z==1 else (1-(g['z_if_disease'] if d==1 else g['z_if_healthy']))",4)
            mechanisms=['Used P(Z=1) for both Z=0 and Z=1 instead of complementing the Bernoulli mass']
            result=calculate(code);assert result['ok'],result
            actual={line.split(':')[0]:float(line.split(':')[1]) for line in result['stdout'].splitlines()}
        else:
            replace('return (fin-fout, fin*fa - fout*A/V - k*A, fout*B/V)','return (fin-fout, fin*fa - fout*A/V - k*A, k*A-fout*B/V)')
            replace('        V=V+dt/6*','        Bdis += dt*fout/6*(B/V+2*B2/V2+2*B3/V3+B4/V4)\n        V=V+dt/6*')
            replace('V=V*(1-rf); A=A*(1-rf); B=B*(1-rf)','A=A*(1-rf); B=B*(1-rf)')
            replace('print(V,A,B,Bdis)',"print({'final_volume_L':V,'final_A_mol':A,'final_B_mol':B,'total_B_discharged_mol':Bdis})")
            mechanisms=['B equation omitted reaction production and used wrong outflow sign','Continuous B discharge was omitted','Replacement drained volume without restoring equal refill volume']
            result=calculate(code);assert result['ok'],result
            actual=ast.literal_eval(result['stdout'].strip())
        reference=solve(make_task(ident,row['seed']))
        assert set(actual)==set(reference),(ident,actual,reference)
        for k,v in reference.items():assert math.isclose(actual[k],v,rel_tol=1e-5,abs_tol=1e-4),(ident,k,actual[k],v)
        out.append(dict(task_id=ident,seed=row['seed'],mechanisms=mechanisms,all_keys_match_after_offline_corrections=True))
    print(json.dumps(dict(model_reruns=0,model_successes_added=0,rows=out),indent=2))

if __name__=='__main__':main()
