"""Packaging gate: manifests agree, the license file matches, skills are well formed, and no
sprint record, secret or scratch path is tracked by git."""
import json
import re
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


def test_license_file_matches_manifest():
    first = (ROOT / "LICENSE").read_text(encoding="utf-8").splitlines()[0].strip()
    assert first == load("plugin.json")["license"] == "UNLICENSED"


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
        if (name == ".agile.json"
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


def test_records_and_secrets_not_tracked():
    try:
        probe = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
                               capture_output=True, text=True, timeout=30)
        inside = probe.returncode == 0 and probe.stdout.strip() == "true"
        if inside:  # a plain copy placed inside another work tree is not this repository
            top = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
                                 capture_output=True, text=True, timeout=30).stdout.strip()
            inside = bool(top) and Path(top).resolve() == ROOT.resolve()
    except (OSError, subprocess.SubprocessError):
        inside = False
    if not inside:
        pytest.skip("git is unavailable or this is not a work tree")
    listed = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, text=True,
                            encoding="utf-8", timeout=30, check=True).stdout
    tracked = [p for p in listed.split("\0") if p]
    assert tracked, "git lists no tracked files"
    assert forbidden_tracked(tracked) == []
