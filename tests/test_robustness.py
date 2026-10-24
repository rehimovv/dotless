"""Pathological input must neither crash nor take quadratic time."""

import time

import pytest

from dotless.scanner import PREFILTER, scan_text

LANGS = sorted(PREFILTER)


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize(
    "text",
    [
        '"' + "a" * 100_000,
        "/*" + "tolower (" * 1000,
        "(" * 20_000 + 'strcasecmp (a, "i")',
        ")" * 1000 + "tolower (c) == 'i' }]",
        bytes(range(256)).decode("latin-1") * 200 + "tolower(c)",
        "r#\"" + "'" * 1000 + "`${" * 500,
    ],
    ids=["unterminated-string", "unterminated-comment", "deep-nesting", "stray-closers", "binary", "mixed-quotes"],
)
def test_no_crash(lang, text):
    scan_text(text, "f", lang)


def test_many_unclosed_calls_on_one_line_is_linear():
    # Used to take seconds: every unclosed call scanned to the end of the file.
    text = "tolower (" * 20_000
    start = time.perf_counter()
    scan_text(text, "f.c", "c")
    assert time.perf_counter() - start < 10


def test_long_line_with_assignments_is_linear():
    start = time.perf_counter()
    findings = scan_text("v = tolower (c); " * 5000, "f.c", "c")
    assert len(findings) == 5000
    assert time.perf_counter() - start < 10
