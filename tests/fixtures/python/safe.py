# Nothing in this file may be reported.
import re

from gi.repository import GLib

KEYWORD = re.compile(r"^(if|int|while)$", re.IGNORECASE)
NUMBER = re.compile(rb"[0-9]+", re.I | re.L)
PLAIN = re.compile(rb"integer", re.L)


def is_integer(name):
    return name.lower() == "integer" or name.casefold() == "integer"


def is_png(name):
    return GLib.utf8_strdown(name, -1) == "png"


def ascii(name):
    return GLib.ascii_strdown(name, -1) == "integer"


DOC = """GLib.utf8_strdown(name, -1) == "integer" inside a string"""
# GLib.utf8_strdown(name, -1) == "integer" inside a comment


def suppressed(name):
    return GLib.utf8_strdown(name, -1) == "ini"  # dotless: ignore
