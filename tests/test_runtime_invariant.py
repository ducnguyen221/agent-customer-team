"""Runtime invariant lock: the packaging layer must not change what the CLI does."""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import agent_customer_team

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
BASELINE_SHA256 = "4dda744a7fd40c54cd6af09d6a182f292c9fa69775a3cef44c776edab8efe4aa"


def run_fixture_cli() -> tuple[int, bytes]:
    """Run the CLI on the three fixtures; return (exit code, stdout bytes)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    done = subprocess.run(
        [sys.executable, "-B", "-m", "agent_customer_team.cli",
         "--context", str(FIXTURES / "context.json"),
         "--payload", str(FIXTURES / "payload.json"),
         "--knowledge", str(FIXTURES / "knowledge.json")],
        cwd=ROOT, env=env, capture_output=True, timeout=60)
    return done.returncode, done.stdout


def test_imports_repo_src():
    module = Path(agent_customer_team.__file__).resolve()
    assert (ROOT / "src").resolve() in module.parents, f"imported {module}, not the repo src"


def test_fixture_output_matches_baseline():
    code, out = run_fixture_cli()
    sha = hashlib.sha256(out).hexdigest()
    assert (code, sha) == (0, BASELINE_SHA256), f"exit {code}, sha256 {sha}"
