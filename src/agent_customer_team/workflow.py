"""Deterministic routing for synthetic support cases."""


def triage(context: dict, payload: dict) -> dict:
    """Use explicit ownership and fixture intent; no natural language inference."""
    ownership, intent = context["ownership"], payload["intent"]
    if ownership not in ("bot", "human", "paused") or intent not in ("support", "risk", "unknown"):
        raise ValueError("unknown ownership or intent")
    if ownership == "human":
        reason = "human_ownership"
    elif ownership == "paused":
        reason = "paused_ownership"
    elif intent == "risk":
        reason = "risk_requires_human"
    elif intent == "unknown":
        reason = "unknown_intent"
    elif ownership == "bot" and intent == "support":
        reason = "support"
    else:  # pragma: no cover - unreachable after the allowlist check above
        raise ValueError("unroutable case")
    return {"intent": intent, "reason": reason}


def run_case(context: dict, payload: dict, corpus: dict) -> dict:
    """Produce an internal draft or a pending handoff without side effects."""
    import hashlib
    from .contracts import parse_inputs
    from .knowledge import retrieve

    context, payload, corpus = parse_inputs(context, payload, corpus)
    decision = triage(context, payload)
    result = {"schema_version": "1", "case_id": payload["case_id"], "status": "escalated",
              "ownership": "paused", "triage": decision, "draft": None,
              "evidence": [], "handoff": None}
    reason = decision["reason"]
    if reason == "human_ownership":
        result.update(status="human_owned", ownership="human")
        return result
    if reason == "support":
        document, reason = retrieve(context, payload["topic"], corpus)
        if reason == "eligible":
            answer = document["answer"]
            result.update(status="draft", ownership="bot", draft=answer,
                          evidence=[{"id": document["id"], "product_version": document["product_version"],
                                     "locator": document["locator"],
                                     "sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest()}])
            return result
    result["handoff"] = {"status": "pending", "ownership": "paused", "proposed_owner": context["proposed_owner"],
                         "reason": reason, "summary": "case:" + payload["case_id"],
                         "next_action": "await_human_review"}
    return result
