"""Exact approved-request draft requires verified immutable image and container schema."""
import argparse
import json
from pathlib import Path
import re
from tasks import TASK_IDS
p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--schema',default='schema-container.json');p.add_argument('--output',default='submission-quantitative-v1.json');a=p.parse_args()
image=a.image.strip()
if not re.fullmatch(r'ghcr\.io/louistiti/openenv-quantitative@sha256:[0-9a-f]{64}',image): raise ValueError('Verified immutable quantitative image required')
request=dict(submission_id='quantitative-reasoning-lab-v1',name='Quantitative Reasoning Lab v1',dataset='Louistiti/openenv-quantitative',image=image,server_port=8000,
 schema=json.loads(Path(a.schema).read_text()),tasks=[dict(task_id=x,split='train',reset_wall_s=120,rollout_wall_s=600,verifier_wall_s=120,tool_wall_s=120,tool_calls_total=16,tool_calls_per_minute=60,completion_tokens=8192,context_tokens=24576,memory_gib=2,cpu_floor_vcpus=1,workspace_gib=1) for x in TASK_IDS],
 example_actions=[dict(operation='submit')],finish_action=dict(operation='submit'),source='https://github.com/louistiti/openenv-quantitative')
Path(a.output).write_text(json.dumps(request,indent=2)+'\n')
print(json.dumps(dict(request=a.output,tasks=len(TASK_IDS),image=image,submitted=False)))
