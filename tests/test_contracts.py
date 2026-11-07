import copy
import pytest
from agent_customer_team.contracts import parse_inputs

@pytest.fixture
def data():
    return ({'tenant_id': 't1', 'product': 'app', 'product_version': 'v1', 'principal': 'u1', 'as_of': '2026-01-01', 'ownership': 'bot', 'proposed_owner': 'agent'}, {'case_id': 'case1', 'message': 'help', 'intent': 'support', 'topic': 'reset', 'attempted_steps': []}, {'documents': []})

def test_valid_no_mutation(data):
    original = copy.deepcopy(data)
    assert parse_inputs(*data) == data
    assert data == original

def test_reject_payload_tenant_override(data):
    data[1]['tenant_id'] = 'other'
    with pytest.raises(ValueError):
        parse_inputs(*data)

@pytest.mark.parametrize('field,value', [('as_of', '2026-02-30'), ('as_of', '２０２６-01-01'), ('unknown', 'x')])
def test_reject_bad_date_and_extra_field(data, field, value):
    data[0][field] = value
    with pytest.raises(ValueError):
        parse_inputs(*data)

def test_corpus_structure_rejected(data):
    data[2]['documents'] = {}
    with pytest.raises(ValueError):
        parse_inputs(*data)

@pytest.mark.parametrize('field,value', [('case_id', 'bad\n'), ('case_id', 'bad id'), ('case_id', 'x' * 129), ('topic', 'a/b'), ('message', '   '), ('message', 'x' * 1025), ('message', '\ud800')])
def test_identifier_and_unicode_bounds(data, field, value):
    data[1][field] = value
    with pytest.raises(ValueError):
        parse_inputs(*data)
