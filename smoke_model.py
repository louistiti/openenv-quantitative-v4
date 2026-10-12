"""Predeclared capped JSON-action generalization smoke test, no tuning/retries."""
import json
from pathlib import Path
import time
import urllib.request
from server import QuantEnvironment,QuantAction
from tasks import TASK_IDS,HELDOUT_IDS

MODEL='qwen3.8:27b'
TOTAL_SECONDS=1200
EPISODE_SECONDS=120
WORKLIST=[(ident,86713+i) for i,ident in enumerate(TASK_IDS+HELDOUT_IDS)]
OUT=Path('model-smoke.json')

def main():
    if OUT.exists(): raise RuntimeError('Smoke output exists: do not silently rerun the capped experiment')
    started=time.monotonic();rows=[]
    schema=QuantAction.model_json_schema()
    system='Solve the quantitative task with the provided calculation workbench. Each reply MUST be exactly one JSON object matching this action schema, no markdown or commentary. You can use python calculations then submit numeric answer JSON text. You may also reply {"finish":true} to end without a new answer. Schema: '+json.dumps(schema)
    for ident,seed in WORKLIST:
        if time.monotonic()-started>=TOTAL_SECONDS: break
        env=QuantEnvironment();initial=env.reset(task_id=ident,seed=seed)
        messages=[dict(role='system',content=system),dict(role='user',content=initial.model_dump_json())]
        transcript=[];episode_start=time.monotonic();row=dict(task_id=ident,seed=seed,heldout=ident in HELDOUT_IDS,reward=None,actions=0,tokens=0,completed=False,error=None)
        try:
            while not env.ended:
                remaining=min(EPISODE_SECONDS-(time.monotonic()-episode_start),TOTAL_SECONDS-(time.monotonic()-started))
                if remaining<=0: raise TimeoutError('Predeclared wall-time cap')
                payload=dict(model=MODEL,messages=messages,stream=False,think=False,
                             options=dict(num_ctx=24576,num_predict=2048,temperature=.7,seed=9001+seed+env.state.step_count),keep_alive='5m')
                request=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(request,timeout=min(remaining,80)) as r: reply=json.load(r)
                row['tokens']+=reply.get('eval_count',0);text=reply['message']['content']
                messages.append(dict(role='assistant',content=text));transcript.append(dict(assistant=text,done_reason=reply.get('done_reason')))
                args=json.loads(text)
                if not isinstance(args,dict): raise ValueError('Reply not an action object')
                if args=={'finish':True}: args=dict(operation='submit')
                if set(args)=={'action'} and isinstance(args['action'],dict): args=args['action']
                observation=env.step(QuantAction(**args));row['actions']=env.state.step_count
                messages.append(dict(role='user',content=observation.model_dump_json()))
                transcript.append(dict(action=args,observation=observation.model_dump()))
                print(json.dumps(dict(task=ident,step=env.state.step_count,operation=args['operation'],done=observation.done,reward=observation.reward)),flush=True)
                if row['tokens']>8192: raise TimeoutError('Predeclared generated-token cap')
            row.update(reward=env.last_reward,completed=True)
        except Exception as e:
            row['error']=type(e).__name__+': '+str(e)[:160]
            # Match Arena finish_action after a failed/truncated reply; no answer is stored between steps.
            if not env.ended: env.step(QuantAction(operation='submit'))
            row.update(reward=env.last_reward,completed=env.ended,actions=env.state.step_count)
        finally:
            row['seconds']=round(time.monotonic()-episode_start,2);row['transcript']=transcript;env.close()
        rows.append(row)
        OUT.write_text(json.dumps(dict(model=MODEL,quantization='nvfp4 MLX local proxy, not Arena weights/runner',interface='system action schema + JSON user observations, no native tool parser/grammar constraint',cap_episodes=20,cap_seconds=TOTAL_SECONDS,episode_cap_seconds=EPISODE_SECONDS,worklist=WORKLIST,episodes=rows,learning_evidence=False),indent=2)+'\n')
        print(json.dumps({k:v for k,v in row.items() if k!='transcript'}),flush=True)
    solved=sum(r['reward']==1 for r in rows)
    print(json.dumps(dict(episodes=len(rows),solved=solved,mixed_outcomes=0<solved<len(rows),heldout_solved=sum(r['heldout'] and r['reward']==1 for r in rows))),flush=True)

if __name__=='__main__': main()
