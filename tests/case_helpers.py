"""Shared synthetic values for independent tests."""

C = {"tenant_id": "t1", "product": "app", "product_version": "v1", "principal": "u1", "as_of": "2026-01-01"}
D = {"id": "a", "tenant_id": "t1", "product": "app", "product_version": "v1", "topic": "reset", "status": "approved", "acl": ["u1"], "effective_from": "2026-01-01", "expires_at": "2026-12-31", "locator": "guide-1", "answer": "Khởi động lại ứng dụng."}
P = {"case_id": "case1", "message": "help", "intent": "support", "topic": "reset", "attempted_steps": []}
CTX = dict(C, ownership="bot", proposed_owner="agent")

def doc(**changes):
    return dict(D, **changes)
