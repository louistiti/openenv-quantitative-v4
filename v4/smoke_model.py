"""One-shot repair diagnostic. Protocol frozen before model calls."""
import hashlib
import json
from pathlib import Path
import time
import urllib.request
from budget import Budget,CAP
from server import QuantEnvironment,QuantAction
from tasks import HELDOUT_IDS
MODEL='qwen3.8:27b'
TOTAL_SECONDS=900
EPISODE_SECONDS=300
WORKLIST=[]
for round_index in range(4):
    WORKLIST.extend((ident,794101+10*round_index+i) for i,ident in enumerate(('constrained-schedule','selected-testing')))
    if round_index<2:WORKLIST.extend((ident,894101+10*round_index+i) for i,ident in enumerate(('parallel-schedule','american-option')))
OUT=Path('model-smoke.json')

def main():
    if OUT.exists(): raise RuntimeError('Frozen output exists; no reruns')
    freeze=json.loads(Path('candidate-freeze.json').read_text())
    for name,digest in freeze['source_hashes'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest: raise RuntimeError('Frozen source changed: '+name)
    started=time.monotonic();rows=[]
    system='Solve the quantitative task with the calculation workbench. Reply exactly one JSON object matching this action schema, no markdown or commentary. Use concise code and print only required results, not large traces. Submit numeric answer JSON text once ready. You may reply {"finish":true} to end without a new answer. Schema: '+json.dumps(QuantAction.model_json_schema())
    for ident,seed in WORKLIST:
        if time.monotonic()-started>=TOTAL_SECONDS: break
        env=QuantEnvironment();initial=env.reset(task_id=ident,seed=seed);b=Budget()
        messages=[dict(role='system',content=system),dict(role='user',content=initial.model_dump_json())]
        transcript=[];episode_start=time.monotonic()
        row=dict(task_id=ident,seed=seed,heldout=ident in HELDOUT_IDS,reward=None,actions=0,worker_errors=0,answer_delivered=False,outcome=None,error=None)
        try:
            while not env.ended:
                remaining=min(EPISODE_SECONDS-time.monotonic()+episode_start,TOTAL_SECONDS-time.monotonic()+started)
                if remaining<=0: row['outcome']='wall_time';raise TimeoutError('Predeclared wall-time cap')
                if b.remaining<=0: row['outcome']='completion_budget';raise ValueError('No remaining completion allowance')
                allowance=b.remaining
                payload=dict(model=MODEL,messages=messages,stream=False,think=False,options=dict(num_ctx=24576,num_predict=allowance,temperature=.7,seed=9001+seed+env.state.step_count),keep_alive='5m')
                request=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(request,timeout=remaining) as r: reply=json.load(r)
                if 'eval_count' not in reply: row['outcome']='accounting_error';raise ValueError('Missing generated token count')
                b.generation(reply['eval_count']);text=reply['message']['content']
                messages.append(dict(role='assistant',content=text))
                transcript.append(dict(assistant=text,done_reason=reply.get('done_reason'),predict_allowance=allowance,eval_count=reply['eval_count']))
                try: args=json.loads(text)
                except json.JSONDecodeError:
                    row['outcome']='truncated_reply' if reply.get('done_reason')=='length' else 'invalid_json';raise
                if not isinstance(args,dict): row['outcome']='invalid_action';raise ValueError('Reply not an action object')
                if args=={'finish':True}: args=dict(operation='submit')
                if set(args)=={'action'} and isinstance(args['action'],dict): args=args['action']
                action=QuantAction(**args)
                obs=env.step(action);row['actions']=env.state.step_count
                if action.operation=='submit':row['answer_delivered']=bool(action.answer.strip())
                if action.operation=='python' and not obs.done:row['worker_errors']+=not json.loads(obs.message).get('ok',False)
                content=obs.model_dump_json();b.observation(content)
                messages.append(dict(role='user',content=content));transcript.append(dict(action=args,observation=obs.model_dump(),budget=b.snapshot()))
                print(json.dumps(dict(task=ident,seed=seed,step=env.state.step_count,operation=action.operation,done=obs.done,reward=obs.reward,completion_accounted=b.used)),flush=True)
                if b.used>CAP:row['outcome']='completion_budget';raise ValueError('Observation exceeded completion allowance')
            row['outcome']='success' if env.last_reward==1 else ('wrong_answer' if row['answer_delivered'] else 'ended_without_answer')
            row['reward']=env.last_reward
        except Exception as e:
            if row['outcome'] is None:row['outcome']='wall_time' if isinstance(e,(TimeoutError,)) else 'interface_error'
            row['error']=type(e).__name__+': '+str(e)[:160]
            row['reward']=env.last_reward if env.ended else 0
        finally:
            row.update(b.snapshot());row['seconds']=round(time.monotonic()-episode_start,2)
            row['transcript']=transcript;env.close()
        rows.append(row)
        output=dict(model=MODEL,quantization='nvfp4 MLX local proxy, not Arena weights/runner',interface='schema prompt and JSON observations, no native grammar',diagnostic_only=True,learning_evidence=False,freeze=freeze,cap_seconds=TOTAL_SECONDS,episode_cap_seconds=EPISODE_SECONDS,worklist=WORKLIST,unattempted=[dict(task_id=t,seed=s) for t,s in WORKLIST[len(rows):]],episodes=rows)
        OUT.write_text(json.dumps(output,indent=2)+'\n')
        print(json.dumps({k:v for k,v in row.items() if k!='transcript'}),flush=True)
    print(json.dumps(dict(attempted=len(rows),unattempted=len(WORKLIST)-len(rows),outcomes={o:sum(r['outcome']==o for r in rows) for o in set(r['outcome'] for r in rows)})),flush=True)

if __name__=='__main__':main()
