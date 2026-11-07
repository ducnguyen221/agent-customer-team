"""Repository text holds no invisible or direction-changing characters in raw form."""
import sys
import unicodedata
from pathlib import Path

import pytest

from case_helpers import tracked_files

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml", ".toml", ".txt", ".in"}
NAMES = {"LICENSE", ".gitignore", ".gitattributes"}
SKIP = {".git", ".claude", ".venv", ".tmp", "__pycache__", ".pytest_cache", "results"}


def hidden(char: str) -> bool:
    kind = unicodedata.category(char)
    return kind in ("Cf", "Zl", "Zp", "Co", "Cn", "Cs") or (kind == "Cc" and char not in "\n\r\t")


def walked_files():
    """Fallback without git (a `git archive` copy): walk the tree and filter by name."""
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and (path.suffix in SUFFIXES or path.name in NAMES) and not SKIP.intersection(path.relative_to(ROOT).parts):
            yield path


def text_files():
    """Every git-tracked file that is not binary; the walk above when git is unavailable."""
    tracked = tracked_files(ROOT)
    if tracked is None:
        yield from walked_files()
        return
    for name in sorted(tracked):
        path = ROOT / name
        if path.is_file() and b"\0" not in path.read_bytes():
            yield path


def hidden_characters(paths) -> list[str]:
    """`path:line U+XXXX` for every raw hidden character; a file that is not UTF-8 raises instead of being skipped."""
    found = []
    for path in paths:
        for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            codes = sorted({"U+%04X" % ord(c) for c in line if hidden(c)})
            if codes:
                found.append(f"{path.as_posix()}:{number} {' '.join(codes)}")
    return found


def test_no_raw_invisible_characters():
    found = hidden_characters(text_files())
    assert found == [], "write these characters as escapes: " + "; ".join(found)


def test_detector_flags_the_characters_it_must():
    for code in (0x200B, 0x200D, 0x202E, 0x2066, 0x2028, 0x2029, 0xFEFF, 0x0085, 0x007F, 0x0378):
        assert hidden(chr(code)), hex(code)
    for char in "aéệ’\t":
        assert not hidden(char), repr(char)


def test_text_files_follow_git_when_available(monkeypatch):
    tracked = tracked_files(ROOT)
    if tracked is None:
        pytest.skip("git is unavailable or this is not a work tree")
    chosen = {p.relative_to(ROOT).as_posix() for p in text_files()}
    present = {n for n in tracked if (ROOT / n).is_file()}
    binary = {n for n in present if b"\0" in (ROOT / n).read_bytes()}
    assert chosen == present - binary
    monkeypatch.setattr(sys.modules[__name__], "tracked_files", lambda root: None)
    assert list(text_files()) == list(walked_files())


def test_undecodable_tracked_text_fails(tmp_path):
    """The scan used by the repository check raises on a file that is not UTF-8, never skips it silently."""
    good = tmp_path / "good.md"
    good.write_bytes(b"ok\n")
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"ok \xff\n")
    assert hidden_characters([good]) == []
    with pytest.raises(UnicodeDecodeError):
        hidden_characters([good, bad])


def test_no_stale_no_remote_wording():
    """RQ-015: the install docs no longer claim the repository has no remote."""
    names = tracked_files(ROOT)
    if names is None:
        pytest.skip("git is unavailable or this is not a work tree")
    found = []
    for name in names:
        path = ROOT / name
        if name == "tests/test_text_hygiene.py" or not path.is_file() or b"\0" in path.read_bytes():
            continue
        flat = " ".join(path.read_text(encoding="utf-8").split()).lower()
        for phrase in ("chưa có remote", "no remote yet"):
            if phrase in flat:
                found.append(f"{name}: {phrase}")
    assert found == []
