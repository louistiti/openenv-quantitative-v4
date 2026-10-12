"""Fresh predeclared screen using the unchanged tested diagnostic harness."""
import hashlib
import json
from pathlib import Path
import smoke_model as screen
from tasks import TASK_IDS,HELDOUT_IDS

WORKLIST=[]
for round_index in range(4):
    WORKLIST.extend((ident,594101+round_index*10+i) for i,ident in enumerate(TASK_IDS))
    if round_index<2:WORKLIST.extend((ident,694101+round_index*10+i) for i,ident in enumerate(HELDOUT_IDS))
OUT=Path('generalization-smoke.json')

def gate(rows):
    training=[r for r in rows if not r['heldout']];heldout=[r for r in rows if r['heldout']]
    solved=sum(r['outcome']=='success' for r in training)
    mixed=sum(0<sum(r['outcome']=='success' for r in training if r['task_id']==ident)<4 for ident in TASK_IDS)
    usable=sum(r['answer_delivered'] and r['outcome'] in ('success','wrong_answer') and r['completion_accounted']<=8192 for r in rows)
    return dict(attempted=len(rows),training_solved=solved,heldout_solved=sum(r['outcome']=='success' for r in heldout),mixed_training_families=mixed,usable_numeric_answers=usable,gate_passed=len(rows)==20 and 4<=solved<=14 and mixed>=2 and any(r['outcome']=='success' for r in heldout) and usable>=18)

def main():
    if OUT.exists():raise RuntimeError('Frozen recurrence screen exists; no reruns')
    freeze=json.loads(Path('generalization-freeze.json').read_text())
    for name,digest in freeze['source_hashes'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Source or preserved diagnostic changed: '+name)
    assert freeze['worklist']==[list(x) for x in WORKLIST]
    screen.WORKLIST=WORKLIST;screen.OUT=OUT
    screen.main()
    data=json.loads(OUT.read_text());summary=gate(data['episodes'])
    summary['result_sha256']=hashlib.sha256(OUT.read_bytes()).hexdigest()
    report=Path('generalization-gate.json');assert not report.exists()
    report.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
