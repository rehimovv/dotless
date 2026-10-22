# Locale-dependent case mapping. Each flagged line has an EXPECT marker.
import re

from gi.repository import GLib

KEYWORD = re.compile(rb"^(if|int|while)$", re.IGNORECASE | re.LOCALE)  # EXPECT DL009 high
WORD = re.compile(rb"[a-z]+", re.I | re.L)  # EXPECT DL009 high


def is_ini(name):
    ext = GLib.utf8_strdown(name, -1)  # EXPECT DL004 high
    return ext == "ini"


def lookup(table, name):
    return table[GLib.utf8_strup(name, -1)]  # EXPECT DL004 high


def display(name):
    return GLib.utf8_strup(name, -1)  # EXPECT DL004 low


def is_image(name):
    low = GLib.utf8_strdown(name, -1)  # EXPECT DL004 high
    return low in ("gif", "tiff")
