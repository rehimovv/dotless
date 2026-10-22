"""``dotless run``: run a command under Turkic locales and diff its output.

The command runs once under a baseline locale (C.UTF-8) and once per test
locale. Messages are kept untranslated (LANGUAGE=en) so that translation
catalogues do not show up as differences; everything else follows the
test locale, which is what a Turkish or Azerbaijani user gets.
"""

from __future__ import annotations

import difflib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass

TURKIC_LETTERS = set("ıİ")


@dataclass
class Result:
    locale: str
    returncode: int | None
    stdout: str
    stderr: str
    error: str | None = None


def _norm(name: str) -> str:
    return name.lower().replace("utf-8", "utf8").replace("-", "")


def available_locales() -> set[str] | None:
    """Normalised names from ``locale -a``, or None if unknown."""
    if not shutil.which("locale"):
        return None
    try:
        out = subprocess.run(["locale", "-a"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return {_norm(line.strip()) for line in out.splitlines() if line.strip()}


def env_for(locale: str) -> dict[str, str]:
    env = dict(os.environ)
    for k in list(env):
        if k.startswith("LC_"):
            del env[k]
    env["LC_ALL"] = locale
    env["LANG"] = locale
    env["LANGUAGE"] = "en"
    return env


def run_once(cmd: list[str], locale: str, timeout: float, stdin_data: bytes | None) -> Result:
    try:
        p = subprocess.run(cmd, env=env_for(locale), input=stdin_data, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return Result(locale, None, "", "", f"command not found: {cmd[0]}")
    except subprocess.TimeoutExpired:
        return Result(locale, None, "", "", f"timed out after {timeout:g}s")
    dec = lambda b: b.decode("utf-8", errors="replace")  # noqa: E731
    return Result(locale, p.returncode, dec(p.stdout), dec(p.stderr))


def _diff(a: str, b: str, name_a: str, name_b: str, limit: int = 40) -> list[str]:
    lines = list(difflib.unified_diff(a.splitlines(), b.splitlines(), name_a, name_b, lineterm="", n=1))
    if len(lines) > limit:
        lines = lines[:limit] + [f"... ({len(lines) - limit} more diff lines)"]
    return lines


def compare(base: Result, other: Result) -> list[str]:
    """Human-readable differences between two runs (empty if identical)."""
    report = []
    if base.returncode != other.returncode:
        report.append(f"exit status: {base.returncode} under {base.locale}, {other.returncode} under {other.locale}")
    for stream in ("stdout", "stderr"):
        a, b = getattr(base, stream), getattr(other, stream)
        if a != b:
            report.append(f"{stream} differs:")
            report.extend("  " + line for line in _diff(a, b, f"{stream}@{base.locale}", f"{stream}@{other.locale}"))
            new = (set(b) & TURKIC_LETTERS) - set(a)
            if new:
                report.append(f"  note: output under {other.locale} contains {', '.join(sorted(new))}, "
                              f"which the {base.locale} output does not (Turkic case mapping)")
    return report


def run_compare(cmd: list[str], locales: list[str], baseline: str, timeout: float, stdin_path: str | None) -> int:
    stdin_data = None
    if stdin_path:
        with open(stdin_path, "rb") as fh:
            stdin_data = fh.read()

    known = available_locales()
    if known is None:
        print("dotless run: cannot list locales (no `locale` command); results may be meaningless "
              "on systems without glibc locales", file=sys.stderr)
    else:
        missing = [loc for loc in [baseline, *locales] if _norm(loc) not in known]
        for loc in missing:
            lang, _, enc = loc.partition(".")
            print(f"dotless run: locale {loc} is not installed; generate it with: "
                  f"localedef -i {lang} -f {enc or 'UTF-8'} {loc}", file=sys.stderr)
        if baseline in missing:
            return 2
        locales = [loc for loc in locales if loc not in missing]
        if not locales:
            return 2

    base = run_once(cmd, baseline, timeout, stdin_data)
    if base.error:
        print(f"dotless run: {base.error}", file=sys.stderr)
        return 2

    differs = False
    for loc in locales:
        res = run_once(cmd, loc, timeout, stdin_data)
        if res.error:
            print(f"[{loc}] {res.error}")
            differs = True
            continue
        report = compare(base, res)
        if report:
            differs = True
            print(f"[{loc}] output differs from {baseline}:")
            print("\n".join(report))
        else:
            print(f"[{loc}] same output as {baseline}")
    return 1 if differs else 0
