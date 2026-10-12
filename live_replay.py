"""Real WebSocket reference episodes; not model performance."""
import argparse
import ast
import asyncio
import json
from pathlib import Path
from websockets.asyncio.client import connect
from tasks import TASK_IDS,make_task
from oracle import program

async def send(sock,kind,data):
    await sock.send(json.dumps({'type':kind,'data':data}))
    result=json.loads(await asyncio.wait_for(sock.recv(),timeout=30))
    assert result['type']=='observation',result
    return result['data']

async def main(url,output):
    records=[]
    for seed in [713,2718]:
        for ident in TASK_IDS:
            async with connect(url.replace('http','ws',1)+'/ws') as sock:
                initial=await send(sock,'reset',dict(task_id=ident,seed=seed))
                assert initial['observation']['message']==make_task(ident,seed).instruction
                floor=await send(sock,'step',dict(operation='submit'))
                assert floor['done'] and floor['reward']==0
                await send(sock,'reset',dict(task_id=ident,seed=seed))
                result=await send(sock,'step',dict(operation='python',code=program(make_task(ident,seed))))
                tool=json.loads(result['observation']['message']);assert tool['ok'],tool
                assert not result['done'] and result['reward']==0
                answer=json.dumps(ast.literal_eval(tool['stdout']))
                terminal=await send(sock,'step',dict(operation='submit',answer=answer))
                assert terminal['done'] and terminal['reward']==1,terminal
                records.append(dict(task_id=ident,seed=seed,reward=1,steps=2))
    Path(output).write_text(json.dumps(dict(transport='network_websocket',episodes=len(records),all_passed=True,model_rollouts=0,rows=records),indent=2)+'\n')
    print(json.dumps(dict(episodes=len(records),all_passed=True)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8768');p.add_argument('--output',default='replay-local.json');a=p.parse_args()
    asyncio.run(main(a.url,a.output))
