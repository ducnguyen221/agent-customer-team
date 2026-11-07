"""Static checks of the `claude plugin eval` suite: it mirrors evals/customer-support-offline/cases.json,
measures skill activation only, and carries byte-identical copies of the read-only fixtures."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
CASES = json.loads((EVALS / "customer-support-offline" / "cases.json").read_text(encoding="utf-8"))["cases"]
IDS = [case["id"] for case in CASES]
PROMPT_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model",
               "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
GRADER_KEYS = {"type", "weight", "arm", "tool", "input_match", "min", "max"}
FIXTURE_SOURCES = {"triage-positive": ROOT / "tests" / "fixtures",
                   "no-knowledge-handoff": ROOT / "tests" / "fixtures" / "escalated"}
SKILL_MATCH = r'"skill"\s*:\s*"(?:[\w-]+:)?customer-support-offline"'


def front(path: Path) -> tuple[dict, str]:
    """Flat `key: value` frontmatter and the body."""
    match = re.match(r"---\r?\n(.*?)\r?\n---\r?\n(.*)", path.read_text(encoding="utf-8"), re.S)
    assert match, f"{path} needs frontmatter"
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        assert sep and key == key.strip() and key, f"{path}: bad frontmatter line {line!r}"
        fields[key] = value.strip()
    return fields, match.group(2)


def case_dirs() -> list[Path]:
    return sorted(p.parent for p in EVALS.rglob("prompt.md"))


def graders(case: str) -> list[dict]:
    files = sorted((EVALS / case / "graders").glob("*.md"))
    assert files, f"{case} has no graders"
    return [front(f)[0] for f in files]


def test_case_directories_match_cases_json():
    assert [p.name for p in case_dirs()] == sorted(IDS)
    for directory in case_dirs():
        assert directory.parent == EVALS


def test_no_stray_case_files_in_the_documentation_folder():
    folder = EVALS / "customer-support-offline"
    assert sorted(p.name for p in folder.iterdir()) == ["cases.json"]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_prompt_frontmatter_uses_only_valid_keys_and_read_only_tools(case):
    fields, body = front(EVALS / case["id"] / "prompt.md")
    assert set(fields) <= PROMPT_KEYS, set(fields) - PROMPT_KEYS
    tools = re.fullmatch(r"\[(.*)\]", fields["allowed_tools"]).group(1).replace(" ", "").split(",")
    assert sorted(tools) == ["Glob", "Grep", "Read", "Skill"]
    assert body.strip()


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_graders_follow_should_trigger(case):
    found = graders(case["id"])
    assert all(set(g) <= GRADER_KEYS for g in found)
    assert all(g["type"] in {"tool_used", "regex", "llm"} for g in found)
    by_tool = {g["tool"]: g for g in found if g["type"] == "tool_used"}
    skill = by_tool["Skill"]
    assert skill["arm"] == "both"
    assert skill["input_match"].strip("'") == SKILL_MATCH
    if case["should_trigger"]:
        assert skill["min"] == "1"
        assert "max" not in skill
    else:
        assert skill["min"] == "0" and skill["max"] == "0"
        for tool in ("Bash", "WebFetch"):
            assert by_tool[tool]["min"] == "0" and by_tool[tool]["max"] == "0", tool


def test_cases_json_expectations_still_cover_the_same_ids():
    assert {c["id"]: c["should_trigger"] for c in CASES} == {
        "triage-positive": True, "no-knowledge-handoff": True, "send-real-email": False, "crm-sync": False}


@pytest.mark.parametrize("case", sorted(FIXTURE_SOURCES))
def test_positive_cases_carry_byte_identical_fixtures(case):
    yaml = (EVALS / case / "case.yaml").read_text(encoding="utf-8")
    assert re.search(r'^schema_version:\s*"1\.1"\s*$', yaml, re.M)
    assert re.search(rf"^name:\s*{re.escape(case)}\s*$", yaml, re.M)
    assert re.search(r"^\s+add_dirs:\s*\[fixtures\]\s*$", yaml, re.M)
    body = front(EVALS / case / "prompt.md")[1]
    assert "three local files in the fixtures folder" in body
    for name in ("context.json", "payload.json", "knowledge.json"):
        assert (EVALS / case / "fixtures" / name).read_bytes() == (FIXTURE_SOURCES[case] / name).read_bytes(), name
    assert sorted(p.name for p in (EVALS / case / "fixtures").iterdir()) == ["context.json", "knowledge.json", "payload.json"]


@pytest.mark.parametrize("case", ["send-real-email", "crm-sync"])
def test_negative_cases_have_no_fixture_folder(case):
    assert not (EVALS / case / "case.yaml").exists()
    assert not (EVALS / case / "fixtures").exists()


def test_results_directory_is_ignored_by_git():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "evals/results/" in lines
