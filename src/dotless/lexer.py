"""A small lexer that separates code from comments and string literals.

It is not a parser. It only needs to answer three questions reliably:
is an offset inside a comment, inside a string literal, or in code; and
what literal text sits at a given offset. To keep offsets stable, every
view has exactly the same length as the source.

``Source.code``  comments blanked, string literals kept
``Source.bare``  comments and literal contents blanked, quote chars kept
``Source.comments``  list of (line, text) for every comment
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field


_PY_PREFIX = re.compile(r"(?:[rR][bBfF]?|[bBfF][rR]?|[uU])(?=['\"])")
_C_PREFIX = re.compile(r"(?:u8|[LuU])(?=['\"])")


@dataclass(frozen=True)
class Syntax:
    line_comments: tuple[str, ...] = ("//",)
    block_comment: tuple[str, str] | None = ("/*", "*/")
    nested_blocks: bool = False
    quotes: tuple[str, ...] = ('"', "'")
    triple_quotes: tuple[str, ...] = ()  # Python ''' and """, Vala """
    string_prefix: re.Pattern | None = None  # b"", L"", u8"" ...
    template_quote: bool = False  # JavaScript `...`
    regex_literals: bool = False  # JavaScript /.../
    rust_chars: bool = False  # 'a' vs lifetime 'a
    rust_raw: bool = False  # r"..." and r#"..."#


C = Syntax(string_prefix=_C_PREFIX)
VALA = Syntax(triple_quotes=('"""',), string_prefix=_C_PREFIX)
PYTHON = Syntax(
    line_comments=("#",),
    block_comment=None,
    triple_quotes=('"""', "'''"),
    string_prefix=_PY_PREFIX,
)
JS = Syntax(template_quote=True, regex_literals=True)
RUST = Syntax(
    quotes=('"',), nested_blocks=True, rust_chars=True, rust_raw=True, string_prefix=re.compile(r'[bc](?=")')
)

# Characters after which a "/" in JavaScript starts a regex, not a division.
_JS_REGEX_PREV = set("(,=:[!&|?{};+-*%<>~^")
_JS_REGEX_KEYWORDS = ("return", "typeof", "case", "do", "else", "in", "of", "void", "yield")
_RUST_CHAR = re.compile(r"'(?:\\u\{[0-9a-fA-F]{1,6}\}|\\x[0-9a-fA-F]{2}|\\.|[^\\'\n])'")
_RUST_RAW = re.compile(r'b?r(#*)"')


@dataclass
class Source:
    text: str
    code: str
    bare: str
    comments: list[tuple[int, str]]
    strings: list[tuple[int, int]]  # [start, end) of each literal incl. quotes
    _line_starts: list[int] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self._line_starts = [0] + [m.end() for m in re.finditer("\n", self.text)]
        self._string_starts = [s for s, _ in self.strings]

    def line_of(self, offset: int) -> int:
        """1-based line number of an offset."""
        return bisect.bisect_right(self._line_starts, offset)

    def col_of(self, offset: int) -> int:
        """1-based column of an offset."""
        return offset - self._line_starts[self.line_of(offset) - 1] + 1

    def line_offset(self, line: int) -> int:
        if line - 1 >= len(self._line_starts):
            return len(self.text)
        return self._line_starts[line - 1]

    def line_text(self, line: int) -> str:
        start = self.line_offset(line)
        end = self.text.find("\n", start)
        return self.text[start : end if end >= 0 else len(self.text)]

    def string_at(self, offset: int) -> tuple[int, int] | None:
        """The literal span that starts exactly at ``offset``, if any."""
        i = bisect.bisect_left(self._string_starts, offset)
        if i < len(self.strings) and self.strings[i][0] == offset:
            return self.strings[i]
        return None

    def in_string(self, offset: int) -> bool:
        i = bisect.bisect_right(self._string_starts, offset) - 1
        return i >= 0 and self.strings[i][0] <= offset < self.strings[i][1]


def _blank(s: str) -> str:
    return "".join("\n" if c == "\n" else " " for c in s)


