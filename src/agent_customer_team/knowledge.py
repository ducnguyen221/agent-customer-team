"""Select approved synthetic evidence without exposing inaccessible records."""
import unicodedata

from .contracts import identifier, text, valid_date

SCOPE = ("tenant_id", "product", "product_version", "topic")
FIELDS = set(SCOPE) | {"id", "status", "acl", "effective_from", "expires_at", "locator", "answer"}


def retrieve(context: dict, topic: str, corpus: dict) -> tuple[dict | None, str, list[dict]]:
    """Filter access before checking potentially confidential content."""
    eligible = []
    for item in corpus["documents"]:
        if not isinstance(item, dict) or not all(identifier(item.get(k)) for k in SCOPE):
            continue
        if any(item[k] != context[k] for k in SCOPE[:-1]) or item["topic"] != topic:
            continue
        acl = item.get("acl")
        if not isinstance(acl, list) or not all(identifier(x) for x in acl) or context["principal"] not in acl:
            continue
        if item.get("status") != "approved":
            continue
        start, end = item.get("effective_from"), item.get("expires_at")
        if not valid_date(start) or not valid_date(end) or start > end:
            return None, "invalid_scoped_knowledge", []
        if not start <= context["as_of"] <= end:
            continue
        locator = item.get("locator")
        if (set(item) != FIELDS or not identifier(item.get("id"))
                or not text(locator, 128) or any(unicodedata.category(c) == "Cc" for c in locator)
                or not text(item.get("answer"), 1024)):
            return None, "invalid_scoped_knowledge", []
        eligible.append(item)
    if not eligible:
        return None, "no_eligible_knowledge", []
    if len({item["id"] for item in eligible}) != len(eligible):
        return None, "invalid_scoped_knowledge", []
    if len({item["answer"] for item in eligible}) != 1:
        return None, "conflicting_knowledge", sorted(eligible, key=lambda item: item["id"])
    return min(eligible, key=lambda item: item["id"]), "eligible", []
