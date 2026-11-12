import pytest
from app.core.real_ibm_advice import payload,validate

def review():
    return {'integrity_verified':True,'external_services_used':False,'observations':[{'source':'openssl_signatures.txt:1','algorithms':['RSA'],'evidence':'PRIVATE LOG ip=192.0.2.10'}],'quality':[{'file':'paquetes_cripto.txt','exit_code':1,'truncated':False,'usable_for_findings':False}]}

def test_payload_minimizes_raw_evidence():
    data=payload(review())
    assert 'PRIVATE LOG' not in str(data) and '192.0.2.10' not in str(data)
    assert data['sources'][0]['source']=='openssl_signatures.txt:1'

@pytest.mark.parametrize('answer',[
 {'actions':[{'action':'run_shell','sources':['E1']}]},
 {'actions':[{'action':'verify_configured_use','sources':['invented']}]},
 {'actions':[{'action':'repeat_failed_collection','sources':['E1']}]},
 {'actions':[{'action':'verify_configured_use','sources':['E2']}]},
 {'actions':[{'action':'verify_configured_use','sources':['E1'],'diagnosis':'secure'}]},
 {'actions':[],'facts':['quantum safe']},
])
def test_rejects_unbounded_or_unsupported_output(answer):
    with pytest.raises(ValueError):validate(answer,payload(review()))

def test_accepts_grounded_actions():
    answer={'actions':[{'action':'verify_configured_use','sources':['E1']},{'action':'repeat_failed_collection','sources':['E2']}]}
    assert validate(answer,payload(review()))==answer
