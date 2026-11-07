"""Lexical path guard: NT object prefixes and Windows device names are refused."""
import json
import pytest
from agent_customer_team.cli import _load, main

BS = "\\"


@pytest.mark.parametrize("path", [
    BS + "??" + BS + "C:" + BS + "Windows" + BS + "win.ini",
    "//??/C:/Windows/win.ini", "/??/C:/x.json",
    BS * 2 + "server" + BS + "share" + BS + "x.json", "//server/share/x.json",
    BS * 2 + "?" + BS + "C:" + BS + "x.json", BS * 2 + "." + BS + "PhysicalDrive0",
    "CON", "con", "NUL", "nul.json", "PRN", "AUX", "COM1", "com9.txt", "LPT1", "lpt9",
    "dir" + BS + "CON", "dir/aux.json", "C:" + BS + "data" + BS + "NUL.json",
    "CON.", "CON ", "CON:", "CONIN$", "CONOUT$",
])
def test_refused_paths_raise_oserror(path):
    with pytest.raises(OSError):
        _load(path)


@pytest.mark.parametrize("name", ["console.json", "com0.json", "com10.json", "lpt0.json", "nullable.json", "auxiliary.json", "prn1.json"])
def test_similar_but_ordinary_names_still_load(tmp_path, name):
    path = tmp_path / name
    path.write_text(json.dumps({"ok": 1}), encoding="utf-8")
    assert _load(str(path)) is not None


def test_nt_prefix_returns_read_error_exit(capsysbinary):
    args = ["--context", BS + "??" + BS + "C:" + BS + "Windows" + BS + "win.ini", "--payload", "x", "--knowledge", "y"]
    assert main(args) == 3
    assert json.loads(capsysbinary.readouterr().out) == {"error": {"code": "read_error"}}


def test_device_name_returns_read_error_exit(capsysbinary):
    assert main(["--context", "NUL", "--payload", "x", "--knowledge", "y"]) == 3
    assert json.loads(capsysbinary.readouterr().out) == {"error": {"code": "read_error"}}
