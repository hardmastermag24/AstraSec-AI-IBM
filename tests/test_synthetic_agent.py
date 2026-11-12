import json
import pytest
from app.core.synthetic_agent import validate_analysis, synthetic_messages
from app.core.agent import OrchestrateProvider


def valid():
    return {'hechos':[{'texto':'Dos fallos registrados.', 'fuentes':['S1']}], 'hipotesis':[], 'recomendaciones':[], 'limitaciones':[{'texto':'Datos sintéticos.', 'fuentes':['S1','S2']}]}


def test_validation_accepts_referenced_sections():
    assert validate_analysis(json.dumps(valid())) == valid()

@pytest.mark.parametrize('change', ['invalid_json','unknown_source','missing_source','missing_section','wrong_list'])
def test_invalid_response_is_rejected(change):
    data=valid()
    if change=='invalid_json': text='not json'
    else:
        if change=='unknown_source': data['hechos'][0]['fuentes']=['SECRET']
        if change=='missing_source': data['hechos'][0]['fuentes']=[]
        if change=='missing_section': del data['limitaciones']
        if change=='wrong_list': data['hechos']='text'
        text=json.dumps(data)
    with pytest.raises(ValueError): validate_analysis(text)


def test_fixture_does_not_include_user_context():
    messages=synthetic_messages()
    assert len(messages)==2
    assert '192.0.2.10' in messages[1]['content']
    assert '198.51.100.10' not in str(messages)
    assert 'S1' in messages[1]['content'] and 'S2' in messages[1]['content']


def test_synthetic_request_uses_dedicated_agent(monkeypatch):
    monkeypatch.setenv('ORCHESTRATE_API_KEY','test')
    monkeypatch.setenv('ORCHESTRATE_URL','https://api.jp-tok.watson-orchestrate.cloud.ibm.com/instances/00000000-0000-4000-8000-000000000005')
    monkeypatch.setenv('ORCHESTRATE_AGENT_ID','00000000-0000-4000-8000-000000000006')
    calls=[]
    def post(self,url,payload,token=None):
        calls.append((url,payload))
        return {'access_token':'token'} if token is None else {'choices':[{'message':{'content':json.dumps(valid())}}]}
    monkeypatch.setattr(OrchestrateProvider,'_post',post)
    provider=OrchestrateProvider()
    assert provider.analyze_synthetic()==valid()
    assert '/00000000-0000-4000-8000-000000000002/' in calls[1][0]
    assert '198.51.100.10' not in json.dumps(calls)
    assert provider._agent_id=='00000000-0000-4000-8000-000000000006'
