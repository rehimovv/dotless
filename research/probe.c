/* Locale probe for C library and GLib case-mapping functions.
 *
 * Usage: probe-c LOCALE
 * Prints one tab-separated line per API: c<TAB>api<TAB>locale<TAB>result
 * Bytes outside printable ASCII are printed as \xNN so that results from
 * single-byte locales (e.g. ISO-8859-9) stay readable.
 */
#define GLIB_DISABLE_DEPRECATION_WARNINGS
#include <ctype.h>
#include <locale.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <wchar.h>
#include <wctype.h>
#ifdef HAVE_GLIB
#include <glib.h>
#endif

static const char *loc;

static void
emit (const char *api, const char *result)
{
  printf ("c\t%s\t%s\t", api, loc);
  for (const unsigned char *p = (const unsigned char *) result; *p; p++)
    {
      if (*p >= 0x20 && *p < 0x7f && *p != '\\')
        putchar (*p);
      else
        printf ("\\x%02x", *p);
    }
  putchar ('\n');
}

static void
emit_int (const char *api, long v)
{
  char buf[64];
  snprintf (buf, sizeof buf, "%ld", v);
  emit (api, buf);
}

static void
emit_cp (const char *api, unsigned long cp)
{
  char buf[64];
  snprintf (buf, sizeof buf, "U+%04lX", cp);
  emit (api, buf);
}

static void
emit_char (const char *api, int c)
{
  char buf[2] = { (char) c, 0 };
  emit (api, buf);
}

static void
emit_bool (const char *api, int v)
{
  emit (api, v ? "equal" : "NOT equal");
}

int
main (int argc, char **argv)
{
  char buf[64];

  loc = argc > 1 ? argv[1] : "";
  if (!setlocale (LC_ALL, loc))
    {
      emit ("setlocale", "FAILED");
      return 1;
    }

  emit_char ("tolower('I')", tolower ('I'));
  emit_char ("toupper('i')", toupper ('i'));

  strcpy (buf, "INTEGER");
  for (char *p = buf; *p; p++)
    *p = tolower ((unsigned char) *p);
  emit ("tolower() loop on \"INTEGER\"", buf);

  strcpy (buf, "integer");
  for (char *p = buf; *p; p++)
    *p = toupper ((unsigned char) *p);
  emit ("toupper() loop on \"integer\"", buf);

  emit_bool ("strcasecmp(\"INTEGER\", \"integer\")", strcasecmp ("INTEGER", "integer") == 0);
  emit_bool ("strncasecmp(\"FILE\", \"file\", 4)", strncasecmp ("FILE", "file", 4) == 0);
  emit_cp ("towlower(L'I')", towlower (L'I'));
  emit_cp ("towupper(L'i')", towupper (L'i'));
  emit_bool ("wcscasecmp(L\"INTEGER\", L\"integer\")", wcscasecmp (L"INTEGER", L"integer") == 0);

  /* Locale independent controls. */
  emit_char ("isupper('I') (control)", isupper ('I') ? 'y' : 'n');

#ifdef HAVE_GLIB
  {
    gchar *s;

    s = g_utf8_strdown ("INTEGER", -1);
    emit ("g_utf8_strdown(\"INTEGER\")", s);
    g_free (s);

    s = g_utf8_strup ("integer", -1);
    emit ("g_utf8_strup(\"integer\")", s);
    g_free (s);

    s = g_utf8_casefold ("INTEGER", -1);
    emit ("g_utf8_casefold(\"INTEGER\")", s);
    g_free (s);

    emit_cp ("g_unichar_tolower('I')", g_unichar_tolower ('I'));
    emit_cp ("g_unichar_toupper('i')", g_unichar_toupper ('i'));

    s = g_ascii_strdown ("INTEGER", -1);
    emit ("g_ascii_strdown(\"INTEGER\")", s);
    g_free (s);

    s = g_ascii_strup ("integer", -1);
    emit ("g_ascii_strup(\"integer\")", s);
    g_free (s);

    emit_char ("g_ascii_tolower('I')", g_ascii_tolower ('I'));
    emit_char ("g_ascii_toupper('i')", g_ascii_toupper ('i'));
    emit_bool ("g_ascii_strcasecmp(\"INTEGER\", \"integer\")",
               g_ascii_strcasecmp ("INTEGER", "integer") == 0);
    emit_bool ("g_ascii_strncasecmp(\"FILE\", \"file\", 4)",
               g_ascii_strncasecmp ("FILE", "file", 4) == 0);

    /* Deprecated API that still appears in older code. */
    emit_bool ("g_strcasecmp(\"INTEGER\", \"integer\") [deprecated]",
               g_strcasecmp ("INTEGER", "integer") == 0);
    emit_bool ("g_strncasecmp(\"FILE\", \"file\", 4) [deprecated]",
               g_strncasecmp ("FILE", "file", 4) == 0);

    strcpy (buf, "INTEGER");
    emit ("g_strdown(\"INTEGER\") [deprecated]", g_strdown (buf));
    strcpy (buf, "integer");
    emit ("g_strup(\"integer\") [deprecated]", g_strup (buf));

    emit_bool ("g_str_match_string(\"integer\", \"INTEGER\", FALSE)",
               g_str_match_string ("integer", "INTEGER", FALSE));

    {
      int r = g_utf8_collate ("integer", "INTEGER");
      emit_int ("sign(g_utf8_collate(\"integer\", \"INTEGER\"))", (r > 0) - (r < 0));
    }
  }
#endif
  return 0;
}
