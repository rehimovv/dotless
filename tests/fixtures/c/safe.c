/* Nothing in this file may be reported. */
#include <ctype.h>
#include <string.h>
#include <strings.h>
#include <glib.h>

/* tolower() in a comment is not code: if (tolower (c) == 'i') */
static const char *doc = "call tolower (c) or strcasecmp (a, \"ini\")";

int tolower (int c);              /* a declaration, not a call */
#define my_lower(c) g_ascii_tolower (c)

static gboolean
is_integer_type (const char *type)
{
  char *low = g_ascii_strdown (type, -1);
  gboolean ret = strcmp (low, "integer") == 0;
  g_free (low);
  return ret || g_ascii_strcasecmp (type, "INTEGER") == 0;
}

static gboolean
is_png (const char *name)
{
  /* "png" has no i/I: the comparison is the same in every locale. */
  return strcasecmp (name, "png") == 0;
}

static gboolean
is_x (int c)
{
  return tolower (c) == 'x';
}

static gboolean
is_jpeg (const char *s)
{
  char *low = g_utf8_strdown (s, -1);
  gboolean ret = g_str_equal (low, "jpeg");
  g_free (low);
  return ret;
}

static void
fold (const char *s)
{
  char *f = g_utf8_casefold (s, -1);
  gunichar c = g_unichar_tolower (g_utf8_get_char (s));
  g_free (f);
  (void) c;
}

static gboolean
suppressed (const char *s)
{
  /* dotless: ignore */
  if (strcasecmp (s, "ini") == 0)
    return TRUE;
  return strcasecmp (s, "inf") == 0; /* dotless: ignore[DL002] */
}

static void
members (struct thing *t, struct thing u)
{
  t->tolower (t);
  u.toupper (u);
}
