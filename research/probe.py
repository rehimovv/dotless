"""Locale probe for Python 3 string APIs (and GLib through PyGObject).

Usage: LC_ALL=LOCALE python3 probe.py LOCALE
Python 3 calls setlocale(LC_CTYPE, "") at start-up; the probe additionally
calls setlocale(LC_ALL, LOCALE) the way a GTK application would.
"""

import locale
import re
import sys

loc = sys.argv[1]


def emit(api, result):
    esc = str(result).encode("unicode_escape").decode("ascii")
    print(f"python\t{api}\t{loc}\t{esc}")


try:
    locale.setlocale(locale.LC_ALL, loc)
except locale.Error:
    emit("setlocale", "FAILED")
    sys.exit(1)

upper, lower = "INTEGER", "integer"
emit("str.lower()", upper.lower())
emit("str.upper()", lower.upper())
emit("str.casefold()", upper.casefold())
emit("bytes.lower()", upper.encode().lower().decode())
emit("bytes.upper()", lower.encode().upper().decode())
emit("re.IGNORECASE (str)", "match" if re.fullmatch(lower, upper, re.I) else "NO match")
emit(
    "re.IGNORECASE|re.LOCALE (bytes)",
    "match" if re.fullmatch(lower.encode(), upper.encode(), re.I | re.L) else "NO match",
)
emit("locale.strxfrm order I<i", locale.strxfrm("I") < locale.strxfrm("i"))

try:
    import gi

    gi.require_version("GLib", "2.0")
    from gi.repository import GLib

    emit("GLib.utf8_strdown() via gi", GLib.utf8_strdown(upper, -1))
    emit("GLib.utf8_strup() via gi", GLib.utf8_strup(lower, -1))
    emit("GLib.ascii_strdown() via gi", GLib.ascii_strdown(upper, -1))
except (ImportError, ValueError) as e:
    emit("GLib via gi", f"unavailable ({e})")
