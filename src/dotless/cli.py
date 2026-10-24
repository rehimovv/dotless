"""Command line interface.

Exit status: 0 nothing found (or ``--exit-zero``), 1 findings reported,
2 usage or configuration error. ``dotless run`` uses 0 for identical
output, 1 for differences and 2 when it cannot run the comparison.
"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .rules import RULES, SEVERITIES

EXIT_OK, EXIT_FINDINGS, EXIT_ERROR = 0, 1, 2


def _err(msg: str) -> None:
    print(f"dotless: {msg}", file=sys.stderr)


def use_color(mode: str, stream) -> bool:
    """Colour for --color=auto follows NO_COLOR and whether ``stream`` is a terminal."""
    if mode == "always":
        return True
    if mode == "never":
        return False
    return "NO_COLOR" not in os.environ and hasattr(stream, "isatty") and stream.isatty()


def _write(text: str) -> None:
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except BrokenPipeError:
        # The reader went away (e.g. `dotless scan . | head`); stop quietly.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())


def _scan(args: argparse.Namespace) -> int:
    from . import config, formats
    from .scanner import scan_paths

    for p in args.paths:
        if not os.path.exists(p):
            _err(f"{p}: no such file or directory")
            return EXIT_ERROR
    bad = [r for r in args.disable if r not in RULES]
    if bad:
        _err(f"unknown rule id(s): {', '.join(bad)} (see `dotless rules`)")
        return EXIT_ERROR

    cfg = config.Config()
    path = args.config if args.config else (None if args.no_config else config.find_pyproject(os.getcwd()))
    if args.config and not os.path.isfile(args.config):
        _err(f"{args.config}: no such file")
        return EXIT_ERROR
    if path:
        try:
            cfg, warning = config.load(path)
        except (config.ConfigError, OSError) as e:
            _err(str(e))
            return EXIT_ERROR
        if warning:
            _err(f"warning: {warning}")

    min_severity = args.min_severity or cfg.min_severity or "low"
    errors: list[str] = []
    findings, files = scan_paths(
        args.paths,
        min_severity,
        excludes=cfg.exclude + args.exclude,
        disable=cfg.disable + args.disable,
        force_exclude=args.force_exclude,
        errors=errors,
    )
    for e in errors:
        _err(f"warning: cannot read {e}")

    if args.format == "text":
        stream = sys.stdout if args.output is None else None
        out = formats.text(findings, files, color=stream is not None and use_color(args.color, stream))
    else:
        out = formats.FORMATS[args.format](findings, files)
        print(formats.summary(findings, files), file=sys.stderr)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(out)
        except OSError as e:
            _err(f"{args.output}: {e.strerror or e}")
            return EXIT_ERROR
    else:
        _write(out)
    return EXIT_FINDINGS if findings and not args.exit_zero else EXIT_OK


def _rules(args: argparse.Namespace) -> int:
    lines = []
    for r in RULES.values():
        lines.append(f"{r.id}  {r.name}  [{', '.join(r.languages)}]")
        lines.append(f"       {r.summary}")
        lines.append(f"       fix: {r.fix}")
    _write("\n".join(lines) + "\n")
    return EXIT_OK


def _run(args: argparse.Namespace) -> int:
    from .runtime import run_compare

    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        _err("run: missing command (usage: dotless run -- COMMAND [ARGS...])")
        return EXIT_ERROR
    return run_compare(cmd, args.locales.split(","), args.baseline, args.timeout, args.stdin)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dotless",
        description="Find dotted/dotless I bugs caused by locale-dependent case mapping.",
        epilog="Exit status: 0 nothing found, 1 findings reported, 2 error.",
    )
    p.add_argument("--version", action="version", version=f"dotless {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser(
        "scan",
        help="scan source files",
        description="Scan C, Vala, Python, JavaScript and Rust sources. Settings in "
        "[tool.dotless] of the nearest pyproject.toml are used unless --no-config is given.",
    )
    s.add_argument("paths", nargs="+", metavar="PATH")
    s.add_argument("-f", "--format", choices=["text", "json", "sarif", "gitlab"], default="text")
    s.add_argument("--min-severity", choices=SEVERITIES, default=None, help="default: low")
    s.add_argument("-o", "--output", metavar="FILE", help="write the report to FILE")
    s.add_argument("--exclude", action="append", default=[], metavar="GLOB", help="skip matching paths (repeatable)")
    s.add_argument("--force-exclude", action="store_true", help="apply excludes to files named on the command line too")
    s.add_argument("--disable", action="append", default=[], metavar="RULE", help="turn off a rule, e.g. DL005 (repeatable)")
    s.add_argument("--color", choices=["auto", "always", "never"], default="auto", help="colour text output (default: auto)")
    s.add_argument("--config", metavar="FILE", help="read [tool.dotless] from FILE")
    s.add_argument("--no-config", action="store_true", help="ignore pyproject.toml")
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
