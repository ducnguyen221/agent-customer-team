"""Validate the synthetic case envelope without trusting its payload."""
import re
from datetime import date

IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z", re.ASCII)
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", re.ASCII)


def identifier(value: object) -> bool:
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def text(value: object, maximum: int) -> bool:
    return (isinstance(value, str) and 1 <= len(value) <= maximum
            and bool(value.strip()) and not any(0xD800 <= ord(c) <= 0xDFFF for c in value))


def valid_date(value: object) -> bool:
    if not isinstance(value, str) or DATE.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def parse_inputs(context: object, payload: object, corpus: object) -> tuple[dict, dict, dict]:
    """Return validated objects; reject malformed envelopes without modification."""
    context_keys = {"tenant_id", "product", "product_version", "principal", "as_of", "ownership", "proposed_owner"}
    payload_keys = {"case_id", "message", "intent", "topic", "attempted_steps"}
    if not isinstance(context, dict) or set(context) != context_keys:
        raise ValueError("invalid context")
    if not all(identifier(context[k]) for k in ("tenant_id", "product", "product_version", "principal", "proposed_owner")):
        raise ValueError("invalid context")
    if not valid_date(context["as_of"]) or context["ownership"] not in ("bot", "human", "paused"):
        raise ValueError("invalid context")
    if not isinstance(payload, dict) or set(payload) != payload_keys:
        raise ValueError("invalid payload")
    if not identifier(payload["case_id"]) or not identifier(payload["topic"]) or not text(payload["message"], 1024):
        raise ValueError("invalid payload")
    if payload["intent"] not in ("support", "risk", "unknown"):
        raise ValueError("invalid payload")
    steps = payload["attempted_steps"]
    if not isinstance(steps, list) or len(steps) > 10 or not all(text(s, 1024) for s in steps):
        raise ValueError("invalid payload")
    if not isinstance(corpus, dict) or set(corpus) != {"documents"}:
        raise ValueError("invalid corpus")
    if not isinstance(corpus["documents"], list) or len(corpus["documents"]) > 100:
        raise ValueError("invalid corpus")
    return context, payload, corpus
