"""The handoff carries the full FR6 package without leaking answers or ACL-excluded records."""
import copy
import hashlib
import json

import pytest
from agent_customer_team.cli import main
from agent_customer_team.workflow import run_case
from case_helpers import CTX, D, P, doc

OLD_KEYS = {"status", "ownership", "proposed_owner", "reason", "summary", "next_action"}
NEW_KEYS = {"case_id", "topic", "intent", "message", "attempted_steps", "evidence"}
SC1 = "\u0085\u009b​‍‮⁦  ﻿\x7f"


def run(context=CTX, payload=P, docs=(D,)):
    return run_case(context, payload, {"documents": list(docs)})


def digest(answer):
    return hashlib.sha256(answer.encode("utf-8")).hexdigest()


CASES = [
    ("paused_ownership", dict(CTX, ownership="paused"), P, (D,)),
    ("risk_requires_human", CTX, dict(P, intent="risk"), (D,)),
    ("unknown_intent", CTX, dict(P, intent="unknown"), (D,)),
    ("no_eligible_knowledge", CTX, P, ()),
    ("conflicting_knowledge", CTX, P, (D, doc(id="b", answer="Khác", locator="guide-2"))),
    ("invalid_scoped_knowledge", CTX, P, (doc(answer=None),)),
]


@pytest.mark.parametrize("reason,context,payload,docs", CASES)
def test_handoff_has_full_package(reason, context, payload, docs):
    payload = dict(payload, message="Xin chào", attempted_steps=["a", "b"])
    handoff = run(context, payload, docs)["handoff"]
    assert set(handoff) == OLD_KEYS | NEW_KEYS
    assert handoff["reason"] == reason
    assert handoff["case_id"] == payload["case_id"] and handoff["topic"] == payload["topic"]
    assert handoff["intent"] == payload["intent"] and handoff["message"] == "Xin chào"
    assert handoff["attempted_steps"] == ["a", "b"]
    assert handoff["status"] == "pending" and handoff["ownership"] == "paused"
    assert handoff["summary"] == "case:" + payload["case_id"]


def test_attempted_steps_is_a_copy():
    payload = dict(P, attempted_steps=["a"])
    handoff = run(payload=payload, docs=())["handoff"]
    handoff["attempted_steps"].append("z")
    assert payload["attempted_steps"] == ["a"]


@pytest.mark.parametrize("reason,context,payload,docs", [c for c in CASES if c[0] != "conflicting_knowledge"])
def test_evidence_empty_unless_conflict(reason, context, payload, docs):
    assert run(context, payload, docs)["handoff"]["evidence"] == []


def test_conflict_evidence_lists_eligible_sorted_without_answer():
    second = doc(id="b", answer="Khác", locator="guide-2")
    handoff = run(docs=(second, D))["handoff"]
    assert handoff["evidence"] == [
        {"id": "a", "product_version": "v1", "locator": "guide-1", "sha256": digest(D["answer"])},
        {"id": "b", "product_version": "v1", "locator": "guide-2", "sha256": digest("Khác")},
    ]
    assert "answer" not in json.dumps(handoff["evidence"])


def test_acl_excluded_conflicting_document_is_absent():
    hidden = doc(id="secret", answer="Bí mật", acl=["other"], locator="hidden-1")
    other_tenant = doc(id="t2", answer="Khác", tenant_id="t2")
    handoff = run(docs=(D, hidden, other_tenant, doc(id="b", answer="Khác")))["handoff"]
    assert handoff["reason"] == "conflicting_knowledge"
    assert [e["id"] for e in handoff["evidence"]] == ["a", "b"]
    assert "Bí mật" not in json.dumps(handoff) and "hidden-1" not in json.dumps(handoff)


def test_draft_shape_is_unchanged():
    result = run()
    assert result["handoff"] is None and result["status"] == "draft"
    assert set(result["evidence"][0]) == {"id", "product_version", "locator", "sha256"}


def test_human_owned_shape_is_unchanged():
    result = run(dict(CTX, ownership="human"))
    assert result["status"] == "human_owned" and result["handoff"] is None and result["evidence"] == []


def test_inputs_are_not_mutated():
    docs = (D, doc(id="b", answer="Khác"))
    before = copy.deepcopy(docs)
    run(docs=docs)
    assert docs == before


def test_cli_stdout_has_no_raw_unsafe_bytes_in_handoff(tmp_path, capsysbinary):
    locator = "g‍1"  # Cf is allowed by the document contract, Cc is not
    payload = dict(P, message="m" + SC1, attempted_steps=["s" + SC1, "t"])
    documents = [doc(locator=locator), doc(id="b", answer="Khác", locator="guide-2")]
    paths = []
    for name, value in (("context", CTX), ("payload", payload), ("knowledge", {"documents": documents})):
        path = tmp_path / (name + ".json")
        path.write_text(json.dumps(value), encoding="utf-8")
        paths.append(str(path))
    code = main(["--context", paths[0], "--payload", paths[1], "--knowledge", paths[2]])
    out = capsysbinary.readouterr().out
    assert code == 0
    for ch in SC1 + locator:
        if ch.isascii() and ch.isprintable():
            continue
        assert ch.encode("utf-8") not in out
    handoff = json.loads(out)["handoff"]
    assert handoff["message"] == payload["message"] and handoff["attempted_steps"] == payload["attempted_steps"]
    assert handoff["evidence"][0]["locator"] == locator
