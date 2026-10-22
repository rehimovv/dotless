# Which case-mapping functions depend on the locale?

Every rule in dotless is backed by a measurement in this file. Nothing here
is taken from documentation alone: each function was called with `"I"`,
`"i"`, `"INTEGER"` or `"integer"` under several locales and the output was
recorded.

## Method

* Probe programs live in [`research/`](../research): `probe.c` (C library
  and GLib), `probe.vala`, `probe.py`, `probe.js` (run under both gjs and
  node) and `rust-probe/`.
* [`research/run.sh`](../research/run.sh) builds each probe and runs it with
  `LC_ALL`/`LANG` set to `C.UTF-8`, `en_US.UTF-8`, `tr_TR.UTF-8`,
  `az_AZ.UTF-8` and `tr_TR.ISO-8859-9`. The C, Vala and Python probes also
  call `setlocale(LC_ALL, ...)` as a GTK application does.
* The probes run in GitLab CI (`research:glibc` and `research:musl` jobs in
  [`.gitlab-ci.yml`](../.gitlab-ci.yml)); locales are generated with
  `localedef`. A row is marked locale-dependent when a Turkic locale gives
  a different answer than `C.UTF-8`.
* Measured with: Debian 13 (trixie), glibc 2.41, GLib 2.84, Vala 0.56.18,
  Python 3.13.5, gjs 1.82.3, node 20.19.2, rustc 1.85.1, glib-rs 0.20.12;
  and Alpine 3.20 (musl) for comparison.
  CI jobs: https://gitlab.com/rehimovv/dotless/-/jobs/17367126376 (glibc),
  https://gitlab.com/rehimovv/dotless/-/jobs/17367075809 (musl)

## Summary

| Language | Locale-dependent (flagged by dotless) | Locale-independent (not flagged) |
|---|---|---|
| C (glibc) | `tolower`, `toupper`, `strcasecmp`, `strncasecmp`, `strcasestr`, `towlower`, `towupper`, `wcscasecmp` | `isupper` (control) |
| GLib (C) | `g_utf8_strdown`, `g_utf8_strup`; deprecated `g_strdown`, `g_strup`, `g_strcasecmp`, `g_strncasecmp` | `g_ascii_*`, `g_utf8_casefold`, `g_unichar_tolower/toupper`, `g_str_match_string` |
| Vala | `string.down()`, `string.up()` | `string.ascii_down()`, `string.ascii_up()`, `string.casefold()`, `unichar.tolower()/toupper()` |
| Python 3 | `re.IGNORECASE \| re.LOCALE` on bytes; `GLib.utf8_strdown/strup` via PyGObject | `str.lower()`, `str.upper()`, `str.casefold()`, `bytes.lower()/upper()`, `re.IGNORECASE` on str |
| JavaScript (gjs) | `toLocaleLowerCase()`, `toLocaleUpperCase()` without an explicit locale; `localeCompare` with `sensitivity: 'base'`; `GLib.utf8_strdown/strup` | `toLowerCase()`, `toUpperCase()`, `/re/i`, `toLocaleLowerCase('en-US')` |
| Rust | `glib::ffi::g_utf8_strdown/strup` (only after `setlocale`, which `gtk::init` does); `libc::tolower`, `libc::strcasecmp` | `str::to_lowercase()`, `to_uppercase()`, `to_ascii_lowercase()`, `eq_ignore_ascii_case()` |

## Findings worth knowing

1. **glibc in a UTF-8 Turkic locale does not produce `ı`/`İ` from
   `tolower`/`toupper`** — the result does not fit in one byte, so it leaves
   the letter alone: `tolower('I') == 'I'` and `toupper('i') == 'i'`. The
   effect is the same for keyword matching: `"INTEGER"` becomes
   `"Integer"`, and `strcasecmp("INTEGER", "integer") != 0`. In
   `tr_TR.ISO-8859-9` the single-byte `ı` (0xFD) / `İ` (0xDD) are returned.
2. **`tr_TR` and `az_AZ` behave identically** in every case measured.
3. **gjs and node disagree.** In gjs (SpiderMonkey), `toLocaleLowerCase()`
   with no argument follows the process locale. In node 20 (V8), the
   no-argument and `undefined` forms stay locale-independent, although
   `toLocaleLowerCase([])` does follow the locale. dotless targets GNOME
   JavaScript, which runs under gjs, so the no-argument form is flagged.
