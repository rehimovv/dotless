# GNOME scan, 2026-10-22

dotless 0.1.0 (after the false-positive fixes in commit "Reduce false
positives found in GNOME modules") on shallow clones of gitlab.gnome.org
`main` branches. One JSON report per module is in this directory.

| Module | Commit | Files | High | Low | Rules |
|---|---|---|---|---|---|
| glib | b683d23e85c5 | 1528 | 0 | 34 | DL001×12, DL002×2, DL004×16, DL005×4 |
| gtk | 65947392edc9 | 2939 | 0 | 17 | DL002×5, DL004×12 |
| gnome-shell | 7574dd19d71a | 420 | 0 | 0 | - |
| mutter | 35f64c3d5864 | 1632 | 0 | 4 | DL002×4 |
| nautilus | a9f8ce885d97 | 302 | 0 | 1 | DL004×1 |
| gnome-control-center | a7e126b2b82c | 583 | 0 | 1 | DL004×1 |
| gnome-text-editor | 16542f0f4c37 | 124 | 0 | 6 | DL004×6 |
| epiphany | 8dd56f2758ba | 358 | 0 | 4 | DL004×4 |
| evolution-data-server | e3d4270d1f61 | 1081 | 5 | 15 | DL001×15, DL002×4, DL004×1 |
| gnome-settings-daemon | d3e717002a6f | 142 | 0 | 0 | - |

All ten modules were reachable; none was skipped.

## High-severity findings and reproduction

Reproducers are in [`../reproducers`](../reproducers) and run in the
`reproducers` CI job (Debian 13, glibc 2.41), under `C.UTF-8` as control and
under `tr_TR.UTF-8` and `az_AZ.UTF-8`:
https://gitlab.com/rehimovv/dotless/-/jobs/17367502098

| # | Location (evolution-data-server) | Result |
|---|---|---|
| 1 | `camel/providers/imapx/camel-imapx-input-stream.c:531` `toupper (p[1]) == 'I'` | **Verified** — `nil`/`Nil` rejected as "expecting nstring" in tr_TR and az_AZ (copied condition, checked verbatim against the commit) |
| 2 | `camel/providers/imapx/camel-imapx-input-stream.c:603` `toupper (token[1]) == 'I'` | **Verified** — same code in `nstring_bytes()` |
| 3 | `addressbook/backends/ldap/openldap-extract.h:546` `strcasecmp (sval, "AUXILIARY")` | **Verified in isolation** — real header compiled; but it is only built with Sun LDAP (`#ifdef SUNLDAP`), not on Linux |
| 4 | `addressbook/backends/ldap/openldap-extract.h:672` `strcasecmp (sval,"AUXILIARY")` | **Verified in isolation** — `auxiliary` gives parse error 2 in tr_TR/az_AZ; same Sun LDAP caveat |
| 5 | `addressbook/backends/ldap/openldap-extract.h:926` `strncasecmp (p, LDAPI_URL_PREFIX, ...)` | **Verified in isolation** — `LDAPI://` URL rejected (rc 3); same Sun LDAP caveat |

Calling the IMAPX functions end to end through Debian's installed
`libcamelimapx.so` was attempted and did not work: the provider's stream
reported end-of-data on its first read for any input, also under
`C.UTF-8`. The cause was not found, so items 1–2 rely on the copied
condition instead.

Found while reviewing low findings (dotless rates it low because it cannot
see that the buffer is a hash input):

| Location | Result |
|---|---|
| `camel/camel-sasl-ntlm.c:129` `lm_password[i] = toupper (...)` | **Verified** (copied loop) — LM key input is `ADMiN1` instead of `ADMIN1` in tr_TR/az_AZ. Only used when the server does not negotiate NTLM2 session security. |

Issue drafts: `../drafts/evolution-data-server.md`.

## What the false positives taught

The first scan produced 7 high findings; 3 were false positives and the
rules were changed (with tests) accordingly:

* `gtk/examples/application{8,9}/exampleappwin.c` —
  `g_hash_table_add (strings, g_utf8_strdown (word, -1))` stores words for
  completion. Storing a converted key is consistent within a run, so
  inserts are now **low**; lookups stay high.
* `gtk/gtk/deprecated/gtkshortcutswindow.c` — `keywords = g_utf8_strdown (...)`
  holds user search terms. `key`/`keyword` were removed from the list of
  identifier-like variable names.
* GLib's own definitions and prototypes (`g_utf8_strup (const gchar *str, ...)`
  in `gunicode.h`, `guniprop.c`, `gstrfuncs.c`) were reported as calls.
  Parameter lists are now recognised and skipped.
* `#define LDAPI_URL_PREFIX "ldapi://"` was invisible to the analysis;
  `#define NAME "literal"` constants in the same file are now resolved,
  which turned finding 5 from low into high.

Remaining low-severity patterns, not changed on purpose:

* Search and filter code (`gtkquery.c`, `nautilus-query.c`,
  `gtkplacesview.c`, `editor-language-dialog.c`, epiphany) lowers both the
  query and the candidates with `g_utf8_strdown`, which is consistent and
  arguably the intended user-facing behaviour.
* Code under `#ifdef` for other platforms (`gdk/win32/*`, Sun LDAP) is
  scanned like any other code; dotless does not evaluate preprocessor
  conditions.
* Hex decoding with `toupper`/`tolower` (`e-vcard.c`, `camel-mime-utils.c`,
  `e-url.c`) is unaffected in practice because hex digits contain no I.
