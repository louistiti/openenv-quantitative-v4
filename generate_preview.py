"""Public seeded inspection previews, not training targets or model trajectories."""
import json
from pathlib import Path
from tasks import TASK_IDS,make_task
rows=[]
for ident in TASK_IDS:
    p=make_task(ident,713)
    rows.append(dict(task_id=ident,split='train',preview_seed=713,instruction=p.instruction,inputs=p.inputs,answer_keys=list(p.targets),reward='1 for all-correct numeric outputs; otherwise <=0.15 proportional independently verified subresult credit',fresh_reset=True))
Path('tasks.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
print(json.dumps(dict(rows=len(rows),contains_targets=False)))
