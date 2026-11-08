"""Shared synthetic values and git helpers for independent tests."""
import shutil
import subprocess
from pathlib import Path

import pytest

C = {"tenant_id": "t1", "product": "app", "product_version": "v1", "principal": "u1", "as_of": "2026-01-01"}
D = {"id": "a", "tenant_id": "t1", "product": "app", "product_version": "v1", "topic": "reset", "status": "approved", "acl": ["u1"], "effective_from": "2026-01-01", "expires_at": "2026-12-31", "locator": "guide-1", "answer": "Khởi động lại ứng dụng."}
P = {"case_id": "case1", "message": "help", "intent": "support", "topic": "reset", "attempted_steps": []}
CTX = dict(C, ownership="bot", proposed_owner="agent")

def doc(**changes):
    return dict(D, **changes)


def run_git(*args: str, **kwargs) -> subprocess.CompletedProcess:
    """Run git with a hard timeout; a hang fails the test instead of blocking it."""
    try:
        return subprocess.run(["git", *args], capture_output=True, timeout=30, **kwargs)
    except subprocess.TimeoutExpired:
        pytest.fail("git " + " ".join(args) + " timed out after 30 s")


def tracked_files(root: Path) -> list[str] | None:
    """Tracked paths of the git repository rooted exactly at root; None when git or such a repository is missing."""
    if shutil.which("git") is None:
        return None
    try:
        probe = run_git("-C", str(root), "rev-parse", "--is-inside-work-tree", text=True)
        inside = probe.returncode == 0 and probe.stdout.strip() == "true"
        if inside:  # a plain copy placed inside another work tree is not this repository
            top = run_git("-C", str(root), "rev-parse", "--show-toplevel", text=True).stdout.strip()
            inside = bool(top) and Path(top).resolve() == root.resolve()
        if not inside:
            return None
        listed = run_git("-C", str(root), "ls-files", "-z", text=True, encoding="utf-8", check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return [p for p in listed.split("\0") if p]
