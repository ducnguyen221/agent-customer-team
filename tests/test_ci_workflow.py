"""Static checks of .github/workflows/ci.yml, read line by line with the standard library only."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
LOCK = ROOT / "requirements-ci.txt"
LOCK_IN = ROOT / "requirements-ci.in"


def lines() -> list[str]:
    return WORKFLOW.read_text(encoding="utf-8").splitlines()


def code_lines() -> list[str]:
    return [re.sub(r"\s+#.*$", "", line) for line in lines() if line.strip() and not line.strip().startswith("#")]


def test_triggers_are_push_pull_request_and_manual():
    text = "\n".join(code_lines())
    block = re.search(r"^on:\n((?:[ \t]+.*\n?)+)", text + "\n", re.M).group(1)
    keys = set(re.findall(r"^  ([a-z_]+):", block, re.M))
    assert keys == {"push", "pull_request", "workflow_dispatch"}


def test_token_is_read_only():
    text = "\n".join(code_lines())
    assert re.search(r"^permissions:\n  contents: read\n(?!  )", text, re.M), "top-level permissions must be exactly contents: read"
    assert text.count("permissions:") == 1


def test_every_action_is_pinned_to_a_full_sha():
    uses = [line.strip() for line in code_lines() if re.match(r"\s*-?\s*uses:", line)]
    assert len(uses) == 2
    for line in uses:
        assert re.fullmatch(r"-?\s*uses: [\w.-]+/[\w.-]+@[0-9a-f]{40}", line), line
    raw = [line for line in lines() if "uses:" in line]
    assert all(re.search(r"@[0-9a-f]{40} # v\d+\.\d+\.\d+$", line) for line in raw), "pin needs the tag as a comment"


def test_matrix_is_three_os_by_three_pythons():
    text = "\n".join(code_lines())
    os_list = re.search(r"^\s+os: \[(.*)\]$", text, re.M).group(1)
    py_list = re.search(r"^\s+python-version: \[(.*)\]$", text, re.M).group(1)
    assert [x.strip() for x in os_list.split(",")] == ["ubuntu-latest", "macos-latest", "windows-latest"]
    assert [x.strip() for x in py_list.split(",")] == ['"3.11"', '"3.12"', '"3.13"']
    assert re.search(r"^\s+runs-on: \$\{\{ matrix\.os \}\}$", text, re.M)
    assert re.search(r"^\s+fail-fast: false$", text, re.M)
    assert re.search(r"^\s+timeout-minutes: 15$", text, re.M)


def test_checkout_does_not_persist_credentials():
    text = "\n".join(code_lines())
    assert re.search(r"^\s+persist-credentials: false$", text, re.M)


def test_concurrency_cancels_older_runs_of_the_same_ref():
    text = "\n".join(code_lines())
    assert re.search(r"^concurrency:\n  group: .*github\.ref.*\n  cancel-in-progress: true$", text, re.M)


def test_no_secrets_no_pull_request_target_no_cache():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "secrets." not in text
    assert "pull_request_target" not in text
    assert not re.search(r"^\s*cache:", text, re.M)
    assert "${{ github.event" not in text, "no event data may be interpolated into a script"


def test_dependencies_install_with_hashes_and_tests_run_with_branch_coverage():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "python -m pip install --require-hashes -r requirements-ci.txt" in text
    assert "python -B -m pytest --cov --cov-branch" in text


def test_lock_file_is_hashed_and_names_the_two_test_tools():
    assert [x for x in LOCK_IN.read_text(encoding="utf-8").split() if x] == ["pytest", "pytest-cov"]
    body = LOCK.read_text(encoding="utf-8")
    requirement_lines = re.findall(r"^([A-Za-z0-9_.\-]+(?:\[[^\]]*\])?==\S+)(?: ;.*)?\s*\\?$", body, re.M)
    names = {re.split(r"[=\[]", r)[0].lower() for r in requirement_lines}
    assert {"pytest", "pytest-cov", "coverage"} <= names
    entries = re.findall(r"^([A-Za-z0-9_.\-]+(?:\[[^\]]*\])?==.*(?:\n[ \t]+.*)*)", body, re.M)
    assert len(entries) == len(requirement_lines)
    for entry in entries:
        assert re.search(r"^\s+--hash=sha256:[0-9a-f]{64}", entry, re.M), entry.splitlines()[0]
    assert not re.search(r"^(?:git\+|https?://|-e )", body, re.M)
