"""Identity-leak gate (distilled from agent-video-studio): the distributable tree must carry no
personal names, brand names, mailboxes, machine paths or private keys.

Every forbidden string is built with chr() so this file never matches itself. The scan walks
the directory tree (no git), so the gate is green or red before the first commit too.
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SELF = "tests/test_no_identity_leak.py"
# Any entry (file or directory) with one of these names is skipped, at every depth.
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".tmp", "build", "dist",
             "htmlcov", ".claude"}
# Files with no extension (LICENSE, .gitignore, ...) are always scanned as text.
TEXT_EXT = {".py", ".md", ".json", ".toml", ".yml", ".yaml", ".txt", ".cfg", ".ini", ".sh",
            ".ps1", ".html", ".css", ".js", ".svg", ".example", ".gitignore",
            ".gitattributes", ""}


def s(*codes):
    return "".join(map(chr, codes))


# key -> regex (matched case-insensitively unless the pattern says otherwise)
PATTERNS = {
    "brand-a": r"\b" + re.escape(s(116, 111, 98, 105)) + r"\b",
    "brand-b": r"\b" + re.escape(s(107, 112, 105, 109)) + r"\b",
    "ten-nguoi": r"(?-i:\b" + re.escape(s(0x110, 0x1EE9, 0x63)) + r"\b)",
    "tac-gia": re.escape(s(100, 117, 99, 110, 103, 117, 121, 101, 110)) + "|" +
               re.escape(s(100, 117, 99, 32, 110, 103, 117, 121, 101, 110)),
    "mien": re.escape(s(100, 117, 99, 110, 103, 117, 121, 101, 110, 46, 118, 110)),
    "duong-may-win": re.escape(s(67, 58, 92, 85, 115, 101, 114, 115, 92)),
    "duong-may-env": re.escape(s(37, 85, 83, 69, 82, 80, 82, 79, 70, 73, 76, 69, 37)),
    "email": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}",
    "duong-may-mac": re.escape(s(47, 85, 115, 101, 114, 115, 47)) + r"[A-Za-z][\w.-]*/",
    "pem": r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----",
}

# (relative path, key) -> number of matches tolerated. Starts empty: add an entry only for an
# approved credit line and write the reason beside it.
EXEMPT: dict[tuple[str, str], int] = {}


def distributable_files(root: Path) -> list[Path]:
    """Text files of the tree under root (no git), skipping every entry named in SKIP_DIRS."""
    found = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name in SKIP_DIRS:
                continue
            path = Path(base) / name
            if path.suffix.lower() in TEXT_EXT or name == "LICENSE":
                found.append(path)
    return sorted(found)


def scan(root: Path) -> list[str]:
    """One line per (file, key) whose match count exceeds EXEMPT; never prints the match."""
    lines = []
    for path in distributable_files(root):
        rel = path.relative_to(root).as_posix()
        if rel == SELF:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            lines.append(f"{rel}: khong-doc-duoc")
            continue
        for key, pattern in PATTERNS.items():
            n = len(re.findall(pattern, text, flags=re.IGNORECASE))
            if n > EXEMPT.get((rel, key), 0):
                lines.append(f"{rel}: {key} x{n}")
    return sorted(lines)


def test_tree_has_no_identity_leak():
    lines = scan(ROOT)
    assert lines == [], "identity leak:\n" + "\n".join(lines)


def test_scanner_catches_planted_leak(tmp_path):
    (tmp_path / "README.md").write_text("contact " + "someone" + "@" + "example.com" + "\n", encoding="utf-8")
    (tmp_path / "hosts" / "x").mkdir(parents=True)
    (tmp_path / "hosts" / "x" / "README.md").write_text(s(67, 58, 92, 85, 115, 101, 114, 115, 92) + "x\n", encoding="utf-8")
    assert scan(tmp_path) == ["README.md: email x1", "hosts/x/README.md: duong-may-win x1"]


def test_skip_dirs_ignored(tmp_path):
    leak = s(67, 58, 92, 85, 115, 101, 114, 115, 92) + "x\n"
    (tmp_path / ".git").write_text(leak, encoding="utf-8")          # a *file* named .git (worktree)
    for name in (".tmp", ".claude", "__pycache__"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "x.md").write_text(leak, encoding="utf-8")
    (tmp_path / "keep.md").write_text("clean\n", encoding="utf-8")
    assert [p.name for p in distributable_files(tmp_path)] == ["keep.md"]
    assert scan(tmp_path) == []


def test_scanner_sees_the_repo():
    seen = {p.relative_to(ROOT).as_posix() for p in distributable_files(ROOT)}
    for must in ("README.md", "pyproject.toml", ".gitignore"):
        assert must in seen, f"gate does not see {must}"


def test_patterns_catch_their_target():
    samples = {
        "brand-a": "brand " + s(84, 111, 98, 105) + " site",
        "brand-b": s(75, 80, 73, 77) + " Academy",
        "ten-nguoi": "anh " + s(0x110, 0x1EE9, 0x63) + " viet",
        "tac-gia": s(68, 117, 99, 32, 78, 103, 117, 121, 101, 110),
        "mien": "site: " + s(100, 117, 99, 110, 103, 117, 121, 101, 110, 46, 118, 110) + "/news",
        "duong-may-win": s(67, 58, 92, 85, 115, 101, 114, 115, 92) + "x",
        "duong-may-env": s(37, 85, 83, 69, 82, 80, 82, 79, 70, 73, 76, 69, 37) + "/x",
        "email": "someone" + "@" + "example.com",
        "duong-may-mac": s(47, 85, 115, 101, 114, 115, 47) + "someone/x",
        "pem": "-----BEGIN " + "RSA " + "PRIVATE KEY-----",
    }
    assert set(samples) == set(PATTERNS), "every pattern needs a positive sample"
    for key, text in samples.items():
        assert re.search(PATTERNS[key], text, flags=re.IGNORECASE), key
    # not a personal name, not an email
    assert not re.search(PATTERNS["ten-nguoi"], s(0x111, 0x1EA1, 0x6F, 32, 0x111, 0x1EE9, 0x63), flags=re.IGNORECASE)
    assert not re.search(PATTERNS["email"], "agent-customer-team@agent-customer-team")
    assert not re.search(PATTERNS["email"], "@AGENTS.md")


def test_undecodable_file_is_reported(tmp_path):
    (tmp_path / "bad.md").write_bytes(b"\xff\xfe\x00bad")
    assert scan(tmp_path) == ["bad.md: khong-doc-duoc"]
