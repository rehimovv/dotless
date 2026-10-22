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
#include <gio/gio.h>

typedef GInputStream *(*NewFunc) (GInputStream *base);
typedef gboolean (*NstringFunc) (gpointer is, guchar **data, GCancellable *c, GError **error);
typedef gboolean (*NstringBytesFunc) (gpointer is, GBytes **out, gboolean progress, GCancellable *c, GError **error);

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

  for (gsize i = 0; i < G_N_ELEMENTS (tokens); i++)
    {
      GInputStream *base, *is;
      guchar *data = (guchar *) "unset";
      GBytes *bytes = NULL;
      GError *error = NULL;
      gboolean ok;

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