4. **Python 3 string methods are safe.** Only `re.LOCALE` on bytes patterns
   goes through the C library's `tolower()`.
5. **GLib only switches to Turkic rules if the program called
   `setlocale()`.** A plain Rust binary using `glib::ffi::g_utf8_strdown`
   is unaffected until something like `gtk::init()` calls `setlocale`.
   glib-rs 0.20 does not wrap `g_utf8_strdown`/`g_utf8_strup` at all (it
   only wraps `g_utf8_casefold`, which is locale independent).
6. **musl has no locale-specific case mapping.** On Alpine all C functions
   above behave like the C locale ([raw table](research-data/musl-alpine3.20.md)).
   The bugs dotless looks for are therefore glibc bugs in practice — which
   is what GNOME distributions ship.
7. Collation (`g_utf8_collate`, `string.collate`, `strxfrm`) differs between
   `C` and `en_US` already, so it is not a Turkic-specific problem and no
   rule covers it.

## Full results (glibc)

Non-ASCII output is escaped: `\xc4\xb1` and `ı` are `ı`, `\xc4\xb0`
and `İ` are `İ`, `\xfd`/`\xdd` are `ı`/`İ` in ISO-8859-9. A `-` means
the probe was not run for that locale.

| Language | API | C.UTF-8 | en_US.UTF-8 | tr_TR.UTF-8 | az_AZ.UTF-8 | tr_TR.ISO-8859-9 | Locale-dependent? |
|---|---|---|---|---|---|---|---|
| c | `tolower('I')` | `i` | `i` | `I` | `I` | `\xfd` | **YES** |
| c | `toupper('i')` | `I` | `I` | `i` | `i` | `\xdd` | **YES** |
| c | `tolower() loop on "INTEGER"` | `integer` | `integer` | `Integer` | `Integer` | `\xfdnteger` | **YES** |
| c | `toupper() loop on "integer"` | `INTEGER` | `INTEGER` | `iNTEGER` | `iNTEGER` | `\xddNTEGER` | **YES** |
| c | `strcasecmp("INTEGER", "integer")` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `strncasecmp("FILE", "file", 4)` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `strcasestr("MIME-INFO", "info") != NULL` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `towlower(L'I')` | `U+0069` | `U+0069` | `U+0131` | `U+0131` | `U+0131` | **YES** |
| c | `towupper(L'i')` | `U+0049` | `U+0049` | `U+0130` | `U+0130` | `U+0130` | **YES** |
| c | `wcscasecmp(L"INTEGER", L"integer")` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `isupper('I') (control)` | `y` | `y` | `y` | `y` | `y` | no |
| c | `g_utf8_strdown("INTEGER")` | `integer` | `integer` | `\xc4\xb1nteger` | `\xc4\xb1nteger` | `\xc4\xb1nteger` | **YES** |
| c | `g_utf8_strup("integer")` | `INTEGER` | `INTEGER` | `\xc4\xb0NTEGER` | `\xc4\xb0NTEGER` | `\xc4\xb0NTEGER` | **YES** |
| c | `g_utf8_casefold("INTEGER")` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| c | `g_unichar_tolower('I')` | `U+0069` | `U+0069` | `U+0069` | `U+0069` | `U+0069` | no |
| c | `g_unichar_toupper('i')` | `U+0049` | `U+0049` | `U+0049` | `U+0049` | `U+0049` | no |
| c | `g_ascii_strdown("INTEGER")` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| c | `g_ascii_strup("integer")` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| c | `g_ascii_tolower('I')` | `i` | `i` | `i` | `i` | `i` | no |
| c | `g_ascii_toupper('i')` | `I` | `I` | `I` | `I` | `I` | no |
| c | `g_ascii_strcasecmp("INTEGER", "integer")` | `equal` | `equal` | `equal` | `equal` | `equal` | no |
| c | `g_ascii_strncasecmp("FILE", "file", 4)` | `equal` | `equal` | `equal` | `equal` | `equal` | no |
| c | `g_strcasecmp("INTEGER", "integer") [deprecated]` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `g_strncasecmp("FILE", "file", 4) [deprecated]` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `g_strdown("INTEGER") [deprecated]` | `integer` | `integer` | `Integer` | `Integer` | `\xfdnteger` | **YES** |
| c | `g_strup("integer") [deprecated]` | `INTEGER` | `INTEGER` | `iNTEGER` | `iNTEGER` | `\xddNTEGER` | **YES** |
| c | `g_str_match_string("integer", "INTEGER", FALSE)` | `equal` | `equal` | `equal` | `equal` | `equal` | no |
| c | `sign(g_utf8_collate("integer", "INTEGER"))` | `1` | `-1` | `1` | `1` | `1` | no |
| vala | `string.down()` | `integer` | `integer` | `\304\261nteger` | `\304\261nteger` | `\304\261nteger` | **YES** |
| vala | `string.up()` | `INTEGER` | `INTEGER` | `\304\260NTEGER` | `\304\260NTEGER` | `\304\260NTEGER` | **YES** |
| vala | `string.casefold()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| vala | `string.ascii_down()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| vala | `string.ascii_up()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| vala | `string.down() == "integer"` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| vala | `unichar.tolower('I')` | `U+0069` | `U+0069` | `U+0069` | `U+0069` | `U+0069` | no |
| vala | `unichar.toupper('i')` | `U+0049` | `U+0049` | `U+0049` | `U+0049` | `U+0049` | no |
| vala | `string.collate() sign` | `1` | `-1` | `1` | `1` | `1` | no |
| python | `str.lower()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| python | `str.upper()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| python | `str.casefold()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| python | `bytes.lower()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| python | `bytes.upper()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| python | `re.IGNORECASE (str)` | `match` | `match` | `match` | `match` | `match` | no |
| python | `re.IGNORECASE\|re.LOCALE (bytes)` | `match` | `match` | `NO match` | `NO match` | `NO match` | **YES** |
| python | `locale.strxfrm order I<i` | `True` | `False` | `True` | `True` | `True` | no |
| python | `GLib.utf8_strdown() via gi` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| python | `GLib.utf8_strup() via gi` | `INTEGER` | `INTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | **YES** |
| python | `GLib.ascii_strdown() via gi` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| node | `Intl default locale` | `en-US` | `en-US` | `tr-TR` | `az-AZ` | `tr-TR` | **YES** |
| node | `toLowerCase()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| node | `toUpperCase()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| node | `toLocaleLowerCase()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| node | `toLocaleUpperCase()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| node | `toLocaleLowerCase(undefined)` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| node | `toLocaleLowerCase([])` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| node | `toLocaleLowerCase('en-US')` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| node | `toLocaleLowerCase('tr')` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | no |
| node | `localeCompare(..., {sensitivity: 'base'}) === 0` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| node | `/integer/i.test("INTEGER")` | `match` | `match` | `match` | `match` | `match` | no |
| gjs | `Intl default locale` | `en-US` | `en-US` | `tr-TR` | `az-AZ` | `tr-TR` | **YES** |
| gjs | `toLowerCase()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| gjs | `toUpperCase()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| gjs | `toLocaleLowerCase()` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| gjs | `toLocaleUpperCase()` | `INTEGER` | `INTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | **YES** |
| gjs | `toLocaleLowerCase(undefined)` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| gjs | `toLocaleLowerCase([])` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| gjs | `toLocaleLowerCase('en-US')` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| gjs | `toLocaleLowerCase('tr')` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | no |
| gjs | `localeCompare(..., {sensitivity: 'base'}) === 0` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| gjs | `/integer/i.test("INTEGER")` | `match` | `match` | `match` | `match` | `match` | no |
| gjs | `GLib.utf8_strdown()` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| gjs | `GLib.utf8_strup()` | `INTEGER` | `INTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | **YES** |
| gjs | `GLib.ascii_strdown()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| rust | `str::to_lowercase()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| rust | `str::to_uppercase()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| rust | `str::to_ascii_lowercase()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| rust | `str::eq_ignore_ascii_case()` | `equal` | `equal` | `equal` | `equal` | `equal` | no |
| rust | `g_utf8_strdown() without setlocale()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| rust | `g_utf8_strdown() after setlocale(LC_ALL, "")` | `integer` | `integer` | `\u{131}nteger` | `\u{131}nteger` | `\u{131}nteger` | **YES** |