def lex(text: str, syntax: Syntax) -> Source:
    n = len(text)
    code: list[str] = []
    bare: list[str] = []
    comments: list[tuple[int, str]] = []
    strings: list[tuple[int, int]] = []
    line = 1
    i = 0
    last_sig = ""  # last significant code character, for JS regex detection
    last_word = ""

    def emit_comment(start: int, end: int) -> None:
        nonlocal line
        seg = text[start:end]
        comments.append((line, seg))
        blank = _blank(seg)
        code.append(blank)
        bare.append(blank)
        line += seg.count("\n")

    def emit_string(start: int, end: int, open_len: int, close_len: int) -> None:
        nonlocal line
        seg = text[start:end]
        strings.append((start, end))
        code.append(seg)
        close = len(seg) - close_len
        bare.append(seg[:open_len] + _blank(seg[open_len:close]) + seg[close:])
        line += seg.count("\n")

    def scan_quoted(start: int, quote: str, multiline: bool) -> int:
        j = start + len(quote)
        while j < n:
            c = text[j]
            if c == "\\":
                j += 2
                continue
            if text.startswith(quote, j):
                return j + len(quote)
            if c == "\n" and not multiline:
                return j
            j += 1
        return n

    while i < n:
        c = text[i]

        # Comments.
        lc = next((t for t in syntax.line_comments if text.startswith(t, i)), None)
        if lc is not None:
            end = text.find("\n", i)
            end = n if end < 0 else end
            emit_comment(i, end)
            i = end
            continue
        if syntax.block_comment and text.startswith(syntax.block_comment[0], i):
            op, cl = syntax.block_comment
            depth, j = 1, i + len(op)
            while j < n and depth:
                if syntax.nested_blocks and text.startswith(op, j):
                    depth += 1
                    j += len(op)
                elif text.startswith(cl, j):
                    depth -= 1
                    j += len(cl)
                else:
                    j += 1
            emit_comment(i, j)
            i = j
            continue

        # Rust raw strings and char literals / lifetimes.
        if syntax.rust_raw and c in "rb" and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
            m = _RUST_RAW.match(text, i)
            if m:
                close = '"' + m.group(1)
                end = text.find(close, m.end())
                end = n if end < 0 else end + len(close)
                emit_string(i, end, m.end() - i, len(close))
                i = end
                last_sig = '"'
                continue
        if syntax.rust_chars and c == "'":
            m = _RUST_CHAR.match(text, i)
            if m:
                emit_string(i, m.end(), 1, 1)
                i = m.end()
                last_sig = "'"
                continue
            code.append(c)
            bare.append(c)
            i += 1
            continue

        # Strings.
        start = i
        if syntax.string_prefix and c.isalnum() and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
            m = syntax.string_prefix.match(text, i)
            if m:
                i = m.end()
                c = text[i]
        q = next((t for t in syntax.triple_quotes if text.startswith(t, i)), None)
        if q is not None:
            end = scan_quoted(i, q, True)
            emit_string(start, end, i - start + 3, 3 if text.endswith(q, 0, end) else 0)
            i = end
            last_sig = '"'
            continue
        if c in syntax.quotes or (syntax.template_quote and c == "`"):
            end = scan_quoted(i, c, c == "`")
            emit_string(start, end, i - start + 1, 1 if end > i + 1 and text[end - 1] == c else 0)
            i = end
            last_sig = '"'
            continue
        i = start
        c = text[i]

        # JavaScript regex literals.
        if syntax.regex_literals and c == "/" and (last_sig in _JS_REGEX_PREV or last_sig == "" or last_word in _JS_REGEX_KEYWORDS):
            j, in_class = i + 1, False
            while j < n and text[j] != "\n":
                d = text[j]
                if d == "\\":
                    j += 2
                    continue
                if d == "[":
                    in_class = True
                elif d == "]":
                    in_class = False
                elif d == "/" and not in_class:
                    break
                j += 1
            if j < n and text[j] == "/":
                j += 1
                while j < n and text[j].isalpha():
                    j += 1
                emit_string(i, j, 1, 0)
                i = j
                last_sig = '"'
                continue

        code.append(c)
        bare.append(c)
        if c == "\n":
            line += 1
        elif not c.isspace():
            if c.isalnum() or c == "_" or c == "$":
                j = i
                while j < n and (text[j].isalnum() or text[j] in "_$"):
                    j += 1
                word = text[i:j]
                code.append(word[1:])
                bare.append(word[1:])
                last_word = word
                last_sig = "a"
                i = j
                continue
            last_sig = c
            last_word = ""
        i += 1

    return Source(text, "".join(code), "".join(bare), comments, strings)


def literal_value(raw: str) -> str | None:
    """Best-effort value of a string or char literal (quotes stripped).

    Returns None for literals whose value cannot be known statically
    (template literals with substitutions, Python f-strings, regexes).
    """
    m = re.match(r'^(?:[A-Za-z0-9]{0,2})("""|\'\'\'|"|\'|`)', raw)
    if not m:
        return None
    prefix = raw[: m.start(1)].lower()
    if "f" in prefix:
        return None
    q = m.group(1)
    body = raw[m.end(1) :]
    if body.endswith(q):
        body = body[: -len(q)]
    if q == "`" and "${" in body:
        return None
    return body
