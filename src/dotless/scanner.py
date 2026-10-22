"""Find locale-dependent case conversions in source files."""

from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import asdict, dataclass
from typing import Callable, Iterable, Iterator

from . import lexer
from .analysis import (
    BOTH,
    LOWER,
    UPPER,
    Verdict,
    enclosing,
    judge_call,
    judge_literals,
    literals_in,
    matching_close,
)
from .lexer import Source
from .rules import RULES, severity_rank

EXTENSIONS = {
    ".c": "c", ".h": "c", ".cc": "c", ".cpp": "c", ".cxx": "c", ".hh": "c", ".hpp": "c",
    ".vala": "vala", ".gs": "vala",
    ".py": "python",
    ".js": "js", ".mjs": "js",
    ".rs": "rust",
}
SYNTAX = {"c": lexer.C, "vala": lexer.VALA, "python": lexer.PYTHON, "js": lexer.JS, "rust": lexer.RUST}

DEFAULT_EXCLUDES = (
    ".git", ".hg", "node_modules", "_build", "build", "builddir", "target",
    "__pycache__", ".venv", "venv", ".flatpak-builder", "subprojects", "po",
)

_SUPPRESS = re.compile(r"dotless:\s*ignore(?P<file>-file)?(?:\[(?P<ids>[A-Z0-9_,\s]+)\])?")


@dataclass
class Finding:
    rule: str
    severity: str
    path: str
    line: int
    column: int
    end_column: int
    language: str
    call: str
    message: str
    reason: str
    fix: str
    snippet: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Match:
    rule: str
    start: int  # start of the reported expression
    end: int  # end of the reported expression
    call: str
    kind: str
    verdict: Verdict | None = None  # pre-decided verdict


Matcher = Callable[[Source], Iterator[Match]]

# ---------------------------------------------------------------- C / C++

_C_DECL_BEFORE = re.compile(r"(?:\b(?:int|extern|static|inline|define|undef|wint_t|char)\s*\**\s*|#\s*(?:define|undef)\s+)$")
_C_CTYPE = re.compile(r"(?<![\w$.>:])(?:std\s*::\s*)?(tolower|toupper|_tolower|_toupper)\s*\(")
_C_WIDE = re.compile(r"(?<![\w$.>:])(?:std\s*::\s*)?(towlower|towupper)\s*\(")
_C_CASECMP = re.compile(r"(?<![\w$.>:])(strcasecmp|strncasecmp|strcasestr|wcscasecmp|wcsncasecmp)\s*\(")
_C_GLIB_DEPR = re.compile(r"(?<![\w$.>:])(g_strdown|g_strup|g_strcasecmp|g_strncasecmp)\s*\(")
_C_GLIB_UTF8 = re.compile(r"(?<![\w$.>:])(g_utf8_strdown|g_utf8_strup)\s*\(")
_C_CALLBACK = re.compile(r"(?<=[(,])\s*(?:\(\s*\w+\s*\)\s*)?(strcasecmp|strncasecmp|g_strcasecmp|wcscasecmp)\s*(?=[,)])")
_LOOKUP_CALLERS = re.compile(r"^(bsearch|lfind|lsearch|g_hash_table_new\w*|g_tree_new\w*|g_\w*find_custom|g_ptr_array_find_with_equal_func|g_\w*_lookup\w*)$")


def _kind_of(name: str) -> str:
    n = name.lower()
    if "casecmp" in n or "casestr" in n:
        return BOTH
    if "low" in n or "down" in n:
        return LOWER
    return UPPER


def _calls(src: Source, pattern: re.Pattern, rule: str, decl_guard: bool = True) -> Iterator[Match]:
    bare = src.bare
    for m in pattern.finditer(bare):
        if decl_guard and _C_DECL_BEFORE.search(bare, max(0, m.start() - 40), m.start()):
            continue
        close = matching_close(bare, m.end() - 1)
        yield Match(rule, m.start(), close, re.sub(r"\s+", "", m.group(0)[:-1]), _kind_of(m.group(1)))


