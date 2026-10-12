"""Read-only model evidence audit; independent oracle stays out of model prompts."""
import hashlib
import json
import math
from pathlib import Path
from budget import Budget,CAP,FRAMING_RESERVE
from reference import solve
from server import grade
from tasks import make_task

def main(path=Path('model-smoke.json')):
    raw=Path(path).read_bytes();data=json.loads(raw)
    rows=[]
    for row in data['episodes']:
        b=Budget();steps=[];last_answer=None
        for item in row['transcript']:
            if 'assistant' in item:
                assert item['predict_allowance']==b.remaining
                b.generation(item['eval_count'])
            else:
                from server import QuantObservation
                b.observation(QuantObservation(**item['observation']).model_dump_json())
                assert b.snapshot()==item['budget']
                if item['action']['operation']=='submit':last_answer=item['action'].get('answer','')
        for k,v in b.snapshot().items():assert row[k]==v,(row['task_id'],k,row[k],v)
        p=make_task(row['task_id'],row['seed']);reference=solve(p)
        assert all(math.isclose(reference[k],v,rel_tol=1e-9,abs_tol=1e-7) for k,v in p.targets.items())
        disagreements=[]
        if last_answer:
            actual=json.loads(last_answer)
            expected_reward=grade(p,last_answer)
            if row['outcome'] not in ('completion_budget',):assert row['reward']==expected_reward
            for key,value in reference.items():
                got=actual.get(key)
                if not isinstance(got,(int,float)) or isinstance(got,bool) or not math.isfinite(got) or not math.isclose(got,value,rel_tol=1e-5,abs_tol=1e-4):
                    disagreements.append(dict(key=key,actual=got,reference=value))
        summary={k:v for k,v in row.items() if k!='transcript'}
        summary['independent_answer_disagreements']=disagreements;rows.append(summary)
    out=dict(result_sha256=hashlib.sha256(raw).hexdigest(),attempted=len(rows),unattempted=data['unattempted'],outcomes={o:sum(r['outcome']==o for r in rows) for o in sorted(set(r['outcome'] for r in rows))},training_solved=sum(r['reward']==1 for r in rows if not r['heldout']),heldout_solved=sum(r['reward']==1 for r in rows if r['heldout']),rows=rows,learning_evidence=False)
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    import sys
    main(sys.argv[1] if len(sys.argv)>1 else Path('model-smoke.json'))
