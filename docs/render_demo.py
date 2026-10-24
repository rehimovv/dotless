"""Render a real terminal session as an SVG for the README.

Usage: python docs/render_demo.py OUTPUT.svg WORKDIR -- COMMAND [ARGS...]

Runs COMMAND in WORKDIR, keeps its ANSI colours and draws the prompt, the
command line and the output into a terminal-like SVG. Long lines wrap the
way a terminal of COLUMNS columns would wrap them.
"""

import html
import re
import subprocess
import sys

COLUMNS = 120
CHAR_W, LINE_H, PAD = 7.9, 19, 18
FG, BG = "#d8dee9", "#1d2128"
COLORS = {"31": "#ff6b6b", "33": "#e5c07b", "32": "#98c379", "36": "#61afef"}
ANSI = re.compile(r"\x1b\[([0-9;]*)m")
BOLD = ' font-weight="bold"'


def spans(line):
    """Split a line with ANSI codes into (text, colour, bold) pieces."""
    out, color, bold, pos = [], FG, False, 0
    for m in ANSI.finditer(line):
        if m.start() > pos:
            out.append((line[pos : m.start()], color, bold))
        for code in (m.group(1) or "0").split(";"):
            if code == "0":
                color, bold = FG, False
            elif code == "1":
                bold = True
            elif code in COLORS:
                color = COLORS[code]
        pos = m.end()
    if pos < len(line):
        out.append((line[pos:], color, bold))
    return out


def wrap(pieces):
    """Wrap a list of pieces into rows of at most COLUMNS characters."""
    rows, row, width = [], [], 0
    for text, color, bold in pieces:
        while text:
            room = COLUMNS - width
            if room == 0:
                rows.append(row)
                row, width = [], 0
                continue
            row.append((text[:room], color, bold))
            width += len(text[:room])
            text = text[room:]
    rows.append(row)
    return rows


def main():
    out_path, workdir = sys.argv[1], sys.argv[2]
    cmd = sys.argv[sys.argv.index("--") + 1 :]
    res = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, encoding="utf-8")
    shown = "dotless " + " ".join(cmd[cmd.index("scan") :]) if "scan" in cmd else " ".join(cmd)
    lines = [[("$ ", COLORS["32"], True), (shown, FG, True)]]
    lines += [spans(line) for line in res.stdout.rstrip("\n").split("\n")]
    rows = [r for line in lines for r in wrap(line)]

    width = int(COLUMNS * CHAR_W + 2 * PAD)
    height = int(len(rows) * LINE_H + 2 * PAD + 26)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" rx="8" fill="{BG}"/>',
        '<circle cx="20" cy="18" r="6" fill="#ff5f57"/><circle cx="40" cy="18" r="6" fill="#febc2e"/>'
        '<circle cx="60" cy="18" r="6" fill="#28c840"/>',
        '<g font-family="DejaVu Sans Mono, Menlo, Consolas, monospace" font-size="14" xml:space="preserve">',
    ]
    for i, row in enumerate(rows):
        y = PAD + 26 + i * LINE_H + 12
        tspans = "".join(
            f'<tspan fill="{c}"{BOLD if b else ""}>{html.escape(t)}</tspan>' for t, c, b in row
        )
        parts.append(f'<text x="{PAD}" y="{y}" style="white-space:pre">{tspans}</text>')
    parts += ["</g>", "</svg>"]
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(parts) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
