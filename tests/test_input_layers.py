"""Negative tests for each input-validation layer; each has a valid control case."""
import pytest
from agent_customer_team.contracts import parse_inputs
from agent_customer_team.knowledge import retrieve
from agent_customer_team.workflow import run_case
from case_helpers import C, CTX, D, P, doc

CORPUS = {"documents": [D]}


def parse(context=CTX, payload=P, corpus=CORPUS):
    return parse_inputs(context, payload, corpus)


@pytest.mark.parametrize("value", ["bot", "human", "paused"])
def test_ownership_valid_values_accepted(value):
    assert parse(context=dict(CTX, ownership=value))[0]["ownership"] == value


@pytest.mark.parametrize("value", ["Human", "BOT", "admin", "", None, 1, ["human"]])
def test_ownership_unknown_or_wrong_case_rejected(value):
    with pytest.raises(ValueError):
        parse(context=dict(CTX, ownership=value))


@pytest.mark.parametrize("value", ["Human", "admin"])
def test_ownership_bad_value_never_reaches_a_draft(value):
    with pytest.raises(ValueError):
        run_case(dict(CTX, ownership=value), P, CORPUS)


@pytest.mark.parametrize("value", ["support", "risk", "unknown"])
def test_intent_valid_values_accepted(value):
    assert parse(payload=dict(P, intent=value))[1]["intent"] == value


@pytest.mark.parametrize("value", ["Support", "refund", "", None, 3])
def test_intent_unknown_rejected(value):
    with pytest.raises(ValueError):
        parse(payload=dict(P, intent=value))


@pytest.mark.parametrize("field", ["tenant_id", "product", "product_version", "principal", "proposed_owner"])
def test_context_identifier_valid_accepted(field):
    assert parse(context=dict(CTX, **{field: "ok-1.x_y"}))[0][field] == "ok-1.x_y"


@pytest.mark.parametrize("field", ["tenant_id", "product", "product_version", "principal", "proposed_owner"])
@pytest.mark.parametrize("value", ["", "bad id", "bad\n", "../x", "-lead", "x" * 129, "té", 7, None, ["t1"]])
def test_context_identifier_bad_grammar_or_type_rejected(field, value):
    with pytest.raises(ValueError):
        parse(context=dict(CTX, **{field: value}))


def test_attempted_steps_at_limit_accepted():
    steps = ["step"] * 10
    assert parse(payload=dict(P, attempted_steps=steps))[1]["attempted_steps"] == steps


def test_attempted_steps_over_limit_rejected():
    with pytest.raises(ValueError):
        parse(payload=dict(P, attempted_steps=["step"] * 11))


@pytest.mark.parametrize("steps", ["step", None, {"a": 1}, [""], ["   "], [1], ["ok", None], ["x" * 1025], ["\ud800"]])
def test_attempted_steps_wrong_shape_or_item_rejected(steps):
    with pytest.raises(ValueError):
        parse(payload=dict(P, attempted_steps=steps))


def test_corpus_exact_key_accepted():
    assert parse(corpus={"documents": []})[2] == {"documents": []}


@pytest.mark.parametrize("corpus", [{"documents": [], "extra": 1}, {}, {"docs": []}, [], None])
def test_corpus_wrong_keys_or_type_rejected(corpus):
    with pytest.raises(ValueError):
        parse(corpus=corpus)


def test_corpus_at_100_documents_accepted():
    assert len(parse(corpus={"documents": [{}] * 100})[2]["documents"]) == 100


def test_corpus_over_100_documents_rejected():
    with pytest.raises(ValueError):
        parse(corpus={"documents": [{}] * 101})


def test_eligible_document_exact_fields_accepted():
    assert retrieve(C, "reset", {"documents": [D]})[1] == "eligible"


@pytest.mark.parametrize("extra", [{"note": "x"}, {"owner": "x"}, {"answer_html": "<b>"}])
def test_eligible_document_with_extra_field_is_invalid(extra):
    assert retrieve(C, "reset", {"documents": [doc(**extra)]}) == (None, "invalid_scoped_knowledge", [])


def test_eligible_document_missing_field_is_invalid():
    item = dict(D)
    del item["locator"]
    assert retrieve(C, "reset", {"documents": [item]}) == (None, "invalid_scoped_knowledge", [])
