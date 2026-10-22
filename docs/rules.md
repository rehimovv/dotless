# Rules

Every rule corresponds to behaviour measured in [research.md](research.md).
Functions that were measured to be locale independent have no rule.

## Severity

Only the pair I/i changes in Turkic locales, so equality checks against
ASCII constants are decidable:

| Conversion | Compared with a constant that contains | Result |
|---|---|---|
| to lower case | `i` (`"ini"`, `"file"`, `'i'`) | **high** |
| to upper case | `I` (`"INTEGER"`, `'I'`) | **high** |
| case-insensitive compare | `i` or `I` | **high** |
| any | a constant without i/I (`"png"`, `"jpeg"`) | not reported |

A finding is also **high** when the converted string is used as a lookup
key (`g_hash_table_*`, `g_key_file_*`, `g_settings_*`, `g_quark_*`,
`bsearch`, dictionary or map subscripts, `.get()`/`.has()`/`.lookup()`),
or is stored in a variable whose name says it is a key, extension, MIME
type, scheme, protocol, charset or header. dotless follows the variable for
60 lines to find such uses. Everything else is **low**.

## Suppressing a finding

```c
if (strcasecmp (s, "ini") == 0) /* dotless: ignore */
/* dotless: ignore[DL002] */    /* on its own line: applies to the next line */
/* dotless: ignore-file */      /* anywhere: skip the whole file */
```

Any comment syntax of the language works (`//`, `/* */`, `#`).

## Catalogue

### DL001 c-ctype-case — C, Rust (`libc::`)
`tolower()`, `toupper()`. In `tr_TR.UTF-8`/`az_AZ.UTF-8` glibc returns
`'I'` and `'i'` unchanged (the Turkic counterpart does not fit in a byte);
in `tr_TR.ISO-8859-9` it returns `ı`/`İ`.

```c
if (tolower (*p) == 'i')          /* high */
*p = g_ascii_tolower (*p);        /* fix */
```

### DL002 c-strcasecmp — C, Rust (`libc::`)
`strcasecmp()`, `strncasecmp()`, `strcasestr()`, `wcscasecmp()`,
`wcsncasecmp()`, and `strcasecmp` passed as a comparison callback.

```c
if (strcasecmp (ext, "ini") == 0)        /* high */
if (g_ascii_strcasecmp (ext, "ini") == 0) /* fix */
```

### DL003 c-wide-case — C
`towlower()`, `towupper()`: `towlower(L'I') == L'ı'`.
Fix: `g_unichar_tolower()` (locale independent) or `g_ascii_tolower()`.

### DL004 glib-utf8-case — C, Python (PyGObject), JavaScript (gjs), Rust (`glib::ffi`)
`g_utf8_strdown()`, `g_utf8_strup()`: `"INTEGER"` → `"ınteger"`.
Fix: `g_ascii_strdown()` for identifiers, `g_utf8_casefold()` to compare
human-readable text.

### DL005 glib-deprecated-case — C
`g_strdown()`, `g_strup()`, `g_strcasecmp()`, `g_strncasecmp()` use the C
library's `tolower()`. Fix: their `g_ascii_*` replacements.

### DL006 vala-string-case — Vala
`string.down()`, `string.up()` (they call `g_utf8_strdown/strup`).
Fix: `string.ascii_down()`/`ascii_up()` or `string.casefold()`.

### DL007 gjs-locale-case — JavaScript
`toLocaleLowerCase()`, `toLocaleUpperCase()` without an explicit locale.
gjs uses the process locale. (node 20 does not for the no-argument form;
see research.md.) Fix: `toLowerCase()`/`toUpperCase()`.

### DL008 js-localecompare-base — JavaScript
`a.localeCompare(b, undefined, {sensitivity: 'base'}) === 0`: I and i are
different base letters in Turkic collation. Only equality checks are
reported; sorting is meant to be locale aware.

### DL009 python-re-locale — Python
`re.IGNORECASE | re.LOCALE` (bytes patterns) uses the C library's
`tolower()`. Python's own `str.lower()`, `str.upper()`, `str.casefold()`
and `re.IGNORECASE` on `str` are locale independent and are not reported.
