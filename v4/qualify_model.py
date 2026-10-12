"""Qualification wrapper, not a trainer or submitter."""
import json
import hashlib
from pathlib import Path
import smoke_model
from tasks import TASK_IDS

def gate(rows):
    train=[r for r in rows if not r['heldout']];hold=[r for r in rows if r['heldout']]
    solved=sum(r['outcome']=='success' for r in train)
    mixed=sum(0<sum(r['outcome']=='success' for r in train if r['task_id']==t)<4 for t in TASK_IDS)
    usable=sum(r['answer_delivered'] and r['outcome'] in ('success','wrong_answer') and r['completion_accounted']<=8192 for r in rows)
    return dict(attempted=len(rows),training_solved=solved,heldout_solved=sum(r['outcome']=='success' for r in hold),mixed_training_families=mixed,usable_numeric_answers=usable,gate_passed=len(rows)==12 and 2<=solved<=6 and mixed==2 and any(r['outcome']=='success' for r in hold) and usable>=11)

def main():
    smoke_model.main()
    data=json.loads(smoke_model.OUT.read_text());result=gate(data['episodes'])
    result['result_sha256']=hashlib.sha256(smoke_model.OUT.read_bytes()).hexdigest()
    path=Path('candidate-gate.json');assert not path.exists()
    path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
