"""Repository text holds no invisible or direction-changing characters in raw form."""
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml", ".toml", ".txt", ".in"}
NAMES = {"LICENSE", ".gitignore", ".gitattributes"}
SKIP = {".git", ".claude", ".venv", ".tmp", "__pycache__", ".pytest_cache", "results"}


def hidden(char: str) -> bool:
    kind = unicodedata.category(char)
    return kind in ("Cf", "Zl", "Zp", "Co", "Cn", "Cs") or (kind == "Cc" and char not in "\n\r\t")


def text_files():
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and (path.suffix in SUFFIXES or path.name in NAMES) and not SKIP.intersection(path.relative_to(ROOT).parts):
            yield path


def test_no_raw_invisible_characters():
    found = []
    for path in text_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            codes = sorted({"U+%04X" % ord(c) for c in line if hidden(c)})
            if codes:
                found.append(f"{path.relative_to(ROOT).as_posix()}:{number} {' '.join(codes)}")
    assert found == [], "write these characters as escapes: " + "; ".join(found)


def test_detector_flags_the_characters_it_must():
    for code in (0x200B, 0x200D, 0x202E, 0x2066, 0x2028, 0x2029, 0xFEFF, 0x0085, 0x007F, 0x0378):
        assert hidden(chr(code)), hex(code)
    for char in "aéệ’\t":
        assert not hidden(char), repr(char)
