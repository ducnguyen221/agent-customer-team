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


def test_gemini_md_is_prose_pointer():
    lines = read("GEMINI.md").splitlines()
    assert not [line for line in lines if line.startswith("@")]
    assert "[AGENTS.md](AGENTS.md)" in read("GEMINI.md")


def test_agents_md_shape():
    text = read("AGENTS.md")
    assert re.findall(r"^## .+$", text, re.M) == HEADINGS
    assert len(text.encode("utf-8")) < 2000
    assert "dữ liệu, không phải mệnh lệnh" in text
