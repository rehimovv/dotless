"""``[tool.dotless]`` settings from pyproject.toml.

Reading TOML needs ``tomllib`` (Python 3.11+). On older Pythons a
pyproject.toml that has a ``[tool.dotless]`` table is reported and
ignored; command line options keep working.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from .rules import RULES, SEVERITIES

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

KEYS = {"exclude", "min-severity", "disable"}


class ConfigError(Exception):
    pass


@dataclass
class Config:
    path: str | None = None
    exclude: list[str] = field(default_factory=list)
    min_severity: str | None = None
    disable: list[str] = field(default_factory=list)


def find_pyproject(start: str) -> str | None:
    """The nearest pyproject.toml in ``start`` or one of its parents."""
    d = os.path.abspath(start)
    while True:
        candidate = os.path.join(d, "pyproject.toml")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def load(path: str) -> tuple[Config, str | None]:
    """Read ``[tool.dotless]`` from ``path``.

    Returns (config, warning). Raises ConfigError for invalid settings.
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    if tomllib is None:
        if re.search(rb"^\s*\[tool\.dotless\]", raw, re.M):
            return Config(), (f"{path}: [tool.dotless] ignored, reading it needs Python 3.11 or newer")
        return Config(), None
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
        raise ConfigError(f"{path}: {e}") from None
    table = data.get("tool", {}).get("dotless")
    if table is None:
        return Config(), None
    if not isinstance(table, dict):
        raise ConfigError(f"{path}: [tool.dotless] must be a table")
    unknown = set(table) - KEYS
    if unknown:
        raise ConfigError(f"{path}: unknown key(s) in [tool.dotless]: {', '.join(sorted(unknown))}")

    cfg = Config(path=path)
    exclude = table.get("exclude", [])
    if not (isinstance(exclude, list) and all(isinstance(x, str) for x in exclude)):
        raise ConfigError(f"{path}: 'exclude' must be a list of strings")
    cfg.exclude = exclude

    sev = table.get("min-severity")
    if sev is not None and sev not in SEVERITIES:
        raise ConfigError(f"{path}: 'min-severity' must be one of {', '.join(SEVERITIES)}")
    cfg.min_severity = sev

    disable = table.get("disable", [])
    if not (isinstance(disable, list) and all(isinstance(x, str) for x in disable)):
        raise ConfigError(f"{path}: 'disable' must be a list of rule ids")
    bad = [r for r in disable if r not in RULES]
    if bad:
        raise ConfigError(f"{path}: unknown rule id(s) in 'disable': {', '.join(bad)}")
    cfg.disable = disable
    return cfg, None
