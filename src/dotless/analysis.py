"""Decide how serious a locale-dependent case conversion is.

Only one character pair behaves differently in Turkic locales: I/i.
That makes equality checks against ASCII constants decidable:

* lowering, then comparing with a constant that contains 'i'  -> broken
* lowering, then comparing with a constant without any 'i'    -> unaffected
* upper-casing works the same way with 'I'

A site is reported as ``high`` when its result is compared with an
affected ASCII constant or is used as a lookup key (hash table, key file,
dictionary, MIME type, file extension ...). A site whose only uses are
comparisons with unaffected constants is not reported at all. Everything
else is ``low``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .lexer import Source, literal_value

LOWER, UPPER, BOTH = "lower", "upper", "both"

_CMP_OP = re.compile(r"\s*(===|!==|==|!=)\s*(?:(?:Ok|Some)\s*\(\s*)?")
_CMP_OP_BEFORE = re.compile(r"(===|!==|==|!=)\s*$")
_PY_IN = re.compile(r"\s*(?:not\s+)?in\s*([(\[{])")
_METHOD_AFTER = re.compile(r"\s*\.\s*(\w+)\s*\(")
_IDENT_BEFORE = re.compile(r"([A-Za-z_$][\w$]*(?:\s*(?:\.|->|::)\s*[A-Za-z_$][\w$]*)*)\s*$")
_ASSIGN_BEFORE = re.compile(
    r"([A-Za-z_$][\w$]*)\s*(?:\[[^\]]*\]\s*)?=\s*(?:\(\s*(?:const\s+)?\w+\s*\**\s*\)\s*)?$"
)
_CASE_LABEL = re.compile(r"\bcase\s+")

COMPARE_FUNCS = {
    "strcmp", "strncmp", "g_strcmp0", "g_str_equal", "g_str_has_prefix",
    "g_str_has_suffix", "strstr", "g_strrstr", "strcasecmp", "strncasecmp",
    "g_ascii_strcasecmp", "g_ascii_strncasecmp", "g_strv_contains", "memcmp",
    "streq", "g_strcasecmp", "g_strncasecmp", "strcasestr", "g_regex_match_simple",
    "g_pattern_match_simple",
}
COMPARE_METHODS = {
    "has_prefix", "has_suffix", "contains", "startsWith", "endsWith",
    "includes", "indexOf", "startswith", "endswith", "find", "index",
    "equals", "equal", "match", "test", "search", "replace", "split",
}
KEY_FUNC_PREFIXES = (
    "g_hash_table_", "g_tree_", "g_key_file_", "g_settings_", "g_quark_",
    "g_intern_", "g_datalist_", "g_dataset_", "g_content_type_", "g_mime_",
    "g_variant_lookup", "g_variant_dict_", "g_object_get_data", "g_object_set_data",
    "g_file_info_get_attribute", "g_file_info_set_attribute", "bsearch",
    "g_app_info_get_default_for_type", "g_application_get_", "g_type_from_name",
    "g_enum_get_value_by_", "g_flags_get_value_by_",
)
KEY_METHODS = {
    "lookup", "lookup_extended", "get", "has", "has_key", "set", "insert",
    "replace", "contains_key", "get_string", "get_boolean", "get_int",
    "get_value", "get_data", "set_data", "setdefault", "pop",
}
# Calls and methods that pass a string through without changing its case.
TRANSPARENT_FUNCS = {
    "from_ptr", "from", "String", "str", "CStr", "Some", "Ok", "g_strstrip",
    "g_strchomp", "g_strchug", "strip", "trim",
}
TRANSPARENT_METHODS = {
    "to_str", "to_bytes", "to_string_lossy", "to_string", "to_owned", "unwrap",
    "as_str", "as_ref", "strip", "trim", "toString", "get_string",
}
IGNORED_USES = {"g_free", "free", "g_clear_pointer", "g_strfreev", "g_steal_pointer", "g_strdup", "strlen"}
KEYISH_WORDS = {
    "ext", "exts", "extension", "extensions", "suffix", "mime", "mimetype",
    "scheme", "protocol", "proto", "keyword", "keywords", "charset",
    "encoding", "codeset", "header", "hash", "key", "keys", "verb",
}


@dataclass
class Verdict:
    severity: str | None  # "high", "low" or None (provably unaffected)
    reason: str


def _affected(value: str, kind: str) -> bool:
    if not value.isascii():
        return False
    if kind == LOWER:
        return "i" in value
    if kind == UPPER:
        return "I" in value
    return "i" in value or "I" in value


def _ident_words(name: str) -> set[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()
    return {w for w in re.split(r"[_\W]+", spaced) if w}


def is_keyish(name: str) -> bool:
    words = _ident_words(name)
    if words & KEYISH_WORDS:
        return True
    return "content_type" in "_".join(words) or "mime_type" in "_".join(words)


def matching_close(bare: str, open_idx: int) -> int:
    """Index just past the bracket matching ``bare[open_idx]``."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = [pairs[bare[open_idx]]]
    i = open_idx + 1
    n = len(bare)
    while i < n and stack:
        c = bare[i]
        if c in pairs:
            stack.append(pairs[c])
        elif c in ")]}":
            if c == stack[-1]:
                stack.pop()
            else:  # unbalanced (macro magic); give up gracefully
                return i + 1
        i += 1
    return i


