"""Offline CLI with bounded input and non-echoing errors."""
import json
import sys
from pathlib import Path
from .workflow import run_case


def _unique(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError("invalid constant")


class _JsonInteger:
    """Preserve a JSON numeric type without converting unbounded digits."""

    def __init__(self, token: str) -> None:
        self.length = len(token)


def _load(path: str) -> object:
    if path.replace("\\", "/").startswith("//") or "\x00" in path:
        raise OSError("invalid local path")
    with Path(path).open("rb") as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError("file too large")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant, parse_int=_JsonInteger)


def _emit(value: dict) -> None:
    encoded = (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    sys.stdout.buffer.write(encoded)


def main(argv: list[str] | None = None) -> int:
    """Return contract exit code and emit only the allowlisted result."""
    args = sys.argv[1:] if argv is None else argv
    try:
        if len(args) != 6 or len(set(args[::2])) != 3 or set(args[::2]) != {"--context", "--payload", "--knowledge"}:
            raise ValueError("invalid flags")
        paths = dict(zip(args[::2], args[1::2]))
        context = _load(paths["--context"])
        payload = _load(paths["--payload"])
        corpus = _load(paths["--knowledge"])
        result = run_case(context, payload, corpus)
    except OSError:
        _emit({"error": {"code": "read_error"}})
        return 3
    except (ValueError, UnicodeError, RecursionError):
        _emit({"error": {"code": "invalid_input"}})
        return 2
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
