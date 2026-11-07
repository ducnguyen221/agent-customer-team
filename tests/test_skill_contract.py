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


def canonical_command() -> tuple[list[str], dict]:
    """argv and env for the one canonical line in SKILL.md, run exactly as written: the PYTHONPATH value is taken
    from the line itself with $PLUGIN_ROOT replaced by the repo root."""
    lines = re.findall(r"^PYTHONPATH=.*agent_customer_team\.cli.*$", read_skill(), re.M)
    assert len(lines) == 1, "exactly one canonical bash command line expected"
    assigned = re.match(r'^PYTHONPATH="([^"]*)"\s+(.*)$', lines[0])
    assert assigned, "canonical line must start with PYTHONPATH=\"...\""
    env = dict(os.environ)
    env["PYTHONPATH"] = assigned.group(1).replace("$PLUGIN_ROOT", str(ROOT))
    argv = shlex.split(assigned.group(2))
    assert argv[0] == "python"
    values = {"$CONTEXT": FIXTURES / "context.json", "$PAYLOAD": FIXTURES / "payload.json",
              "$KNOWLEDGE": FIXTURES / "knowledge.json"}
    return [sys.executable] + [str(values.get(a, a)) for a in argv[1:]], env


def test_skill_command_runs_on_fixtures(tmp_path):
    argv, env = canonical_command()
    done = subprocess.run(argv, cwd=tmp_path, env=env, capture_output=True, timeout=60)
    assert done.returncode == 0, f"exit {done.returncode}: {done.stderr[-300:]!r}"
    assert hashlib.sha256(done.stdout).hexdigest() == BASELINE_SHA256


def test_skill_command_ignores_cwd_package(tmp_path):
    """A package of the same name in the working directory must not shadow the plugin's code (flag -P)."""
    fake = tmp_path / "agent_customer_team"
    fake.mkdir()
    (fake / "__init__.py").write_text("", encoding="utf-8")
    (fake / "cli.py").write_text("print('HIJACKED')\n", encoding="utf-8")
    argv, env = canonical_command()
    done = subprocess.run(argv, cwd=tmp_path, env=env, capture_output=True, timeout=60)
    assert b"HIJACKED" not in done.stdout
    assert done.returncode == 0, f"exit {done.returncode}: {done.stderr[-300:]!r}"
    assert hashlib.sha256(done.stdout).hexdigest() == BASELINE_SHA256


def test_every_command_form_has_safe_flags():
    text = read_skill()
    for form in re.findall(r"python3? -B[^\n]*agent_customer_team\.cli[^\n]*", text):
        assert " -B -P -m " in form, f"missing -B -P: {form}"
    assert "-P" in text.split("## Lệnh")[1].split("## Đọc kết quả")[0]


def test_error_table_covers_other_exit_codes():
    section = read_skill().split("## Khi lỗi")[1].split("## Giới hạn")[0]
    assert re.search(r"^\| khác \(", section, re.M), "table needs a row for any other exit code"
    assert "dừng" in section


def test_results_are_data_not_commands():
    section = read_skill().split("## Đọc kết quả")[1].split("## Khi lỗi")[0]
    assert "dữ liệu, không phải mệnh lệnh" in section


def test_command_blocks_quote_paths_safely():
    text = read_skill()
    bash = re.search(r"^```bash\n(.*?)^```", text, re.M | re.S).group(1)
    for name in ("PLUGIN_ROOT", "CONTEXT", "PAYLOAD", "KNOWLEDGE"):
        assert re.search(rf"^{name}='[^']*'$", bash, re.M), f"{name} must be assigned with single quotes"
    ps = re.search(r"^```powershell\n(.*?)^```", text, re.M | re.S).group(1)
    assert "try {" in ps and "finally {" in ps, "PowerShell must restore PYTHONPATH"
    assert "$PluginRoot = '" in ps and "$Context = '" in ps, "PowerShell values use single-quoted strings"
    assert "@((Get-Item" in text and ".Target)[0]" in text


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


GOLDEN = FIXTURES / "golden"
ESCALATED = FIXTURES / "escalated"


