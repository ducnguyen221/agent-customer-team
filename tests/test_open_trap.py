"""The shared no_open trap must catch every way the CLI could open a file."""
import builtins
import io
import os
from pathlib import Path

import pytest

OPENERS = {
    "Path.open": lambda path: Path(path).open("rb"),
    "builtins.open": lambda path: builtins.open(path, "rb"),
    "io.open": lambda path: io.open(path, "rb"),
    "os.open": lambda path: os.open(path, os.O_RDONLY),
}


@pytest.mark.parametrize("name", sorted(OPENERS))
def test_trap_catches_each_opener(name, tmp_path, no_open):
    target = tmp_path / "x.json"
    target.write_text("{}", encoding="utf-8")
    with no_open():
        with pytest.raises(AssertionError, match="attempted open"):
            OPENERS[name](str(target))


@pytest.mark.parametrize("name", sorted(OPENERS))
def test_trap_is_disarmed_outside_the_block(name, tmp_path, no_open):
    target = tmp_path / "x.json"
    target.write_text("{}", encoding="utf-8")
    with no_open():
        pass
    handle = OPENERS[name](str(target))
    if isinstance(handle, int):
        os.close(handle)
    else:
        handle.close()
