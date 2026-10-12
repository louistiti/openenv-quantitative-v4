"""Prepare an exact request, never submit it. Requires verified immutable image."""
import argparse
import json
from pathlib import Path
import re
from tasks import TASK_IDS
p=argparse.ArgumentParser()
p.add_argument('--image',required=True)
p.add_argument('--schema',default='schema-container.json')
p.add_argument('--output',default='submission-quantitative-v4.json')
a=p.parse_args()
image=a.image.strip()
if not re.fullmatch(r'ghcr\.io/louistiti/openenv-quantitative-v4@sha256:[0-9a-f]{64}',image):
    raise ValueError('Verified immutable v4 image required')
out=Path(a.output)
assert not out.exists(), 'Never overwrite an existing submission request'
schema=json.loads(Path(a.schema).read_text())
from server import QuantAction,QuantObservation
assert schema['action']==QuantAction.model_json_schema()
assert schema['observation']==QuantObservation.model_json_schema()
assert TASK_IDS==('constrained-schedule','selected-testing')
request=dict(submission_id='quantitative-reasoning-lab-v4',name='Quantitative Reasoning Lab v4',image=image,server_port=8000,
 schema=schema,tasks=[dict(task_id=x,split='train',reset_wall_s=120,rollout_wall_s=600,verifier_wall_s=120,tool_wall_s=120,tool_calls_total=16,tool_calls_per_minute=60,completion_tokens=8192,context_tokens=24576,memory_gib=2,cpu_floor_vcpus=1,workspace_gib=1) for x in TASK_IDS],
 example_actions=[dict(operation='submit')],finish_action=dict(operation='submit'),source='https://github.com/louistiti/openenv-quantitative-v4/tree/main/v4')
out.write_text(json.dumps(request,indent=2)+'\n')
print(json.dumps(dict(request=str(out),train_tasks=len(TASK_IDS),submitted=False)))
