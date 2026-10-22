/* evolution-data-server: IMAP "nil" is not recognised in Turkic locales.
 *
 * camel-imapx-input-stream.c checks for the NIL atom with
 *     toupper (p[0]) == 'N' && toupper (p[1]) == 'I' && toupper (p[2]) == 'L'
 * In tr_TR.UTF-8 / az_AZ.UTF-8 glibc's toupper ('i') returns 'i', so a
 * lower-case "nil" (IMAP atoms are case-insensitive) is rejected with
 * "expecting nstring".
 *
 * This calls the real functions from the installed IMAPX provider module.
 * Usage: repro /path/to/libcamelimapx.so
 */
#include <dlfcn.h>
#include <locale.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <gio/gio.h>
#include <gio/gunixinputstream.h>

typedef GInputStream *(*NewFunc) (GInputStream *base);
typedef gboolean (*NstringFunc) (gpointer is, guchar **data, GCancellable *c, GError **error);
typedef gboolean (*NstringBytesFunc) (gpointer is, GBytes **out, gboolean progress, GCancellable *c, GError **error);

/* A pollable stream over a pipe, like the socket the provider reads from. */
static GInputStream *
stream_for (const char *text)
{
  int fds[2];

  if (pipe (fds) != 0)
    return NULL;
  if (write (fds[1], text, strlen (text)) < 0)
    return NULL;
  close (fds[1]);
  return g_unix_input_stream_new (fds[0], TRUE);
}

int
main (int argc, char **argv)
{
  const char *tokens[] = { "NIL", "nil", "Nil" };
  void *module;
  NewFunc new_stream;
  NstringFunc nstring;
  NstringBytesFunc nstring_bytes;

  setlocale (LC_ALL, "");
  module = dlopen (argv[1], RTLD_NOW | RTLD_GLOBAL);
  if (!module)
    {
      printf ("dlopen failed: %s\n", dlerror ());
      return 2;
    }
  new_stream = (NewFunc) dlsym (module, "camel_imapx_input_stream_new");
  nstring = (NstringFunc) dlsym (module, "camel_imapx_input_stream_nstring");
  nstring_bytes = (NstringBytesFunc) dlsym (module, "camel_imapx_input_stream_nstring_bytes");
  if (!new_stream || !nstring)
    {
      printf ("symbols not found\n");
      return 2;
    }

  if (g_getenv ("REPRO_DEBUG"))
    {
      GInputStream *base = g_memory_input_stream_new_from_data (g_strdup ("NIL )\r\n"), -1, g_free);
      GInputStream *is = new_stream (base);
      char buf[64] = { 0 };
      GError *error = NULL;
      gssize n;

      printf ("debug: type=%s filter=%d same-base=%d\n", G_OBJECT_TYPE_NAME (is),
              G_IS_FILTER_INPUT_STREAM (is),
              G_IS_FILTER_INPUT_STREAM (is) && g_filter_input_stream_get_base_stream (G_FILTER_INPUT_STREAM (is)) == base);
      n = g_input_stream_read (base, buf, sizeof buf - 1, NULL, &error);
      printf ("debug: direct read of base: %" G_GSSIZE_FORMAT " \"%s\"\n", n, buf);

      {
        typedef int (*TokenFunc) (gpointer is, guchar **token, guint *len, GCancellable *c, GError **error);
        TokenFunc token = (TokenFunc) dlsym (module, "camel_imapx_input_stream_token");
        GInputStream *b2 = g_memory_input_stream_new_from_data (g_strdup ("NIL )\r\n"), -1, g_free);
        GInputStream *s2 = new_stream (b2);

        for (int k = 0; token && k < 3; k++)
          {
            guchar *t = NULL;
            guint len = 0;
            int tok = token (s2, &t, &len, NULL, &error);
            printf ("debug: token %d: type=%d len=%u \"%.*s\" %s\n", k, tok, len, (int) len,
                    t ? (char *) t : "", error ? error->message : "");
            g_clear_error (&error);
          }
      }
    }

  for (gsize i = 0; i < G_N_ELEMENTS (tokens); i++)
    {
      GInputStream *base, *is;
      guchar *data = (guchar *) "unset";
      GBytes *bytes = NULL;
      GError *error = NULL;
      gboolean ok;
      g_autofree char *line = g_strdup_printf ("%s )
", tokens[i]);

      base = g_memory_input_stream_new_from_data (g_strdup_printf ("%s )\r\n", tokens[i]), -1, g_free);
      is = new_stream (base);
      ok = nstring (is, &data, NULL, &error);
      printf ("nstring(\"%s\"): %s\n", tokens[i],
              ok ? (data == NULL ? "NIL" : "a string") : error->message);
      g_clear_error (&error);
      g_object_unref (is);
      g_object_unref (base);

      if (!nstring_bytes)
        continue;
      base = g_memory_input_stream_new_from_data (g_strdup_printf ("%s )\r\n", tokens[i]), -1, g_free);
      is = new_stream (base);
      ok = nstring_bytes (is, &bytes, FALSE, NULL, &error);
      printf ("nstring_bytes(\"%s\"): %s\n", tokens[i],
              ok ? (bytes == NULL ? "NIL" : "a string") : error->message);
      g_clear_error (&error);
      g_clear_pointer (&bytes, g_bytes_unref);
      g_object_unref (is);
      g_object_unref (base);
    }
  return 0;
}
