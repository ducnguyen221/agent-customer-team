import hashlib
import pytest
from agent_customer_team.workflow import run_case, triage
from case_helpers import CTX, D, P, doc

def test_human_precedes_risk():
    assert triage({'ownership': 'human'}, {'intent': 'risk'}) == {'intent': 'risk', 'reason': 'human_ownership'}

def test_bot_support():
    assert triage({'ownership': 'bot'}, {'intent': 'support'})['reason'] == 'support'

def test_unknown_and_paused():
    assert triage({'ownership': 'bot'}, {'intent': 'unknown'})['reason'] == 'unknown_intent'
    assert triage({'ownership': 'paused'}, {'intent': 'risk'})['reason'] == 'paused_ownership'

def run(context=CTX, payload=P, docs=(D,)):
    return run_case(context, payload, {'documents': list(docs)})

def test_draft_is_exact_and_hash_matches():
    result = run()
    assert result['draft'] == 'Khởi động lại ứng dụng.'
    assert result['evidence'][0]['sha256'] == hashlib.sha256(result['draft'].encode('utf-8')).hexdigest()
    assert result['handoff'] is None and result['ownership'] == 'bot'

@pytest.mark.parametrize('owner', ['human', 'paused'])
def test_human_and_paused_never_draft(owner):
    result = run(context=dict(CTX, ownership=owner))
    assert result['draft'] is None and result['evidence'] == []
    if owner == 'human':
        assert result['ownership'] == 'human' and result['handoff'] is None
    else:
        assert result['handoff']['status'] == 'pending' and result['ownership'] == 'paused'

def test_no_knowledge_handoff():
    result = run(docs=())
    assert result['handoff'] == {'status': 'pending', 'ownership': 'paused', 'proposed_owner': 'agent', 'reason': 'no_eligible_knowledge', 'summary': 'case:case1', 'next_action': 'await_human_review', 'case_id': 'case1', 'topic': 'reset', 'intent': 'support', 'message': 'help', 'attempted_steps': [], 'evidence': []}

@pytest.mark.parametrize(
    'owner,intent,docs,triage_reason,handoff_reason',
    [
        ('human', 'risk', (D,), 'human_ownership', None),
        ('paused', 'support', (D,), 'paused_ownership', 'paused_ownership'),
        ('bot', 'risk', (D,), 'risk_requires_human', 'risk_requires_human'),
        ('bot', 'unknown', (D,), 'unknown_intent', 'unknown_intent'),
        ('bot', 'support', (), 'support', 'no_eligible_knowledge'),
        ('bot', 'support', (D, doc(id='b', answer='different')), 'support', 'conflicting_knowledge'),
        ('bot', 'support', (doc(answer=None),), 'support', 'invalid_scoped_knowledge'),
    ],
)
def test_decision_table(owner, intent, docs, triage_reason, handoff_reason):
    context = dict(CTX, ownership=owner)
    payload = dict(P, intent=intent)

    result = run(context, payload, docs)

    assert result['triage']['reason'] == triage_reason
    assert (result['handoff']['reason'] if result['handoff'] else None) == handoff_reason
    assert result['draft'] is None and result['evidence'] == []


def test_triage_support_requires_explicit_bot_and_support():
    assert triage({'ownership': 'bot'}, {'intent': 'support'}) == {'intent': 'support', 'reason': 'support'}


@pytest.mark.parametrize('ownership,intent', [('Human', 'support'), ('admin', 'support'), ('', 'support'), ('bot', 'Support'), ('bot', 'refund'), ('bot', ''), (None, 'support'), ('bot', None)])
def test_triage_unknown_value_never_defaults_to_support(ownership, intent):
    with pytest.raises(ValueError):
        triage({'ownership': ownership}, {'intent': intent})
