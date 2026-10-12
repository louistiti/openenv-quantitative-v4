"""WebSocket references, never model performance."""
import ast
import asyncio
import json
from pathlib import Path
from websockets.asyncio.client import connect
from tasks import TASK_IDS,HELDOUT_IDS,make_task
from reference import program

async def send(sock,kind,data):
    await sock.send(json.dumps({'type':kind,'data':data}))
    result=json.loads(await asyncio.wait_for(sock.recv(),timeout=30))
    assert result['type']=='observation',result
    return result['data']

async def main():
    out=Path('replay-local.json');assert not out.exists()
    records=[]
    for seed in (713,2718):
        for ident in TASK_IDS+HELDOUT_IDS:
            async with connect('ws://127.0.0.1:8768/ws') as sock:
                p=make_task(ident,seed);initial=await send(sock,'reset',dict(task_id=ident,seed=seed))
                assert initial['observation']['message']==p.instruction
                floor=await send(sock,'step',dict(operation='submit'));assert floor['done'] and floor['reward']==0
                await send(sock,'reset',dict(task_id=ident,seed=seed))
                result=await send(sock,'step',dict(operation='python',code=program(p)))
                tool=json.loads(result['observation']['message']);assert tool['ok'],tool
                assert not result['done'] and result['reward']==0
                final=await send(sock,'step',dict(operation='submit',answer=json.dumps(ast.literal_eval(tool['stdout']))))
                assert final['done'] and final['reward']==1,final
                records.append(dict(task_id=ident,seed=seed,reward=1,steps=2))
    out.write_text(json.dumps(dict(transport='network_websocket',episodes=len(records),all_passed=True,model_rollouts=0,rows=records),indent=2)+'\n')
    print(json.dumps(dict(episodes=len(records),all_passed=True)))

if __name__=='__main__': asyncio.run(main())