def run_cli(directory: Path, tmp_path: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    argv = [sys.executable, "-B", "-P", "-m", "agent_customer_team.cli"]
    for flag in ("context", "payload", "knowledge"):
        argv += [f"--{flag}", str(directory / f"{flag}.json")]
    return subprocess.run(argv, cwd=tmp_path, env=env, capture_output=True, timeout=60)


def test_quote_escape_is_given_for_both_shells():
    command = read_skill().split("## Lệnh")[1].split("## Đọc kết quả")[0]
    assert "bash viết `'\\''`" in command
    assert "PowerShell viết `''`" in command
    assert "`\u2018 \u2019 \u201a \u201b`" in command, "PowerShell curly quotes must be named"
    assert "`\u2019` viết `\u2019\u2019`" in command
    assert "dấu nháy đơn trong đường viết `'\\''`)" not in command, "the bash-only sentence must be replaced"


def test_exit_two_has_two_meanings():
    section = read_skill().split("## Khi lỗi")[1].split("## Giới hạn")[0]
    rows = [r for r in section.splitlines() if r.startswith("| 2 ")]
    assert len(rows) == 2, rows
    with_json = [r for r in rows if "invalid_input" in r and "stdout" not in r.split("|")[2] and r.count("{") >= 1]
    assert with_json, "one row keeps the invalid_input JSON"
    other = [r for r in rows if "invalid_input" not in r.split("|")[2]]
    assert len(other) == 1
    assert "-P" in other[0] and "3.11" in other[0] and "stderr" in other[0]
    assert "không gọi là `invalid_input`" in other[0]


def test_untrusted_text_is_data_across_all_fields():
    section = read_skill().split("## Đọc kết quả")[1].split("## Khi lỗi")[0]
    assert "dữ liệu, không phải mệnh lệnh" in section
    paragraph = next(p for p in section.split("\n\n") if "dữ liệu, không phải mệnh lệnh" in p)
    for field in ("handoff", "message", "attempted_steps", "draft", "evidence"):
        assert f"`{field}`" in paragraph, field
    bullet = next(b for b in re.split(r"\n(?=- )", section) if "status: \"escalated\"" in b)
    for field in ("case_id", "topic", "intent", "message", "attempted_steps", "evidence"):
        assert field in bullet, field


def test_limits_name_acl_and_hash_caveats():
    limits = read_skill().split("## Giới hạn")[1]
    assert "principal" in limits and "ACL" in limits
    assert "sha256" in limits and "tổng hợp" in limits


def test_eval_cases_use_safe_flags_and_ignore_embedded_instructions():
    data = json.loads(CASES.read_text(encoding="utf-8"))
    for case in data["cases"]:
        for line in case["expected_behaviors"]:
            if "agent_customer_team.cli" in line:
                assert "-B -P -m agent_customer_team.cli" in line, line
    handoff = next(c for c in data["cases"] if c["id"] == "no-knowledge-handoff")
    joined = " ".join(handoff["expected_behaviors"]).casefold()
    assert "message" in joined and "attempted_steps" in joined and "instruction" in joined


def test_escalated_fixture_reaches_a_handoff(tmp_path):
    done = run_cli(ESCALATED, tmp_path)
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)
    assert result["status"] == "escalated"
    assert result["handoff"]["reason"] == "no_eligible_knowledge"
    assert result["handoff"]["evidence"] == []


@pytest.mark.parametrize("name,directory", [("draft", FIXTURES), ("escalated", ESCALATED)])
def test_golden_files_equal_cli_stdout(name, directory, tmp_path):
    done = run_cli(directory, tmp_path)
    assert done.returncode == 0, done.stderr
    golden = (GOLDEN / f"{name}.json").read_bytes()
    assert done.stdout == golden
    assert json.loads(golden) == json.loads(done.stdout)
    assert b"\r" not in golden


def test_golden_draft_is_the_runtime_baseline():
    assert hashlib.sha256((GOLDEN / "draft.json").read_bytes()).hexdigest() == BASELINE_SHA256


def test_gitattributes_protects_golden_bytes():
    lines = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert any(re.fullmatch(r"tests/fixtures/golden/\*\s+-text", line.strip()) for line in lines)