def enclosing(bare: str, pos: int, limit: int = 2000) -> tuple[int, str, int] | None:
    """Innermost unclosed ( or [ before ``pos`` and the name in front of it.

    Returns (offset of the bracket, name, offset where the possibly
    qualified name starts). ``name`` is "[" for subscripts. Stops at
    statement boundaries.
    """
    depth = 0
    i = pos - 1
    stop = max(0, pos - limit)
    while i >= stop:
        c = bare[i]
        if c in ")]":
            depth += 1
        elif c in "([":
            if depth == 0:
                if c == "[":
                    return i, "[", i
                m = _IDENT_BEFORE.search(bare, max(0, i - 200), i)
                if not m:
                    return i, "", i
                return i, re.split(r"\s*(?:\.|->|::)\s*", m.group(1))[-1], m.start(1)
            depth -= 1
        elif c in ";{}" and depth == 0:
            return None
        i -= 1
    return None


def literals_in(src: Source, start: int, end: int) -> list[str]:
    out = []
    for s, e in src.strings:
        if s >= end:
            break
        if s >= start:
            v = literal_value(src.text[s:e])
            if v is not None:
                out.append(v)
    return out


def judge_literals(values: list[str], kind: str, what: str) -> Verdict | None:
    if not values:
        return None
    hit = next((v for v in values if _affected(v, kind)), None)
    if hit is not None:
        return Verdict("high", f"{what} {_show(hit)}")
    return Verdict(None, f"{what} only constants without i/I")


def _show(v: str) -> str:
    v = v if len(v) <= 40 else v[:37] + "..."
    return '"' + v.replace("\n", "\\n") + '"'


def _literal_ending_at(src: Source, end: int) -> str | None:
    for s, e in reversed(src.strings):
        if e == end:
            return literal_value(src.text[s:e])
        if e < end:
            return None
    return None


