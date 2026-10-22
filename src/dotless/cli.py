"""Command line interface."""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .rules import RULES, SEVERITIES


def _scan(args: argparse.Namespace) -> int:
    from . import formats
    from .scanner import scan_paths

    for p in args.paths:
        if not os.path.exists(p):
            print(f"dotless: {p}: no such file or directory", file=sys.stderr)
            return 2
    findings, files = scan_paths(args.paths, args.min_severity, args.exclude)
    if args.format == "text":
        color = args.output is None and sys.stdout.isatty() and "NO_COLOR" not in os.environ
        out = formats.text(findings, files, color=color)
    else:
        out = formats.FORMATS[args.format](findings, files)
        print(formats.summary(findings, files), file=sys.stderr)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(out)
    else:
        sys.stdout.write(out)
    return 1 if findings and not args.exit_zero else 0


def _rules(args: argparse.Namespace) -> int:
    for r in RULES.values():
        print(f"{r.id}  {r.name}  [{', '.join(r.languages)}]")
        print(f"       {r.summary}")
        print(f"       fix: {r.fix}")
    return 0


def _run(args: argparse.Namespace) -> int:
    from .runtime import run_compare

    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("dotless run: missing command (usage: dotless run -- COMMAND [ARGS...])", file=sys.stderr)
        return 2
    return run_compare(cmd, args.locales.split(","), args.baseline, args.timeout, args.stdin)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dotless",
        description="Find dotted/dotless I bugs caused by locale-dependent case mapping.",
    )
    p.add_argument("--version", action="version", version=f"dotless {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="scan source files")
    s.add_argument("paths", nargs="+", metavar="PATH")
    s.add_argument("-f", "--format", choices=["text", "json", "sarif", "gitlab"], default="text")
    s.add_argument("--min-severity", choices=SEVERITIES, default="low")
    s.add_argument("-o", "--output", metavar="FILE", help="write the report to FILE")
    s.add_argument("--exclude", action="append", default=[], metavar="GLOB", help="skip matching paths (repeatable)")
    s.add_argument("--exit-zero", action="store_true", help="exit with 0 even if there are findings")
    s.set_defaults(func=_scan)

    r = sub.add_parser("rules", help="list rules")
    r.set_defaults(func=_rules)

    run = sub.add_parser(
        "run",
        help="run a command under Turkic locales and compare its output",
        usage="dotless run [--locales L1,L2] [--baseline LOCALE] -- COMMAND [ARGS...]",
    )
    run.add_argument("--locales", default="tr_TR.UTF-8,az_AZ.UTF-8")
    run.add_argument("--baseline", default="C.UTF-8")
    run.add_argument("--timeout", type=float, default=60.0)
    run.add_argument("--stdin", metavar="FILE", help="feed FILE to the command's standard input")
    run.add_argument("command", nargs=argparse.REMAINDER)
    run.set_defaults(func=_run)
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    args = build_parser().parse_args(argv)
    return args.func(args)