def _casecmp_calls(src: Source, pattern: re.Pattern, rule: str) -> Iterator[Match]:
    """strcasecmp-family: the comparison constant is an argument."""
    for match in _calls(src, pattern, rule):
        open_idx = src.bare.index("(", match.start)
        lits = literals_in(src, open_idx, match.end)
        verdict = judge_literals(lits, BOTH, "compares with") if lits else None
        if verdict is not None and verdict.severity is None:
            continue
        match.verdict = verdict
        yield match


def match_c(src: Source) -> Iterator[Match]:
    yield from _calls(src, _C_CTYPE, "DL001")
    yield from _casecmp_calls(src, _C_CASECMP, "DL002")
    yield from _calls(src, _C_WIDE, "DL003")
    yield from _calls(src, _C_GLIB_UTF8, "DL004")
    for m in _calls(src, _C_GLIB_DEPR, "DL005"):
        if m.kind == BOTH:
            open_idx = src.bare.index("(", m.start)
            lits = literals_in(src, open_idx, m.end)
            m.verdict = judge_literals(lits, BOTH, "compares with") if lits else None
            if m.verdict is not None and m.verdict.severity is None:
                continue
        yield m
    # strcasecmp passed as a callback (bsearch, g_hash_table_new, ...)
    for m in _C_CALLBACK.finditer(src.bare):
        enc = enclosing(src.bare, m.start(1))
        name = enc[1] if enc else ""
        if _LOOKUP_CALLERS.match(name):
            v = Verdict("high", f"used as the comparison function of {name}()")
        else:
            v = Verdict("low", f"passed as a callback to {name or 'a function'}()")
        rule = "DL005" if m.group(1).startswith("g_") else "DL002"
        yield Match(rule, m.start(1), m.end(1), m.group(1), BOTH, v)


# ------------------------------------------------------------------- Vala

_VALA_CASE = re.compile(r"\.\s*(down|up)\s*\(")


def match_vala(src: Source) -> Iterator[Match]:
    bare = src.bare
    for m in _VALA_CASE.finditer(bare):
        close = matching_close(bare, m.end() - 1)
        args = bare[m.end() : close - 1].strip()
        if args and not re.fullmatch(r"[\w.\-+ ]+", args):
            continue
        # Start the expression at the receiver so comparisons in front of
        # it ("x" == s.down ()) are seen.
        rs = m.start()
        recv = re.search(r"([\w.]+|\))\s*$", bare[max(0, rs - 200) : rs])
        start = rs - len(recv.group(0)) if recv and recv.group(1) != ")" else rs
        yield Match("DL006", start, close, m.group(1) + "()", LOWER if m.group(1) == "down" else UPPER)


# ----------------------------------------------------------------- Python

_PY_GLIB = re.compile(r"\bGLib\s*\.\s*(utf8_strdown|utf8_strup)\s*\(")
_PY_RE_LOCALE = re.compile(r"\bre\s*\.\s*(?:L|LOCALE)\b")
_PY_RE_ICASE = re.compile(r"\bre\s*\.\s*(?:I|IGNORECASE)\b")


def match_python(src: Source) -> Iterator[Match]:
    yield from _calls(src, _PY_GLIB, "DL004", decl_guard=False)
    bare = src.bare
    for m in _PY_RE_LOCALE.finditer(bare):
        enc = enclosing(bare, m.start())
        if enc is None:
            continue
        open_idx, name, _ = enc
        close = matching_close(bare, open_idx)
        call_text = bare[open_idx:close]
        lits = literals_in(src, open_idx, close)
        if not (_PY_RE_ICASE.search(call_text) or any(v.startswith("(?i") for v in lits)):
            continue
        pattern = lits[0] if lits else None
        if pattern is None:
            v = Verdict("low", "pattern is not a constant")
        elif re.search(r"[iI]|a-z|A-Z", pattern):
            v = Verdict("high", f"case-insensitive pattern {pattern!r} contains i/I or a letter range")
        else:
            continue
        name_start = bare.rfind(name, 0, open_idx)
        yield Match("DL009", name_start if name_start >= 0 else open_idx, close, f"re.{name}(..., re.LOCALE)", BOTH, v)


# ------------------------------------------------------------- JavaScript

