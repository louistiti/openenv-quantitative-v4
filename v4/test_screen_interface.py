"""Offline synthetic replies only; these are not model episodes or learning evidence."""
import io
import json
import pytest
import smoke_model as screen
from tasks import make_task

@pytest.mark.parametrize('kind,expected',[
 ('correct','success'),('wrong','wrong_answer'),('invalid','invalid_json'),
 ('truncated','truncated_reply'),('timeout','wall_time'),('missing_count','accounting_error')])
def test_single_attempt_and_classification(monkeypatch,tmp_path,kind,expected):
    ident,seed='selected-testing',777777
    monkeypatch.setattr(screen,'WORKLIST',[(ident,seed)])
    monkeypatch.setattr(screen,'OUT',tmp_path/'offline.json')
    calls=[]
    def fake(request,timeout):
        payload=json.loads(request.data);calls.append(payload)
        assert payload['options']['num_predict']==8152
        assert timeout>80 # No obsolete eighty-second request limit.
        assert payload['think'] is False
        if kind=='timeout':raise TimeoutError('synthetic timeout')
        truth=make_task(ident,seed).targets
        answer=json.dumps(truth if kind=='correct' else {k:-1 for k in truth})
        content=json.dumps(dict(operation='submit',answer=answer))
        if kind in ('invalid','truncated'):content='{"operation":'
        reply=dict(message=dict(content=content),done_reason='length' if kind=='truncated' else 'stop',eval_count=100)
        if kind=='missing_count':del reply['eval_count']
        return io.BytesIO(json.dumps(reply).encode())
    monkeypatch.setattr(screen.urllib.request,'urlopen',fake)
    screen.main()
    data=json.loads(screen.OUT.read_text());row=data['episodes'][0]
    assert row['outcome']==expected,row
    assert len(calls)==1 and not data['unattempted']
    assert row['answer_delivered']==(kind in ('correct','wrong'))
    if kind=='correct':assert row['reward']==1 and row['observation_tokens']>0
    with pytest.raises(RuntimeError,match='Frozen output'):screen.main()
    assert len(calls)==1
