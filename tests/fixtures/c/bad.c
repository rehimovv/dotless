/* Locale-dependent case mapping. Each flagged line has an EXPECT marker. */
#include <ctype.h>
#include <string.h>
#include <strings.h>
#include <wctype.h>
#include <glib.h>

static const char *keywords[] = { "if", "int", "while" };

static gboolean
is_integer_type (const char *type)
{
  char *low = g_utf8_strdown (type, -1); /* EXPECT DL004 high */
  gboolean ret = strcmp (low, "integer") == 0;
  g_free (low);
  return ret;
}

static gboolean
is_ini (const char *name)
{
  return strcasecmp (name, "ini") == 0; /* EXPECT DL002 high */
}

static gboolean
starts_with_info (const char *s)
{
  return strncasecmp (s, "INFO:", 5) == 0; /* EXPECT DL002 high */
}

static gboolean
contains_mime (const char *s)
{
  return strcasestr (s, "mime") != NULL; /* EXPECT DL002 high */
}

static int
first_is_i (const char *s)
{
  return tolower (*s) == 'i'; /* EXPECT DL001 high */
}

static void
upcase (char *s)
{
  for (; *s; s++)
    *s = toupper (*s); /* EXPECT DL001 low */
}

static gpointer
lookup (GHashTable *table, const char *name)
{
  return g_hash_table_lookup (table, g_utf8_strup (name, -1)); /* EXPECT DL004 high */
}

static const char *
mime_for (const char *filename)
{
  char *ext = g_utf8_strdown (strrchr (filename, '.'), -1); /* EXPECT DL004 high */
  return ext;
}

static gboolean
wide_eq (wchar_t c)
{
  return towlower (c) == L'i'; /* EXPECT DL003 high */
}

static gboolean
old_api (char *s)
{
  g_strdown (s); /* EXPECT DL005 low */
  return g_strcasecmp (s, "pixbuf") == 0; /* EXPECT DL005 high */
}

static gboolean
is_keyword (const char *word)
{
  return bsearch (&word, keywords, 3, sizeof (char *), (GCompareFunc) strcasecmp) != NULL; /* EXPECT DL002 high */
}

static void
switch_on_char (int c)
{
  switch (toupper (c)) /* EXPECT DL001 high */
    {
    case 'A': break;
    case 'I': break;
    }
}
