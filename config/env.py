"""Tiny `.env` file reader.

Why not a library? This keeps the config layer free of extra dependencies,
so scripts, tests and the engine can load settings without installing
FastAPI or pydantic.

Rules of the format:
    KEY=value          -> simple value
    KEY="value"        -> quotes are removed
    # comment          -> ignored
    empty lines        -> ignored
Variables already set in the real environment always win
(this is what Docker and CI expect).
"""

import os
from pathlib import Path


def parse_env_line(line: str) -> tuple[str, str] | None:
    """Turn one line of a .env file into (key, value), or None if it holds no variable."""
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    value = value.strip()
    # Remove matching surrounding quotes: "abc" or 'abc'
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return key.strip(), value


def load_env_file(path: Path) -> None:
    """Copy the variables of a .env file into os.environ (without overwriting existing ones)."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_env_line(line)
        if parsed is not None:
            key, value = parsed
            os.environ.setdefault(key, value)
