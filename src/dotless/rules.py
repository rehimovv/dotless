"""Rule catalogue.

Every rule here corresponds to a row marked locale-dependent in
docs/research.md. Functions that were measured to be locale independent
(Python str.lower(), JavaScript toLowerCase(), Rust to_lowercase(),
g_ascii_*, g_utf8_casefold(), g_unichar_tolower(), Vala ascii_down() ...)
deliberately have no rule.
"""

from __future__ import annotations

from dataclasses import dataclass

C_LIKE = ("c",)


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    languages: tuple[str, ...]
    summary: str
    fix: str
    help_uri: str = "https://gitlab.com/rehimovv/dotless/-/blob/main/docs/rules.md"


RULES: dict[str, Rule] = {
    r.id: r
    for r in (
        Rule(
            "DL001",
            "c-ctype-case",
            ("c", "rust"),
            "tolower()/toupper() follow LC_CTYPE: in tr_TR.UTF-8 and az_AZ.UTF-8 "
            "glibc leaves 'I' and 'i' unchanged, in tr_TR.ISO-8859-9 it returns "
            "the dotless/dotted variants.",
            "Use g_ascii_tolower()/g_ascii_toupper() for ASCII data "
            "(libc: a locale-independent helper; Rust: u8::to_ascii_lowercase()).",
        ),
        Rule(
            "DL002",
            "c-strcasecmp",
            ("c", "rust"),
            "strcasecmp()-family comparisons follow LC_CTYPE: "
            "strcasecmp(\"INTEGER\", \"integer\") != 0 in tr_TR and az_AZ.",
            "Use g_ascii_strcasecmp()/g_ascii_strncasecmp() for ASCII keywords.",
        ),
        Rule(
            "DL003",
            "c-wide-case",
            C_LIKE,
            "towlower()/towupper() map 'I' to U+0131 and 'i' to U+0130 in Turkic locales.",
            "Use g_unichar_tolower()/g_unichar_toupper() (locale independent), "
            "or g_ascii_tolower() for ASCII data.",
        ),
        Rule(
            "DL004",
            "glib-utf8-case",
            ("c", "python", "js", "rust"),
            "g_utf8_strdown()/g_utf8_strup() use Turkic rules when LC_CTYPE is "
            "tr_* or az_*: \"INTEGER\" becomes \"ınteger\".",
            "Use g_ascii_strdown()/g_ascii_strup() for identifiers, or "
            "g_utf8_casefold() to compare human-readable text.",
        ),
        Rule(
            "DL005",
            "glib-deprecated-case",
            C_LIKE,
            "Deprecated g_strdown()/g_strup()/g_strcasecmp()/g_strncasecmp() "
            "use the C library's locale-dependent tolower()/toupper().",
            "Use g_ascii_strdown()/g_ascii_strup()/g_ascii_strcasecmp().",
        ),
        Rule(
            "DL006",
            "vala-string-case",
            ("vala",),
            "Vala string.down()/string.up() call g_utf8_strdown()/g_utf8_strup() "
            "and follow the Turkic rules.",
            "Use string.ascii_down()/string.ascii_up() for identifiers, or "
            "string.casefold() to compare human-readable text.",
        ),
        Rule(
            "DL007",
            "gjs-locale-case",
            ("js",),
            "Under gjs, toLocaleLowerCase()/toLocaleUpperCase() without an explicit "
            "locale use the process locale: 'INTEGER' becomes 'ınteger' in "
            "tr_TR/az_AZ.",
            "Use toLowerCase()/toUpperCase() (locale independent), or pass an "
            "explicit locale.",
        ),
        Rule(
            "DL008",
            "js-localecompare-base",
            ("js",),
            "localeCompare() with sensitivity 'base' or 'accent' treats 'I' and 'i' "
            "as different letters in Turkic locales.",
            "Compare a.toLowerCase() === b.toLowerCase(), or pass an explicit "
            "locale to localeCompare().",
        ),
        Rule(
            "DL009",
            "python-re-locale",
            ("python",),
            "re.LOCALE together with re.IGNORECASE uses the C library's tolower(): "
            "b'INTEGER' does not match b'integer' in tr_TR/az_AZ.",
            "Drop re.LOCALE (decode to str and use re.IGNORECASE), or use "
            "explicit character classes.",
        ),
    )
}

SEVERITIES = ("low", "high")


def severity_rank(severity: str) -> int:
    return SEVERITIES.index(severity)
