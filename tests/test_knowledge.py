import copy
import pytest
from agent_customer_team.knowledge import retrieve
from case_helpers import C, D, doc

def find(*docs):
    return retrieve(C, 'reset', {'documents': list(docs)})

@pytest.mark.parametrize('change', [{'tenant_id': 'other'}, {'product': 'other'}, {'product_version': 'v2'}, {'topic': 'other'}, {'acl': ['u2']}, {'acl': 'u10'}, {'status': 'draft'}, {'effective_from': '2026-01-02'}, {'effective_from': '2025-01-01', 'expires_at': '2025-12-31'}])
def test_scope_and_dates(change):
    assert find(doc(**change)) == (None, 'no_eligible_knowledge')

def test_inclusive_dates():
    assert find(doc(expires_at='2026-01-01'))[1] == 'eligible'
    assert find(doc(effective_from='2026-01-01'))[1] == 'eligible'

def test_conflict():
    assert find(D, doc(id='b', answer='Different')) == (None, 'conflicting_knowledge')

def test_identical_tiebreak():
    assert find(doc(id='z'), D)[0]['id'] == 'a'

def test_unrelated_topic_and_expired_are_invariant():
    assert find(D) == find(D, doc(topic='other'), doc(effective_from='2024-01-01', expires_at='2025-01-01'))

@pytest.mark.parametrize('extra', [doc(acl=['u2'], answer=None, id=None), doc(status='draft', answer=None, id=None), doc(effective_from='2024-01-01', expires_at='2025-01-01', answer=None, id=None), doc(acl='u10', answer=None, id=None), {'answer': 'private'}])
def test_selector_precedence(extra):
    assert find(D) == find(D, extra)

@pytest.mark.parametrize('change', [{'answer': None}, {'id': None}, {'effective_from': 'bad'}, {'expires_at': '2025-01-01', 'effective_from': '2026-01-01'}, {'answer': '\ud800'}])
def test_granted_malformed_is_pending(change):
    assert find(doc(**change)) == (None, 'invalid_scoped_knowledge')

def test_duplicate_eligible_id():
    assert find(D, copy.deepcopy(D)) == (None, 'invalid_scoped_knowledge')
