"""All release manifests share one version, and the changelog leads with it."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?")
MANIFESTS = ["plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def manifest_versions() -> dict[str, str]:
    found = {rel: json.loads(read(rel)).get("version") for rel in MANIFESTS}
    market = json.loads(read(".claude-plugin/marketplace.json"))
    for plugin in market.get("plugins", []):
        found[f".claude-plugin/marketplace.json#{plugin.get('name')}"] = plugin.get("version")
    return found


def test_all_manifests_share_one_semver_version():
    versions = manifest_versions()
    assert None not in versions.values(), f"missing version field: {versions}"
    assert len(set(versions.values())) == 1, f"manifest versions differ: {versions}"
    assert SEMVER.fullmatch(next(iter(versions.values())))


def test_marketplace_lists_this_plugin():
    plugins = json.loads(read(".claude-plugin/marketplace.json"))["plugins"]
    assert [p.get("name") for p in plugins] == ["agent-customer-team"]
    assert plugins[0].get("source") == "./"


def test_changelog_leads_with_current_version():
    version = next(iter(manifest_versions().values()))
    first = re.search(r"^## (\S+)", read("CHANGELOG.md"), re.MULTILINE)
    assert first and first.group(1) == version, (
        f"first CHANGELOG.md entry must be {version}, found {first.group(1) if first else None}")
