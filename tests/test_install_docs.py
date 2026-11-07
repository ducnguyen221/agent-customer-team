"""User and install documents: they exist, relative links resolve, INSTALL.md covers every host with a short
paste-in prompt, the READMEs state the limits, and the Python floor is one number everywhere."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOSTS = ("claude", "codex", "antigravity", "claude-desktop")
USER_DOCS = (
    "README.md", "README.vi.md", "INSTALL.md", "ECOSYSTEM.md", "CHANGELOG.md", "docs/offline-guide.md",
    "hosts/README.md", *[f"hosts/{h}/README.md" for h in HOSTS],
)
LINK = re.compile(r"\]\(([^)\s]+)\)")
FENCE_ANY = re.compile(r"^```.*?^```[ \t]*$", re.M | re.S)
FENCE_TEXT = re.compile(r"^```text\r?\n(.*?)^```[ \t]*$", re.M | re.S)
CODE_SPAN = re.compile(r"`[^`\n]*`")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def broken_links(text: str, base: Path) -> list[str]:
    """Relative links whose target is missing. External URLs, in-page anchors, fenced code and code spans are ignored."""
    broken = []
    for target in LINK.findall(CODE_SPAN.sub("", FENCE_ANY.sub("", text))):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) or target.startswith("#"):
            continue
        path = target.split("#", 1)[0]
        if path and not (base / path).exists():
            broken.append(target)
    return broken


def test_user_docs_exist():
    missing = [rel for rel in USER_DOCS if not (ROOT / rel).is_file()]
    assert missing == [], f"missing user docs: {missing}"


def test_relative_links_resolve():
    bad = {}
    for rel in USER_DOCS:
        path = ROOT / rel
        found = broken_links(path.read_text(encoding="utf-8"), path.parent)
        if found:
            bad[rel] = found
    assert bad == {}, f"broken relative links: {bad}"


def test_install_covers_hosts():
    text = read("INSTALL.md")
    missing = [h for h in HOSTS if f"hosts/{h}/README.md" not in text or not (ROOT / "hosts" / h / "README.md").is_file()]
    assert missing == [], f"INSTALL.md does not link an existing host page for: {missing}"


def test_install_prompt_short():
    blocks = FENCE_TEXT.findall(read("INSTALL.md"))
    assert blocks, "INSTALL.md needs a paste-in prompt in a text block"
    assert len(blocks[-1].strip().splitlines()) <= 12


def test_readmes_state_limits():
    en, vi = read("README.md"), read("README.vi.md")
    for word in ("synthetic", "production", "UNLICENSED"):
        assert word in en, f"README.md lacks {word!r}"
    for word in ("tổng hợp", "production", "UNLICENSED"):
        assert word in vi, f"README.vi.md lacks {word!r}"
    assert "README.vi.md" in en and "README.md" in vi, "the two READMEs must link each other"


def test_ecosystem_has_five_fields():
    text = read("ECOSYSTEM.md")
    for field in ("Role", "Upstream", "Downstream", "Bundles", "Handoff"):
        assert re.search(rf"^- \*\*{field}:\*\* \S", text, re.M), f"ECOSYSTEM.md lacks {field}"


def test_python_floor_consistent():
    for rel in ("INSTALL.md", "README.md", "README.vi.md"):
        text = read(rel)
        assert "3.11" in text, f"{rel} must state Python 3.11"
        assert not re.search(r"3\.(?:9|10)(?!\d)", text), f"{rel} promises a lower Python"


def test_link_checker_catches_a_broken_link(tmp_path):
    (tmp_path / "real.md").write_text("x", encoding="utf-8")
    text = ("[ok](real.md) [gone](missing.md) [web](https://example.org/x) [anchor](#top)\n"
            "```text\n[in code](nothing.md)\n```\n")
    assert broken_links(text, tmp_path) == ["missing.md"]
