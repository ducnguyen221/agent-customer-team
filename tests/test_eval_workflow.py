"""Static checks of the behavior-eval workflow, its pinned CLI and the credential canary (standard library only).

The workflow uses a repository secret on a public repository, so these tests pin the properties that keep the secret
away from forks, from tool subprocesses, from logs and from kept artifacts."""
import json
import re
import subprocess
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "eval-behavior.yml"
LOCK = ROOT / ".github" / "eval" / "package-lock.json"
SCAN = ROOT / ".github" / "eval" / "scan.sh"
CANARY = ROOT / "evals-scrub" / "env-scrub"
CLI_VERSION = "2.1.310"


def code_lines() -> list[str]:
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    return [re.sub(r"\s+#.*$", "", line) for line in lines if line.strip() and not line.strip().startswith("#")]


def text() -> str:
    return "\n".join(code_lines())


def run_blocks() -> list[str]:
    """Shell bodies of every `run: |` step."""
    blocks, current, indent = [], None, None
    for line in code_lines():
        if current is not None:
            if indent is None:
                indent = len(line) - len(line.lstrip())
            if len(line) - len(line.lstrip()) >= indent:
                current.append(line.strip())
                continue
            blocks.append("\n".join(current))
            current, indent = None, None
        if re.match(r"^\s+run: \|$", line):
            current = []
        elif re.match(r"^\s+run: \S", line):
            blocks.append(line.split("run:", 1)[1].strip())
    if current is not None:
        blocks.append("\n".join(current))
    return blocks


def test_triggers_are_manual_or_label_only():
    block = re.search(r"^on:\n((?:[ \t]+.*\n?)+)", text() + "\n", re.M).group(1)
    assert set(re.findall(r"^  ([a-z_]+):", block, re.M)) == {"workflow_dispatch", "pull_request"}
    assert re.search(r"^  pull_request:\n    types: \[labeled\]$", block, re.M)
    assert "pull_request_target" not in text()
    assert not re.search(r"^  push:", block, re.M)


def test_job_runs_only_for_same_repository_pull_requests_and_the_two_labels():
    condition = " ".join(text().split())
    assert "github.event.pull_request.head.repo.full_name == github.repository" in condition
    assert "github.event.label.name == 'run-behavior-eval-smoke'" in condition
    assert "github.event.label.name == 'run-behavior-eval'" in condition


def test_token_is_read_only_and_checkout_keeps_no_credentials():
    assert re.search(r"^permissions:\n  contents: read$", text(), re.M)
    assert text().count("permissions:") == 1
    assert "persist-credentials: false" in text()
    assert "cache:" not in text()
    assert re.search(r"^    timeout-minutes: \d+$", text(), re.M)