_JS_LOCALE_CASE = re.compile(r"\.\s*(toLocaleLowerCase|toLocaleUpperCase)\s*\(")
_JS_GLIB = re.compile(r"\bGLib\s*\.\s*(utf8_strdown|utf8_strup)\s*\(")
_JS_LOCALE_COMPARE = re.compile(r"\.\s*localeCompare\s*\(")
_JS_NO_LOCALE = re.compile(r"^\s*(?:undefined|null|\[\s*\])?\s*$")


def match_js(src: Source) -> Iterator[Match]:
    bare = src.bare
    for m in _JS_LOCALE_CASE.finditer(bare):
        close = matching_close(bare, m.end() - 1)
        args = bare[m.end() : close - 1]
        if not _JS_NO_LOCALE.match(args):
            lits = literals_in(src, m.end(), close)
            if lits:
                continue  # explicit locale, e.g. 'en-US' or deliberately 'tr'
        start = _receiver_start(bare, m.start())
        yield Match("DL007", start, close, m.group(1) + "()", LOWER if "Lower" in m.group(1) else UPPER)
    yield from _calls(src, _JS_GLIB, "DL004", decl_guard=False)
    for m in _JS_LOCALE_COMPARE.finditer(bare):
        close = matching_close(bare, m.end() - 1)
        args_code = src.code[m.end() : close - 1]
        if not re.search(r"sensitivity\s*:\s*['\"](base|accent)['\"]", args_code):
            continue
        # Explicit locale as second argument?
        lits = literals_in(src, m.end(), close)
        start = _receiver_start(bare, m.start())
        cmp = re.match(r"\s*(===|!==|==|!=|<|>)\s*0\b", bare[close:])
        if lits and re.match(r"['\"]", args_code.split(",")[1].strip() if "," in args_code else ""):
            continue
        receiver_lits = literals_in(src, start, m.start())
        candidates = [v for v in lits if not re.fullmatch(r"base|accent", v)] + receiver_lits
        if cmp and any(_has_i(v) for v in candidates):
            v = Verdict("high", "equality check against a constant containing i/I")
        elif cmp:
            v = Verdict("low", "equality check with sensitivity base/accent")
        else:
            continue  # sorting: locale-aware order is intended
        yield Match("DL008", start, close, "localeCompare()", BOTH, v)


def _has_i(v: str) -> bool:
    return v.isascii() and ("i" in v or "I" in v)


def _receiver_start(bare: str, dot: int) -> int:
    recv = re.search(r"([\w$.]+)\s*$", bare[max(0, dot - 200) : dot])
    return dot - len(recv.group(0)) if recv else dot


# ------------------------------------------------------------------- Rust

_RS_LIBC_CTYPE = re.compile(r"\blibc\s*::\s*(tolower|toupper)\s*\(")
_RS_LIBC_CASECMP = re.compile(r"\blibc\s*::\s*(strcasecmp|strncasecmp)\s*\(")
_RS_GLIB_FFI = re.compile(r"(?<![\w$])(?:(?:glib\s*::\s*)?ffi\s*::\s*|glib_sys\s*::\s*)?(g_utf8_strdown|g_utf8_strup)\s*\(")


def match_rust(src: Source) -> Iterator[Match]:
    yield from _calls(src, _RS_LIBC_CTYPE, "DL001", decl_guard=False)
    yield from _casecmp_calls(src, _RS_LIBC_CASECMP, "DL002")
    for m in _calls(src, _RS_GLIB_FFI, "DL004", decl_guard=False):
        if re.search(r"\bfn\s*$", src.bare[max(0, m.start - 20) : m.start]):
            continue
        yield m


MATCHERS: dict[str, Matcher] = {
    "c": match_c,
    "vala": match_vala,
    "python": match_python,
    "js": match_js,
    "rust": match_rust,
}

