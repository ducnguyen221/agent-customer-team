"""Shared fixtures."""
import builtins
import contextlib
import io
import os
from pathlib import Path

import pytest


@pytest.fixture
def no_open(monkeypatch):
    """Return a context manager that makes every way of opening a file raise AssertionError.

    The traps are armed only inside the ``with`` block so that pytest, capture and the
    temporary directory machinery keep working around the call under test.
    """
    def trapped(*args, **kwargs):
        raise AssertionError("attempted open")

    @contextlib.contextmanager
    def armed():
        with monkeypatch.context() as scope:
            scope.setattr(Path, "open", trapped)
            scope.setattr(builtins, "open", trapped)
            scope.setattr(io, "open", trapped)
            scope.setattr(os, "open", trapped)
            yield

    return armed