def test_every_action_is_pinned_to_a_commit_sha():
    uses = re.findall(r"uses: (\S+)", text())
    assert uses
    assert all(re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", u) for u in uses), uses


def test_secrets_appear_only_in_step_level_env():
    lines = code_lines()
    for number, line in enumerate(lines):
        if "secrets." not in line:
            continue
        assert re.match(r"^ {10}[A-Z_]+: \$\{\{ secrets\.[A-Z_]+ \}\}$", line), line
        above = next(l for l in reversed(lines[:number]) if not l.startswith(" " * 10))
        assert above == "        env:", f"secret outside a step env block: {line}"
    job_env = re.search(r"^    env:\n((?: {6}.*\n)+)", text() + "\n", re.M).group(1)
    assert "secrets." not in job_env


def test_user_input_never_reaches_a_shell_body_through_an_expression():
    for body in run_blocks():
        assert "${{" not in body, body


def test_run_size_is_checked_before_use():
    body = next(b for b in run_blocks() if "GITHUB_ENV" in b)
    assert "[1-5]" in body and "([1-9]|10)(\\.[0-9]+)?" in body and "[a-z0-9*-]+" in body
    assert 'CASE="triage-positive"; RUNS="1"; MAX="1"' in body
    assert 'CASE="*"; RUNS="3"; MAX="5"' in body


def test_eval_commands_carry_the_safety_flags():
    evals = [b for b in run_blocks() if "claude plugin eval" in b]
    assert len(evals) == 2
    for body in evals:
        joined = " ".join(body.replace("\\\n", " ").split())
        for flag in ("--trust-plugin", "--no-publish", "--max-cost-usd", "--model", "--judge-model", "--allow-tools Bash"):
            assert flag in joined, (flag, joined)
        assert "/opt/acs" in joined
    assert "--eval-dir evals-scrub" in " ".join(evals[0].split())
    assert "--eval-dir evals-behavior" in " ".join(evals[1].split())


def test_eval_steps_scrub_the_tool_environment():
    steps = re.split(r"\n      - name: ", text())
    for step in steps:
        if "claude plugin eval" in step:
            assert 'CLAUDE_CODE_SUBPROCESS_ENV_SCRUB: "1"' in step, step.splitlines()[0]


def test_results_are_scanned_and_kept_even_when_the_eval_fails():
    steps = {s.splitlines()[0]: s for s in re.split(r"\n      - name: ", text())}
    scan = next(s for name, s in steps.items() if name.startswith("Scan results"))
    keep = next(s for name, s in steps.items() if name.startswith("Keep the results"))
    assert "if: always()" in scan and "id: scan" in scan and ".github/eval/scan.sh" in scan
    assert "if: always() && steps.scan.outcome == 'success'" in keep
    assert "retention-days: 7" in keep
    behavior = next(s for name, s in steps.items() if name == "Behavior eval")
    assert "if: steps.canary.outputs.exit == '0'" in behavior
    assert 'echo "exit=$code" >> "$GITHUB_OUTPUT"' in behavior


def test_cli_install_uses_the_lock_file_and_checks_signatures():
    assert "npm ci --prefix .github/eval" in text()
    assert "npm audit signatures --prefix .github/eval" in text()
    assert "npm install" not in text()


def test_lock_file_pins_the_cli_and_its_linux_binary_by_integrity():
    packages = json.loads(LOCK.read_text(encoding="utf-8"))["packages"]
    for name in ("@anthropic-ai/claude-code", "@anthropic-ai/claude-code-linux-x64"):
        entry = packages[f"node_modules/{name}"]
        assert entry["version"] == CLI_VERSION, name
        assert entry["integrity"].startswith("sha512-"), name
    assert packages[""]["dependencies"] == {"@anthropic-ai/claude-code": CLI_VERSION}


def test_canary_prints_a_length_never_the_value():
    prompt = (CANARY / "prompt.md").read_text(encoding="utf-8")
    assert "printenv ANTHROPIC_API_KEY | wc -c" in prompt
    assert not re.search(r"(echo|cat|printenv)\s+\$?ANTHROPIC_API_KEY\s*$", prompt, re.M)
    graders = {p.name: p.read_text(encoding="utf-8") for p in (CANARY / "graders").glob("*.md")}
    assert set(graders) == {"ran-the-command.md", "length-is-zero.md", "no-length-reported.md"}
    assert "match: not_contains" in graders["no-length-reported.md"]


@pytest.mark.parametrize("reply,ok", [("0", True), ("It printed 0.", True), ("109", False), ("0\n109", False)])
def test_canary_graders_tell_scrubbed_from_leaked(reply, ok):
    zero = re.search(r"\b0\b", reply) is not None
    long_number = re.search(r"\b[1-9][0-9]+\b", reply) is not None
    assert (zero and not long_number) is ok


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("grep") is None, reason="needs bash and grep")
@pytest.mark.parametrize("content,patterns,code", [
    ("plain result", "FAKE-SECRET-0000", 0),
    ("has FAKE-SECRET-0000 inside", "FAKE-SECRET-0000", 3),
    ("key sk-ant-" + "x" * 24, "", 3),
    ("plain result", "", 0),
])
def test_scan_script_finds_values_and_key_shapes(tmp_path, content, patterns, code):
    out = tmp_path / "out"
    out.mkdir()
    (out / "result.json").write_text(content, encoding="utf-8")
    pattern_file = tmp_path / "patterns"
    pattern_file.write_text(patterns + "\n" if patterns else "", encoding="utf-8")
    done = subprocess.run(["bash", SCAN.as_posix(), out.as_posix(), pattern_file.as_posix()],
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == code, done.stdout + done.stderr
    assert "FAKE-SECRET-0000" not in done.stdout + done.stderr


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("grep") is None, reason="needs bash and grep")
def test_scan_script_fails_when_it_cannot_read(tmp_path):
    empty = tmp_path / "patterns"
    empty.write_text("", encoding="utf-8")
    done = subprocess.run(["bash", SCAN.as_posix(), (tmp_path / "missing").as_posix(), empty.as_posix()],
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == 4
