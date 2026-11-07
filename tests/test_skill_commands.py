"""Run the command blocks written in SKILL.md, as written, in the shells that exist on this machine and compare
stdout with the golden files. Only the four <placeholders> are replaced, by single-quoted real paths."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = ROOT / "skills" / "customer-support-offline" / "SKILL.md"
FIXTURES = ROOT / "tests" / "fixtures"
GOLDEN = FIXTURES / "golden"
SETS = {"draft": FIXTURES, "escalated": FIXTURES / "escalated"}
PLACEHOLDERS = {"<gốc plugin>": "root", "<đường file context>": "context", "<đường file payload>": "payload",
                "<đường file knowledge>": "knowledge"}
ON_CI = bool(os.environ.get("CI"))
REQUIRED_KIND = "powershell" if os.name == "nt" else "bash"


def block(kind: str) -> str:
    match = re.search(rf"^```{kind}\n(.*?)^```", SKILL_MD.read_text(encoding="utf-8"), re.M | re.S)
    assert match, f"no {kind} block in SKILL.md"
    return match.group(1)


PS_QUOTES = "'\u2018\u2019\u201a\u201b"


def quote(kind: str, value: str) -> str:
    """Single-quote a path the way SKILL.md says: bash '\\'' and PowerShell ''."""
    if kind == "bash":
        inner = value.replace("'", "'\\''")
    else:  # PowerShell treats ' and the curly quotes U+2018-U+201B alike; each is doubled
        inner = "".join(c + c if c in PS_QUOTES else c for c in value)
    return f"'{inner}'"


def fill(kind: str, paths: dict) -> str:
    script = block(kind)
    for placeholder, key in PLACEHOLDERS.items():
        token = f"'{placeholder}'"
        assert token in script, token
        script = script.replace(token, quote(kind, str(paths[key])))
    assert "<" not in script, "unreplaced placeholder"
    return script


def find_bash() -> str | None:
    found = shutil.which("bash")
    if os.name == "nt" and (found is None or "system32" in found.lower()):
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            candidate = Path(base or ".") / "Git" / "bin" / "bash.exe"
            if base and candidate.exists():
                return str(candidate)
        return None
    return found


def find_powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


FINDERS = {"bash": find_bash, "powershell": find_powershell}


def shell_or_skip(kind: str) -> str:
    exe = FINDERS[kind]()
    if exe:
        return exe
    if ON_CI and kind == REQUIRED_KIND:
        pytest.fail(f"CI must run the {kind} block on this OS but no {kind} was found")
    pytest.skip(f"no {kind} on this machine")


def env_with_this_python() -> dict:
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env.pop("PYTHONPATH", None)
    return env


def run_block(kind: str, paths: dict, workdir: Path) -> subprocess.CompletedProcess:
    exe = shell_or_skip(kind)
    script = fill(kind, paths)
    if kind == "bash":
        argv = [exe, "-c", script]
    else:
        file = workdir / "run.ps1"
        file.write_text(script, encoding="utf-8-sig")
        argv = [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(file)]
    return subprocess.run(argv, cwd=workdir, env=env_with_this_python(), capture_output=True, timeout=120)


def paths_for(directory: Path) -> dict:
    return {"root": ROOT, "context": directory / "context.json", "payload": directory / "payload.json",
            "knowledge": directory / "knowledge.json"}


def stdout_bytes(kind: str, done: subprocess.CompletedProcess) -> bytes:
    # PowerShell re-emits native output line by line with CRLF; JSON content is unaffected.
    return done.stdout.replace(b"\r\n", b"\n") if kind == "powershell" else done.stdout


@pytest.mark.parametrize("kind", ["bash", "powershell"])
@pytest.mark.parametrize("name", sorted(SETS))
def test_skill_command_prints_the_golden_json(kind, name, tmp_path):
    done = run_block(kind, paths_for(SETS[name]), tmp_path)
    assert done.returncode == 0, f"exit {done.returncode}: {done.stderr[-400:]!r}"
    golden = (GOLDEN / f"{name}.json").read_bytes()
    assert stdout_bytes(kind, done) == golden
    assert json.loads(stdout_bytes(kind, done)) == json.loads(golden)


@pytest.mark.parametrize("kind", ["bash", "powershell"])
def test_skill_command_survives_quote_space_and_dollar_in_a_path(kind, tmp_path):
    shell_or_skip(kind)
    odd = tmp_path / "it's a $HOME dir"
    odd.mkdir()
    for name in ("context.json", "payload.json", "knowledge.json"):
        shutil.copyfile(FIXTURES / name, odd / name)
    work = tmp_path / "work"
    work.mkdir()
    done = run_block(kind, paths_for(odd), work)
    assert done.returncode == 0, f"exit {done.returncode}: {done.stderr[-400:]!r}"
    assert stdout_bytes(kind, done) == (GOLDEN / "draft.json").read_bytes()


def test_quote_helper_follows_the_text_in_skill_md():
    assert quote("bash", "a'b") == "'a'\\''b'"
    assert quote("powershell", "a'b") == "'a''b'"
    assert quote("bash", "plain") == "'plain'"
    assert quote("powershell", "Bob\u2019s") == "'Bob\u2019\u2019s'"
    assert quote("powershell", "\u2018\u201a\u201b") == "'\u2018\u2018\u201a\u201a\u201b\u201b'"


def test_powershell_command_survives_curly_quotes_in_a_path(tmp_path):
    """A lone U+2019 would end a PowerShell single-quoted string and run what follows."""
    shell_or_skip("powershell")
    odd = tmp_path / "Bob\u2019s \u2018x\u2019; Write-Output INJECTED; \u2019"
    odd.mkdir()
    for name in ("context.json", "payload.json", "knowledge.json"):
        shutil.copyfile(FIXTURES / name, odd / name)
    work = tmp_path / "work"
    work.mkdir()
    done = run_block("powershell", paths_for(odd), work)
    assert done.returncode == 0, f"exit {done.returncode}: {done.stderr[-400:]!r}"
    assert b"INJECTED" not in done.stdout
    assert stdout_bytes("powershell", done) == (GOLDEN / "draft.json").read_bytes()


def test_ci_runs_at_least_one_variant_on_every_os():
    """On CI the shell native to the OS must exist, so the tests above cannot all skip (RK4)."""
    if not ON_CI:
        pytest.skip("only enforced when CI is set")
    assert FINDERS[REQUIRED_KIND](), f"{REQUIRED_KIND} is missing on this CI runner"