# Cheap prefilter: skip lexing files that cannot contain a match.
PREFILTER = {
    "c": re.compile(r"tolower|toupper|towlower|towupper|casecmp|casestr|g_strdown|g_strup|g_utf8_str(?:down|up)"),
    "vala": re.compile(r"\.\s*(?:down|up)\s*\("),
    "python": re.compile(r"utf8_str(?:down|up)|re\s*\.\s*(?:L\b|LOCALE)"),
    "js": re.compile(r"toLocale(?:Lower|Upper)Case|utf8_str(?:down|up)|localeCompare"),
    "rust": re.compile(r"libc\s*::\s*(?:to(?:lower|upper)|str\w*casecmp)|g_utf8_str(?:down|up)"),
}


def language_of(path: str) -> str | None:
    return EXTENSIONS.get(os.path.splitext(path)[1].lower())


def _suppressions(src: Source) -> tuple[bool, dict[int, set[str] | None]]:
    """(whole file ignored, {line: rule ids or None for all rules})."""
    lines: dict[int, set[str] | None] = {}
    for line, text in src.comments:
        for m in _SUPPRESS.finditer(text):
            if m.group("file"):
                return True, {}
            ids = {i.strip() for i in m.group("ids").split(",")} if m.group("ids") else None
            comment_line = line + text[: m.start()].count("\n")
            targets = [comment_line]
            if src.line_text(comment_line).strip().startswith(("//", "/*", "#", "*")):
                targets.append(comment_line + 1)
            for t in targets:
                prev = lines.get(t, set())
                lines[t] = None if ids is None or prev is None else prev | ids
    return False, lines


def scan_text(text: str, path: str, lang: str) -> list[Finding]:
    if not PREFILTER[lang].search(text):
        return []
    src = lexer.lex(text, SYNTAX[lang])
    ignore_file, suppressed = _suppressions(src)
    if ignore_file:
        return []
    findings = []
    seen: set[tuple[str, int]] = set()
    for m in MATCHERS[lang](src):
        verdict = m.verdict or judge_call(src, m.start, m.end, m.kind, lang)
        if verdict.severity is None:
            continue
        line = src.line_of(m.start)
        sup = suppressed.get(line, set())
        if sup is None or m.rule in sup:
            continue
        key = (m.rule, m.start)
        if key in seen:
            continue
        seen.add(key)
        rule = RULES[m.rule]
        col = src.col_of(m.start)
        end_col = col + (m.end - m.start) if src.line_of(m.end) == line else len(src.line_text(line)) + 1
        findings.append(
            Finding(
                rule=m.rule,
                severity=verdict.severity,
                path=path,
                line=line,
                column=col,
                end_column=end_col,
                language=lang,
                call=m.call,
                message=f"{m.call}: {rule.summary}",
                reason=verdict.reason,
                fix=rule.fix,
                snippet=src.line_text(line).strip(),
            )
        )
    findings.sort(key=lambda f: (f.line, f.column))
    return findings


def iter_files(paths: Iterable[str], excludes: Iterable[str] = ()) -> Iterator[tuple[str, str]]:
    excludes = tuple(excludes)

    def excluded(rel: str) -> bool:
        rel = rel.replace(os.sep, "/")
        return any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(os.path.basename(rel), pat) for pat in excludes)

    for root in paths:
        if os.path.isfile(root):
            lang = language_of(root)
            if lang:
                yield root, lang
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(
                d for d in dirnames
                if d not in DEFAULT_EXCLUDES and not excluded(os.path.relpath(os.path.join(dirpath, d), root))
            )
            for f in sorted(filenames):
                full = os.path.join(dirpath, f)
                lang = language_of(f)
                if lang and not excluded(os.path.relpath(full, root)):
                    yield full, lang


def scan_paths(paths: Iterable[str], min_severity: str = "low", excludes: Iterable[str] = ()) -> tuple[list[Finding], int]:
    """Scan files and directories. Returns (findings, number of files scanned)."""
    findings: list[Finding] = []
    count = 0
    floor = severity_rank(min_severity)
    for path, lang in iter_files(paths, excludes):
        count += 1
        try:
            with open(path, "rb") as fh:
                text = fh.read().decode("utf-8", errors="replace")
        except OSError:
            continue
        for f in scan_text(text, path.replace(os.sep, "/"), lang):
            if severity_rank(f.severity) >= floor:
                findings.append(f)
    return findings, count
