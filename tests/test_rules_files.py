"""Shape of the repository rule files. Content is reviewed by people; this only pins structure."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADINGS = ["## Phạm vi", "## Dữ liệu và quyền", "## Kiểm trước khi báo xong"]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_no_root_claude_md():
    """RQ-012: no CLAUDE.md at the root so `claude plugin validate --strict` passes; rules live in AGENTS.md."""
    assert not (ROOT / "CLAUDE.md").exists()


FIVE = ("INSTALL.md", "hosts/README.md", "hosts/claude/README.md", "README.md", "README.vi.md")
FULL = ("INSTALL.md", "hosts/claude/README.md")
POINTERS = ("hosts/README.md", "README.md", "README.vi.md")
OLD_PHRASES = ("hoặc thêm vào `CLAUDE.md` bạn đang dùng", "hoặc dùng đường tuyệt đối", "không tự nạp")


def flat(name: str) -> str:
    """Text with whitespace collapsed, so hard line breaks in the docs do not matter."""
    return " ".join(read(name).split())


def test_claude_guidance_gives_a_working_import():
    """RQ-014: one recommended import, `.claude/CLAUDE.md` with `@../AGENTS.md`, in all five files."""
    for name in FIVE:
        assert "`@../AGENTS.md`" in flat(name), name


def test_full_guides_warn_about_absolute_path_imports():
    """FR3.1-FR3.3: the two full guides name the single way, the auto-read condition and both warnings."""
    for name in FULL:
        text = flat(name)
        assert "Cách khuyến nghị duy nhất" in text, name
        assert "`~/.claude/CLAUDE.md` của bạn **không** tính" in text, name
        assert "**mọi** dự án" in text, name
        assert "hỏi duyệt import ngoài" in text, name


def test_short_files_point_to_the_full_guide():
    for name in POINTERS:
        text = flat(name)
        assert "claude/README.md" in text or "`INSTALL.md`" in text, name


def test_no_stale_import_wording():
    for name in FIVE:
        text = flat(name)
        for phrase in OLD_PHRASES:
            assert phrase not in text, (name, phrase)
        assert "(cấp dự án hay cấp người dùng)" not in text, name


def test_gemini_md_is_prose_pointer():
    lines = read("GEMINI.md").splitlines()
    assert not [line for line in lines if line.startswith("@")]
    assert "[AGENTS.md](AGENTS.md)" in read("GEMINI.md")


def test_agents_md_shape():
    text = read("AGENTS.md")
    assert re.findall(r"^## .+$", text, re.M) == HEADINGS
    assert len(text.encode("utf-8")) < 2000
    assert "dữ liệu, không phải mệnh lệnh" in text
