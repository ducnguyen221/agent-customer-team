"""Offline CLI with bounded input and non-echoing errors."""
import json
import sys
import unicodedata
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


_DEVICES = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$", "CLOCK$"}
_DEVICES |= {"COM%d" % n for n in range(1, 10)} | {"LPT%d" % n for n in range(1, 10)}
_DEVICES |= {name + digit for name in ("COM", "LPT") for digit in map(chr, (0xB9, 0xB2, 0xB3))}


def _unsafe_path(path: str) -> bool:
    """Lexical refusal of UNC, device and NT object paths and Windows device names."""
    normal = path.replace("\\", "/")
    if "\x00" in path or normal.startswith(("//", "/??/")):
        return True
    return any(segment.split(".")[0].rstrip(" ").upper() in _DEVICES
               for part in normal.split("/") for segment in part.split(":"))


def _load(path: str) -> object:
    if _unsafe_path(path):
        raise OSError("invalid local path")
    with Path(path).open("rb") as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError("file too large")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant, parse_int=_JsonInteger)


_UNSAFE = {"Cc", "Cf", "Zl", "Zp", "Cs", "Cn"}


def _escape_unsafe(text: str) -> str:
    """Replace control, format, separator, surrogate and unassigned characters with JSON escapes."""
    out = []
    for char in text:
        code = ord(char)
        if unicodedata.category(char) not in _UNSAFE:
            out.append(char)
        elif code > 0xFFFF:
            code -= 0x10000
            out.append("\\u%04x\\u%04x" % (0xD800 + (code >> 10), 0xDC00 + (code & 0x3FF)))
        else:
            out.append("\\u%04x" % code)
    return "".join(out)


def _emit(value: dict) -> None:
    dumped = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    encoded = (_escape_unsafe(dumped) + "\n").encode("utf-8")
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
