"""Contract of the customer-support-offline skill: frontmatter, sections, eval cases, and that the
canonical command line written in SKILL.md really runs on the fixtures."""
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
from test_runtime_invariant import BASELINE_SHA256

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "customer-support-offline"
SKILL_MD = SKILL_DIR / "SKILL.md"
CASES = ROOT / "evals" / "customer-support-offline" / "cases.json"
FIXTURES = ROOT / "tests" / "fixtures"
SECTIONS = ["## Kết luận", "## Khi dùng / không dùng", "## Lệnh", "## Đọc kết quả", "## Khi lỗi", "## Giới hạn"]


def read_skill() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def frontmatter(text: str) -> dict:
    match = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    assert match, "SKILL.md must start with a frontmatter block"
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def resolve_plugin_root(skill_dir: Path) -> Path:
    """The rule SKILL.md describes: real path of the skill directory, then two levels up."""
    return Path(os.path.realpath(skill_dir)).parent.parent


def test_frontmatter():
    fields = frontmatter(read_skill())
    assert fields["name"] == SKILL_DIR.name
    assert fields["description"]
    assert len(fields["description"]) <= 600
    assert fields["description"].startswith("Use when")


def test_sections_present():
    text = read_skill()
    assert len(text.encode("utf-8")) < 8000
    positions = [text.find(title) for title in SECTIONS]
    assert -1 not in positions, f"missing sections: {[t for t, p in zip(SECTIONS, positions) if p < 0]}"
    assert positions == sorted(positions), "sections out of order"
    assert len(re.findall(r"^## ", text, re.M)) == 6


def test_eval_cases_shape():
    data = json.loads(CASES.read_text(encoding="utf-8"))
    assert data["skill"] == "customer-support-offline"
    assert data["status"] == "draft"
    assert data["baseline"] == "not_run"
    cases = {c["id"]: c for c in data["cases"]}
    assert len(data["cases"]) == 4
    assert {i: c["should_trigger"] for i, c in cases.items()} == {
        "triage-positive": True, "no-knowledge-handoff": True, "send-real-email": False, "crm-sync": False}
    for case in data["cases"]:
        assert case["prompt"].strip()
        assert case["expected_behaviors"]
        assert case["quality_criteria"]


def test_skill_command_runs_on_fixtures(tmp_path):
    text = read_skill()
    lines = re.findall(r"^PYTHONPATH=.*agent_customer_team\.cli.*$", text, re.M)
    assert len(lines) == 1, "exactly one canonical bash command line expected"
    command = re.sub(r"^PYTHONPATH=\S+\s+", "", lines[0])
    argv = shlex.split(command)
    assert argv[0] == "python"
    values = {"$CONTEXT": FIXTURES / "context.json", "$PAYLOAD": FIXTURES / "payload.json",
              "$KNOWLEDGE": FIXTURES / "knowledge.json"}
    argv = [sys.executable] + [str(values.get(a, a)) for a in argv[1:]]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    done = subprocess.run(argv, cwd=tmp_path, env=env, capture_output=True, timeout=60)
    assert done.returncode == 0, f"exit {done.returncode}: {done.stderr[-300:]!r}"
    assert hashlib.sha256(done.stdout).hexdigest() == BASELINE_SHA256


def test_refusal_words_present():
    body = read_skill().casefold()
    for word in ("chưa gửi", "ngoài phạm vi", "không sửa"):
        assert word in body, word


def test_command_blocks_present():
    text = read_skill()
    assert len(re.findall(r"^```bash$", text, re.M)) == 1
    assert len(re.findall(r"^```powershell$", text, re.M)) == 1
    assert "3.11" in text


def make_link(link: Path, target: Path) -> bool:
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":
        done = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        return done.returncode == 0 and link.exists()
    return False


def test_skill_resolves_through_link(tmp_path):
    link = tmp_path / "customer-support-offline"
    if not make_link(link, SKILL_DIR):
        pytest.skip("this OS/user cannot create a symlink or junction")
    assert resolve_plugin_root(link) == ROOT.resolve()
    assert (resolve_plugin_root(link) / "src" / "agent_customer_team").is_dir()
