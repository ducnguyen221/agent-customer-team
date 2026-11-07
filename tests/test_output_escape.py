"""Stdout carries no raw control, format, separator, surrogate or unassigned characters."""
import hashlib
import json

import pytest
from agent_customer_team import cli
from agent_customer_team.cli import _emit, _escape_unsafe, main
from case_helpers import CTX, D, P, doc

SC1 = ["\u0085", "\u009b", "​", "‍", "‮", "⁦", " ", " ", "﻿", "\x1b", "\x7f",
       "\U000e0001", "͸"]  # last two: Cf outside BMP, Cn inside BMP


def raw_bytes(ch):
    return ch.encode("utf-8")


@pytest.mark.parametrize("ch", SC1)
def test_escape_unsafe_replaces_character(ch):
    out = _escape_unsafe("a" + ch + "b")
    assert ch not in out and out.isascii()
    assert json.loads('"' + out + '"') == "a" + ch + "b"


def test_non_bmp_becomes_surrogate_pair():
    assert _escape_unsafe("\U000e0001") == r"\udb40\udc01"


def test_lone_surrogate_is_escaped_not_encoded():
    assert _escape_unsafe("\ud800") == r"\ud800"


def test_ordinary_text_is_untouched():
    text = "Khởi động lại ứng dụng. \U0001f600 ok"
    assert _escape_unsafe(text) == text


@pytest.mark.parametrize("ch", SC1)
def test_emit_success_has_no_raw_bytes(ch, capsysbinary):
    value = {"draft": "x" + ch + "y", "n": 1}
    _emit(value)
    out = capsysbinary.readouterr().out
    assert raw_bytes(ch) not in out and out.endswith(b"\n")
    assert json.loads(out) == value


@pytest.mark.parametrize("ch", SC1)
def test_emit_error_branch_has_no_raw_bytes(ch, capsysbinary):
    value = {"error": {"code": "invalid_input" + ch}}
    _emit(value)
    out = capsysbinary.readouterr().out
    assert raw_bytes(ch) not in out
    assert json.loads(out) == value


def test_run_case_draft_through_cli_with_all_characters(tmp_path, capsysbinary):
    answer = "A" + "".join(SC1) + "Z"
    document = doc(answer=answer)
    files = {}
    for name, value in (("context", CTX), ("payload", P), ("knowledge", {"documents": [document]})):
        files[name] = tmp_path / (name + ".json")
        files[name].write_text(json.dumps(value), encoding="utf-8")
    code = main(["--context", str(files["context"]), "--payload", str(files["payload"]), "--knowledge", str(files["knowledge"])])
    out = capsysbinary.readouterr().out
    assert code == 0
    for ch in SC1:
        assert raw_bytes(ch) not in out
    result = json.loads(out)
    assert result["draft"] == answer
    assert result["evidence"][0]["sha256"] == hashlib.sha256(answer.encode("utf-8")).hexdigest()


def test_main_invalid_input_goes_through_emit(monkeypatch, capsysbinary):
    seen = []
    monkeypatch.setattr(cli, "_emit", lambda value: seen.append(value))
    assert main(["--bad"]) == 2
    assert seen == [{"error": {"code": "invalid_input"}}]
