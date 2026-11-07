"""Packaging gate: manifests agree, the license file matches, skills are well formed, and no
sprint record, secret or scratch path is tracked by git."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = ["plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"]
REQUIRED = ["name", "version", "description", "license", "author"]
SKILL_LIMIT = 8000


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_manifests_parse_and_share_identity():
    manifests = {rel: load(rel) for rel in MANIFESTS}
    market = load(".claude-plugin/marketplace.json")
    entry = market["plugins"][0]
    assert market["name"] and market["owner"]["name"]
    for rel, data in {**manifests, ".claude-plugin/marketplace.json#plugin": entry}.items():
        missing = [k for k in REQUIRED if not data.get(k)]
        assert not missing, f"{rel} lacks {missing}"
    everyone = [*manifests.values(), entry]
    for field in ("name", "license", "author", "description"):
        values = {json.dumps(m[field], sort_keys=True) for m in everyone}
        assert len(values) == 1, f"{field} differs across manifests: {values}"
    assert manifests[".claude-plugin/plugin.json"]["skills"] == "./skills/"
    assert manifests[".codex-plugin/plugin.json"]["skills"] == "./skills/"
    assert "interface" in manifests[".codex-plugin/plugin.json"]


def test_manifest_specific_fields():
    root = load("plugin.json")
    assert root.get("$schema") == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert root.get("extensions", {}).get("org.agent-customer-team", {}).get("claudeManifest") == \
        ".claude-plugin/plugin.json"
    codex = load(".codex-plugin/plugin.json")
    interface = codex.get("interface")
    assert isinstance(interface, dict)
    for key in ("displayName", "shortDescription", "category", "capabilities"):
        assert interface.get(key), f"codex interface lacks {key}"
    for rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
        assert load(rel).get("skills") == "./skills/", f"{rel}: skills must be ./skills/"


def test_license_file_matches_manifest():
    first = (ROOT / "LICENSE").read_text(encoding="utf-8").splitlines()[0].strip()
    assert first == "MIT License"
    assert load("plugin.json")["license"] == "MIT"


def frontmatter(text: str) -> dict:
    match = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    assert match, "frontmatter missing"
    return {k.strip(): v.strip() for k, _, v in (line.partition(":") for line in match.group(1).splitlines())}


def test_skills_declared_correctly():
    folders = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    assert folders, "no skills found"
    for folder in folders:
        skill = folder / "SKILL.md"
        assert skill.is_file(), f"{folder.name} has no SKILL.md"
        raw = skill.read_bytes()
        assert len(raw) < SKILL_LIMIT, f"{folder.name}/SKILL.md is {len(raw)} bytes"
        text = raw.decode("utf-8")
        fields = frontmatter(text)
        assert fields.get("name") == folder.name, f"{folder.name}: frontmatter name {fields.get('name')!r}"
        assert fields.get("description"), f"{folder.name}: no description"
        for link in re.findall(r"\]\(([^)\s]+)\)", text):
            if link.startswith(("http://", "https://", "#", "mailto:")):
                continue
            assert (folder / link.split("#")[0]).exists(), f"{folder.name}: broken link {link}"


def forbidden_tracked(paths: list[str]) -> list[str]:
    bad = []
    for path in paths:
        parts = path.split("/")
        name = parts[-1]
        if (name in (".agile.json", "auth.json", "oauth_creds.json")
                or "output" in parts[:-1]
                or path.startswith(("docs/plans/", "docs/evidence/"))
                or (name.startswith(".env") and name != ".env.example")
                or name.endswith((".pem", ".key", ".credentials.json"))
                or {".tmp", ".claude"} & set(parts[:-1])):
            bad.append(path)
    return bad


def test_forbidden_detector_catches_its_targets():
    sample = [".agile.json", "docs/plans/a.md", "docs/evidence/b.md", ".env", ".env.production", "x/k.pem",
              "k.key", "a.credentials.json", ".tmp/x", ".claude/settings.json", "sub/.tmp/x"]
    assert forbidden_tracked(sample) == sample
    assert forbidden_tracked([".env.example", "README.md", ".claude-plugin/plugin.json", "skills/a/SKILL.md"]) == []
    # every secret entry of .gitignore
    more = ["auth.json", "sub/oauth_creds.json", "output/result.json", "x/output/y.txt"]
    assert forbidden_tracked(more) == more
    assert forbidden_tracked(["outputs/a.md", "src/output.py"]) == []


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


def test_records_and_secrets_not_tracked():
    tracked = tracked_files(ROOT)
    if tracked is None:
        pytest.skip("git is unavailable or this is not a work tree")
    assert tracked, "git lists no tracked files"
    assert forbidden_tracked(tracked) == []


def test_forced_secret_in_a_real_repo_is_flagged(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    if run_git("init", "-q", str(tmp_path)).returncode != 0:
        pytest.skip("git init failed in a temporary directory")
    (tmp_path / "auth.json").write_text("{}", encoding="utf-8")
    (tmp_path / "ok.md").write_text("ok", encoding="utf-8")
    assert run_git("-C", str(tmp_path), "add", "-f", "auth.json", "ok.md").returncode == 0
    tracked = tracked_files(tmp_path)
    assert tracked is not None and sorted(tracked) == ["auth.json", "ok.md"]
    assert forbidden_tracked(tracked) == ["auth.json"]


def test_missing_git_means_no_tracked_listing(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("git must not be started when it is missing")

    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.setattr(subprocess, "run", refuse)
    assert tracked_files(ROOT) is None


def test_hanging_git_fails_with_a_clear_message(monkeypatch):
    seen = []

    def hang(cmd, *args, **kwargs):
        seen.append(kwargs.get("timeout"))
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout"))

    monkeypatch.setattr(shutil, "which", lambda name: "git")
    monkeypatch.setattr(subprocess, "run", hang)
    with pytest.raises(pytest.fail.Exception, match="rev-parse .* timed out"):
        tracked_files(ROOT)
    assert seen == [30]
