# dotless

Find the Turkish and Azerbaijani "I" bug in C/GLib, Vala, Python,
JavaScript (gjs) and Rust code.

In Turkish and Azerbaijani, the upper-case form of `i` is `İ` and the
lower-case form of `I` is `ı`, so code that case-converts with the user's
locale and then compares the result with an ASCII keyword breaks for
everyone running `tr_TR` or `az_AZ`:

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

Bugs like this have been fixed one at a time in LibreOffice, Mir, Python and
many others. dotless looks for them systematically.

## Install

```bash
pipx install git+https://gitlab.com/rehimovv/dotless.git
```

From a checkout, `pipx install .` works too. dotless needs Python 3.9 or
newer and has no dependencies.

## Usage

```bash
dotless scan path/to/project
```

```
src/parser.c:118:13: [high] DL004 g_utf8_strdown: g_utf8_strdown()/g_utf8_strup() use Turkic rules ...
    char *low = g_utf8_strdown (type, -1);
    why: stored in `low`, which is passed to strcmp() with "integer" (line 119)
    fix: Use g_ascii_strdown()/g_ascii_strup() for identifiers, or g_utf8_casefold() ...
```

Options:

| Option | |
|---|---|
| `--format text\|json\|sarif\|gitlab` | output format (default `text`) |
| `--min-severity low\|high` | hide low-severity findings |
| `--output FILE` | write the report to a file |
| `--exclude GLOB` | skip paths (repeatable); `.git`, `build`, `subprojects`, `node_modules` ... are skipped by default |
| `--exit-zero` | always exit 0 (default: exit 1 when something is found) |

`dotless rules` lists the rules. To silence a finding, add a comment
`dotless: ignore` (or `dotless: ignore[DL002]`) on the same line or on the
line above; `dotless: ignore-file` skips a file.

### Runtime check

```bash
dotless run -- ./my-program --some-args
```

runs the command under `C.UTF-8`, then under `tr_TR.UTF-8` and
`az_AZ.UTF-8`, and shows any difference in exit status, stdout or stderr.
Messages stay untranslated (`LANGUAGE=en`), so differences come from the
locale itself. Missing locales can be generated with
`localedef -i tr_TR -f UTF-8 tr_TR.UTF-8`.

## Severity

Only I/i behaves differently, so dotless can often decide whether a call is
actually broken. A conversion is **high** when its result is compared with an
ASCII constant containing the affected letter (`"ini"`, `"file"`, `'I'`), or
is used as a hash table key, config key, file extension, MIME type or
protocol name. A comparison with a constant that has no i/I (`"png"`) is
the same in every locale and is not reported. Everything else is **low**.
Details: [docs/rules.md](docs/rules.md).

## CI

GitLab — one line in `.gitlab-ci.yml` (findings show up in the merge request
Code Quality widget):

```yaml
include: 'https://gitlab.com/rehimovv/dotless/-/raw/main/ci/dotless.gitlab-ci.yml'
```

GitHub Actions — upload SARIF to code scanning:

```yaml
- run: pipx install git+https://gitlab.com/rehimovv/dotless.git
- run: dotless scan . --format sarif --output dotless.sarif --exit-zero
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: dotless.sarif
```

## Languages and rules

Each rule is backed by a measurement under `tr_TR.UTF-8`, `az_AZ.UTF-8` and
`tr_TR.ISO-8859-9` on glibc; see [docs/research.md](docs/research.md) for
the full table and the probe programs.

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

Things measured along the way: musl (Alpine) has no Turkic case mapping;
GLib only switches to Turkic rules after the program calls `setlocale()`
(every GTK application does); node and gjs disagree on
`toLocaleLowerCase()` without arguments.

## Development

```bash
pip install -e '.[test]'
pytest
```

`research/run.sh` re-runs the locale measurements (needs glibc, GLib,
valac, gjs, node and cargo; the `research:glibc` CI job does this in Debian).

## License

GPL-3.0-or-later.

## Türkçe / Azərbaycanca

**Türkçe.** dotless, büyük/küçük harf dönüşümünü sistem diline göre yapıp
sonucu ASCII bir anahtar kelimeyle karşılaştıran kodu bulur. Bu tür kod
`tr_TR` ve `az_AZ` yerellerinde bozulur: `"INTEGER"` küçültülünce
`"ınteger"` olur, `strcasecmp("INI", "ini")` eşit dönmez. Kurulum ve
kullanım yukarıdakiyle aynıdır: `dotless scan <dizin>`. Hangi fonksiyonun
gerçekten yerele bağlı olduğu `docs/research.md` dosyasında test sonuçlarıyla
belgelenmiştir.

**Azərbaycanca.** dotless böyük/kiçik hərf çevirməsini sistemin dilinə görə
edib nəticəni ASCII açar sözlə müqayisə edən kodu tapır. Belə kod `az_AZ`
və `tr_TR` lokallarında səhv işləyir: `"INTEGER"` kiçildiləndə `"ınteger"`
olur, `strcasecmp("INI", "ini")` bərabər qaytarmır. Quraşdırma və istifadə
yuxarıdakı kimidir: `dotless scan <qovluq>`. Hansı funksiyanın həqiqətən
lokaldan asılı olduğu `docs/research.md` faylında test nəticələri ilə
sənədləşdirilib.
