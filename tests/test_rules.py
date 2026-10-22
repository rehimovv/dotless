"""Fixture-driven rule tests.

Every line in a ``bad.*`` fixture that must be reported carries a marker
``EXPECT <rule> <severity>``. ``safe.*`` fixtures must produce no finding.
"""

import pathlib
import re

import pytest

from dotless.rules import RULES
from dotless.scanner import language_of, scan_text

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
BAD = sorted(FIXTURES.glob("*/bad.*"))
SAFE = sorted(FIXTURES.glob("*/safe.*"))
MARKER = re.compile(r"EXPECT (DL\d{3}) (high|low)")


def scan(path):
    return scan_text(path.read_text(encoding="utf-8"), str(path), language_of(str(path)))


def expected(path):
    out = set()
    for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for m in MARKER.finditer(line):
            out.add((no, m.group(1), m.group(2)))
    return out


@pytest.mark.parametrize("path", BAD, ids=lambda p: p.parent.name)
def test_bad_fixture(path):
    got = {(f.line, f.rule, f.severity) for f in scan(path)}
    assert got == expected(path)


@pytest.mark.parametrize("path", SAFE, ids=lambda p: p.parent.name)
def test_safe_fixture(path):
    assert [(f.line, f.rule, f.call) for f in scan(path)] == []


def test_every_rule_has_positive_case():
    covered = {rule for path in BAD for _, rule, _ in expected(path)}
    assert covered == set(RULES)


def test_every_rule_language_has_negative_case():
    langs = {language_of(str(p)) for p in SAFE}
    for rule in RULES.values():
        assert set(rule.languages) <= langs, rule.id


@pytest.mark.parametrize(
    "lang,code",
    [
        ("c", 'x = strcasecmp (a, "ini") == 0;'),
        ("vala", 'x = s.down () == "integer";'),
        ("python", 'x = GLib.utf8_strdown(s, -1) == "ini"'),
        ("js", "x = s.toLocaleLowerCase() === 'ini';"),
        ("rust", 'libc::strcasecmp(a, b"ini\\0".as_ptr()) == 0'),
    ],
)
def test_minimal_positive_per_language(lang, code):
    assert [f.severity for f in scan_text(code, "t", lang)] == ["high"]


def test_ignore_file():
    code = '/* dotless: ignore-file */\nx = strcasecmp (a, "ini");\n'
    assert scan_text(code, "t.c", "c") == []


def test_ignore_other_rule_does_not_suppress():
    code = 'x = strcasecmp (a, "ini"); /* dotless: ignore[DL001] */\n'
    assert [f.rule for f in scan_text(code, "t.c", "c")] == ["DL002"]


def test_ignore_previous_line_only_affects_next_line():
    code = '// dotless: ignore\nx = strcasecmp (a, "ini");\ny = strcasecmp (b, "ini");\n'
    assert [f.line for f in scan_text(code, "t.c", "c")] == [3]


def test_upper_needs_capital_i():
    # toupper() can only break comparisons with a constant containing 'I'.
    assert scan_text("x = toupper (c) == 'i';", "t.c", "c") == []
    assert [f.severity for f in scan_text("x = toupper (c) == 'I';", "t.c", "c")] == ["high"]


def test_variable_reassignment_stops_tracking():
    code = (
        "char *s = g_utf8_strdown (a, -1);\n"
        "s = g_strdup (b);\n"
        'if (g_str_equal (s, "ini")) {}\n'
    )
    assert [f.severity for f in scan_text(code, "t.c", "c")] == ["low"]