def judge_expression(src: Source, start: int, end: int, kind: str, lang: str, depth: int = 0) -> Verdict | None:
    """Look at how the value of ``text[start:end]`` is used.

    Returns a Verdict when the use is decidable, None otherwise.
    """
    bare = src.bare

    # Skip case-preserving method chains: expr.to_str().unwrap() == "lit"
    while True:
        m = _METHOD_AFTER.match(bare, end)
        if not m or m.group(1) not in TRANSPARENT_METHODS:
            break
        end = matching_close(bare, m.end() - 1)

    # expr == "lit"
    m = _CMP_OP.match(bare, end)
    if m:
        span = src.string_at(m.end())
        if span:
            v = literal_value(src.text[span[0] : span[1]])
            if v is not None:
                return judge_literals([v], kind, "compared with")
    # "lit" == expr
    m = _CMP_OP_BEFORE.search(bare, max(0, start - 50), start)
    if m:
        k = m.start()
        while k > 0 and bare[k - 1].isspace():
            k -= 1
        v = _literal_ending_at(src, k)
        if v is not None:
            return judge_literals([v], kind, "compared with")

    # expr in ("a", "b")
    if lang == "python":
        m = _PY_IN.match(bare, end)
        if m:
            close = matching_close(bare, m.end() - 1)
            return judge_literals(literals_in(src, m.end(), close), kind, "checked for membership in")

    # expr.endsWith(".ini") / expr.has_suffix (".ini")
    m = _METHOD_AFTER.match(bare, end)
    if m:
        close = matching_close(bare, m.end() - 1)
        if m.group(1) in COMPARE_METHODS:
            v = judge_literals(literals_in(src, m.end(), close), kind, f"passed to .{m.group(1)}() with")
            if v:
                return v

    enc = enclosing(bare, start)
    if enc is None:
        return None
    open_idx, name, name_start = enc
    if name == "[":
        return Verdict("high", "used as a subscript key")
    if name == "switch":
        close = matching_close(bare, open_idx)
        brace = bare.find("{", close)
        if brace >= 0 and not bare[close:brace].strip():
            body_end = matching_close(bare, brace)
            labels = []
            for cm in _CASE_LABEL.finditer(bare, brace, body_end):
                span = src.string_at(cm.end())
                if span:
                    v = literal_value(src.text[span[0] : span[1]])
                    if v is not None:
                        labels.append(v)
            return judge_literals(labels, kind, "switch case")
        return None
    close = matching_close(bare, open_idx)
    if name in TRANSPARENT_FUNCS and depth < 3:
        return judge_expression(src, name_start, close, kind, lang, depth + 1)
    if name in COMPARE_FUNCS or name in COMPARE_METHODS:
        return judge_literals(literals_in(src, open_idx, close), kind, f"passed to {name}() with")
    if name.startswith(KEY_FUNC_PREFIXES) or name in KEY_METHODS:
        return Verdict("high", f"used as a lookup key in {name}()")
    if name in IGNORED_USES:
        return Verdict(None, f"only passed to {name}()")
    return None


def judge_call(src: Source, start: int, end: int, kind: str, lang: str) -> Verdict:
    """Severity for a locale-dependent call spanning text[start:end]."""
    direct = judge_expression(src, start, end, kind, lang)
    if direct is not None:
        return direct

    # Result stored in a variable: follow it for a while.
    bare = src.bare
    line_start = bare.rfind("\n", 0, start) + 1
    m = _ASSIGN_BEFORE.search(bare, line_start, start)
    if m:
        var = m.group(1)
        if is_keyish(var):
            return Verdict("high", f"stored in `{var}` (looks like a key, extension, MIME type or protocol name)")
        return _follow_variable(src, var, end, kind, lang)
    return Verdict("low", "result not compared with a constant nearby")


def _follow_variable(src: Source, var: str, from_off: int, kind: str, lang: str) -> Verdict:
    bare = src.bare
    end_line = src.line_of(from_off) + 60
    limit = src.line_offset(end_line)
    use = re.compile(r"(?<![\w$.>])" + re.escape(var) + r"(?![\w$])")
    verdicts: list[Verdict] = []
    undecided = False
    for m in use.finditer(bare, from_off, limit):
        if re.match(r"\s*=(?!=)", bare[m.end() : m.end() + 3]):
            break  # reassigned
        v = judge_expression(src, m.start(), m.end(), kind, lang)
        if v is None:
            undecided = True
            continue
        if v.severity == "high":
            return Verdict("high", f"stored in `{var}`, which is {v.reason} (line {src.line_of(m.start())})")
        verdicts.append(v)
    if verdicts and not undecided:
        return Verdict(None, f"`{var}` is {verdicts[0].reason}")
    return Verdict("low", f"stored in `{var}`; no comparison with an affected constant found")
