# dotless

[![PyPI](https://img.shields.io/pypi/v/dotless)](https://pypi.org/project/dotless/)
[![Pipeline](https://gitlab.com/rehimovv/dotless/badges/main/pipeline.svg)](https://gitlab.com/rehimovv/dotless/-/pipelines)
[![Python versions](https://img.shields.io/pypi/pyversions/dotless)](https://pypi.org/project/dotless/)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)](https://gitlab.com/rehimovv/dotless/-/blob/main/LICENSE)

Find the Turkish and Azerbaijani "I" bug in C/GLib, Vala, Python,
JavaScript (gjs) and Rust code.

![dotless scanning evolution-data-server](https://gitlab.com/rehimovv/dotless/-/raw/main/docs/demo.svg)

In Turkish and Azerbaijani, the upper-case form of `i` is `İ` and the
lower-case form of `I` is `ı`. Code that changes case with the user's locale
and then compares the result with an ASCII keyword breaks for everyone
running `tr_TR` or `az_AZ`:

```c
char *t = g_utf8_strdown (type, -1);   /* "INTEGER" -> "ınteger" in tr_TR */
if (strcmp (t, "integer") == 0)        /* never true for Turkish users   */
  ...
if (strcasecmp (ext, "ini") == 0)      /* "INI" != "ini" in tr_TR/az_AZ  */
```

| | Upper | Lower |
|---|---|---|
| English | I | i |
| Turkish / Azerbaijani | I | ı |
| Turkish / Azerbaijani | İ | i |

## Why dotless?

This bug has been found and fixed one project at a time for decades.
Python's codec lookup failed under Turkish locales because it normalised
names with the C library's `tolower()`
([bpo-1813](https://bugs.python.org/issue1813), fixed 2011). LibreOffice's
resource compiler had to be fixed to work in `tr_TR.UTF-8` because of
`toupper()`/`tolower()`
([commit](https://github.com/LibreOffice/core/commit/81d2967bc7be11e7efa40a296fee40210843e5e7),
2016), and later failed to substitute configuration entries
([tdf#125284](https://github.com/LibreOffice/core/commit/7bc3da4ff0a6fda621340a4ded79f7ed4ce31d85),
2019). Geary did not sync mail from Gmail with `LC_CTYPE=tr_TR.UTF-8`
([GNOME bug 795906](https://bugzilla.gnome.org/show_bug.cgi?id=795906), fixed in 0.12.3).
dotless looks for the pattern systematically.

Every rule is backed by a measurement, not by documentation alone: small
probe programs run under `C.UTF-8`, `tr_TR.UTF-8`, `az_AZ.UTF-8` and
`tr_TR.ISO-8859-9` in CI ([docs/research.md](https://gitlab.com/rehimovv/dotless/-/blob/main/docs/research.md)). Some
results were not what one would guess:

* glibc's `toupper('i')` in a UTF-8 Turkish locale returns `'i'`, not `İ`:
  the answer does not fit in a byte, so the letter is left alone.
* GLib only applies Turkic rules after the program calls `setlocale()`.
  Every GTK application does; a plain Rust binary using `glib::ffi` does not.
* gjs and node disagree: `toLocaleLowerCase()` without arguments follows the
  locale in gjs but not in node 20.
* musl (Alpine) has no Turkish case mapping at all; the bug is a glibc bug in
  practice, which is what GNOME distributions ship.
* Python 3's `str.lower()` is locale independent. Only `re.LOCALE` on bytes
  is affected.

## Install

```bash
pipx install dotless
```

or `pip install dotless`. dotless needs Python 3.9 or newer and has no
dependencies. The development version installs with
`pipx install git+https://gitlab.com/rehimovv/dotless.git`.

## Usage

```bash
dotless scan path/to/project
```

| Option | |
|---|---|
| `--format text\|json\|sarif\|gitlab` | output format (default `text`) |
| `--min-severity low\|high` | hide low-severity findings |
| `--output FILE` | write the report to a file |
| `--exclude GLOB` | skip paths (repeatable); `.git`, `build`, `subprojects`, `node_modules`, `po` ... are skipped by default |
| `--disable RULE` | turn a rule off, e.g. `--disable DL005` (repeatable) |
| `--color auto\|always\|never` | colour in the terminal; `auto` honours `NO_COLOR` and turns colour off when output is piped |
| `--config FILE`, `--no-config` | read settings from another file, or ignore `pyproject.toml` |
| `--force-exclude` | apply excludes to files named on the command line too |
| `--exit-zero` | always exit with 0 |

`dotless rules` lists the rules and `dotless --version` prints the version.

**Exit status:** `0` nothing found, `1` findings reported, `2` usage or
configuration error (unknown option or rule, missing path, invalid
`[tool.dotless]`). Files that cannot be read are reported on stderr and
skipped.

To silence a finding, add a comment `dotless: ignore` (or
`dotless: ignore[DL002]`) on the same line or on the line above;
`dotless: ignore-file` skips a file.

### Configuration

dotless reads `[tool.dotless]` from the nearest `pyproject.toml` (in the
current directory or a parent). Command line options take precedence.

```toml
[tool.dotless]
exclude = ["vendor", "tests/data/*"]
min-severity = "high"
disable = ["DL005"]
```

Reading `pyproject.toml` needs Python 3.11 or newer (`tomllib`). On 3.9 and
3.10 dotless prints a warning and ignores the table; command line options
work everywhere.

### pre-commit

```yaml
repos:
  - repo: https://gitlab.com/rehimovv/dotless
    rev: v1.0.0
    hooks:
      - id: dotless
```

The hook passes `--force-exclude`, so `exclude` patterns from
`[tool.dotless]` also apply to the files pre-commit hands over.

### CI

GitLab — one line in `.gitlab-ci.yml`; findings show up in the merge
request Code Quality widget:

```yaml
include: 'https://gitlab.com/rehimovv/dotless/-/raw/main/ci/dotless.gitlab-ci.yml'
```

GitHub Actions — upload SARIF to code scanning:

```yaml
- run: pipx install dotless
- run: dotless scan . --format sarif --output dotless.sarif --exit-zero
- uses: github/codeql-action/upload-sarif@v4
  with:
    sarif_file: dotless.sarif
```

### Runtime check

```bash
dotless run -- ./my-program --some-args
```

runs the command under `C.UTF-8`, then under `tr_TR.UTF-8` and
`az_AZ.UTF-8`, and shows any difference in exit status, stdout or stderr.
Messages stay untranslated (`LANGUAGE=en`), so differences come from the
locale itself. Missing locales can be generated with
`localedef -i tr_TR -f UTF-8 tr_TR.UTF-8`. Exit status: `0` same output,
`1` differences, `2` the comparison could not run.

## Severity

Only I/i behaves differently, so dotless can often tell whether a call is
actually broken. A conversion is **high** when its result is compared with
an ASCII constant containing the affected letter (`"ini"`, `"file"`, `'I'`),
or is looked up as a hash table key, config key, file extension, MIME type
or protocol name. A comparison with a constant that has no i/I (`"png"`) is
the same in every locale and is not reported. Everything else is **low**.
Details: [docs/rules.md](https://gitlab.com/rehimovv/dotless/-/blob/main/docs/rules.md).

## Languages and rules

| Rule | Language | Flagged (locale-dependent) | Not flagged (measured safe) |
|---|---|---|---|
| DL001 | C, Rust `libc::` | `tolower`, `toupper` | `g_ascii_tolower`, `g_ascii_toupper` |
| DL002 | C, Rust `libc::` | `strcasecmp`, `strncasecmp`, `strcasestr`, `wcscasecmp` | `g_ascii_strcasecmp`, `g_ascii_strncasecmp` |
| DL003 | C | `towlower`, `towupper` | `g_unichar_tolower`, `g_unichar_toupper` |
| DL004 | C, Python, gjs, Rust `glib::ffi` | `g_utf8_strdown`, `g_utf8_strup` | `g_ascii_strdown`, `g_utf8_casefold` |
| DL005 | C | `g_strdown`, `g_strup`, `g_strcasecmp`, `g_strncasecmp` (deprecated) | |
| DL006 | Vala | `string.down()`, `string.up()` | `ascii_down()`, `ascii_up()`, `casefold()` |
| DL007 | JavaScript (gjs) | `toLocaleLowerCase()`, `toLocaleUpperCase()` without a locale | `toLowerCase()`, `toUpperCase()` |
| DL008 | JavaScript | `localeCompare(..., {sensitivity: 'base'}) === 0` | `localeCompare` for sorting |
| DL009 | Python | `re.IGNORECASE \| re.LOCALE` | `str.lower()`, `str.upper()`, `str.casefold()`, `re.IGNORECASE` |
| — | Rust | | `to_lowercase()`, `to_uppercase()`, `to_ascii_lowercase()` |

## Bugs found

* evolution-data-server: IMAP `NIL` detection and the NTLM LanManager hash
  use `toupper()`, so a lower-case `nil` is rejected and the LM response
  differs for passwords containing `i` under `tr_TR`/`az_AZ`
  ([#677](https://gitlab.gnome.org/GNOME/evolution-data-server/-/issues/677), reported).

A scan of ten GNOME modules and the reproducers behind this report are in
[reports/](https://gitlab.com/rehimovv/dotless/-/blob/main/reports/README.md) and [reproducers/](https://gitlab.com/rehimovv/dotless/-/tree/main/reproducers).

## Contributing

See [CONTRIBUTING.md](https://gitlab.com/rehimovv/dotless/-/blob/main/CONTRIBUTING.md). False positives are bugs; please
report them with the code that triggered them.

## License

GPL-3.0-or-later.

## Türkçe

dotless, büyük/küçük harf dönüşümünü sistem diline göre yapıp sonucu ASCII
bir anahtar kelimeyle karşılaştıran kodu bulur. Bu tür kod `tr_TR` ve
`az_AZ` yerellerinde bozulur: `"INTEGER"` küçültülünce `"ınteger"` olur,
`strcasecmp("INI", "ini")` eşit dönmez.

```bash
pipx install dotless
dotless scan <dizin>
```

Ayarlar `pyproject.toml` içindeki `[tool.dotless]` tablosundan okunur
(Python 3.11 ve üstü); pre-commit kancası ve GitLab/GitHub CI örnekleri
yukarıdadır. Bir bulguyu susturmak için satıra `dotless: ignore` yorumu
eklenir. Hangi fonksiyonun gerçekten yerele bağlı olduğu
[docs/research.md](https://gitlab.com/rehimovv/dotless/-/blob/main/docs/research.md) dosyasında ölçüm sonuçlarıyla
belgelenmiştir.

## Azərbaycanca

dotless böyük/kiçik hərf çevirməsini sistemin dilinə görə edib nəticəni
ASCII açar sözlə müqayisə edən kodu tapır. Belə kod `az_AZ` və `tr_TR`
lokallarında səhv işləyir: `"INTEGER"` kiçildiləndə `"ınteger"` olur,
`strcasecmp("INI", "ini")` bərabər qaytarmır.

```bash
pipx install dotless
dotless scan <qovluq>
```

Parametrlər `pyproject.toml` faylındakı `[tool.dotless]` cədvəlindən oxunur
(Python 3.11 və daha yeni); pre-commit və GitLab/GitHub CI nümunələri
yuxarıdadır. Tapıntını susdurmaq üçün sətrə `dotless: ignore` şərhi
əlavə olunur. Hansı funksiyanın həqiqətən lokaldan asılı olduğu
[docs/research.md](https://gitlab.com/rehimovv/dotless/-/blob/main/docs/research.md) faylında ölçmə nəticələri ilə
sənədləşdirilib.
