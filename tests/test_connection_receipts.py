import json
from app.core.connection_receipts import connection_results

def test_no_receipt_is_not_live(tmp_path):
    assert connection_results(tmp_path)=={}

def test_receipts_require_success_not_just_configuration(tmp_path):
    data=tmp_path/'data';data.mkdir()
    (data/'cos_live_receipt.json').write_text('{"configured":true,"verified":false}')
    assert 'COS' not in connection_results(tmp_path)
    (data/'cos_live_receipt.json').write_text('{"verified":true}')
    assert 'COS' in connection_results(tmp_path)

def test_bad_receipt_does_not_break_panel(tmp_path):
    data=tmp_path/'data';data.mkdir()
    (data/'cos_live_receipt.json').write_text('invalid json')
    assert connection_results(tmp_path)=={}
