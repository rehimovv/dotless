/* evolution-data-server: IMAP "nil" is not recognised in Turkic locales.
 *
 * camel-imapx-input-stream.c (camel_imapx_input_stream_nstring() and
 * camel_imapx_input_stream_nstring_bytes()) detects the NIL atom with
 *     toupper (p[0]) == 'N' && toupper (p[1]) == 'I' && toupper (p[2]) == 'L'
 * In tr_TR.UTF-8 / az_AZ.UTF-8 glibc's toupper ('i') returns 'i', so a
 * lower-case or mixed-case "nil" (IMAP atoms are case-insensitive,
 * RFC 3501 section 9) is rejected with "expecting nstring".
 *
 * Calling the functions through the installed provider module did not work
 * (its stream reports end-of-data on the first read even in C.UTF-8), so
 * this runs the condition copied verbatim from the scanned commit; run.sh
 * checks that the copied lines are still present in the source.
 */
#include <ctype.h>
#include <locale.h>
#include <stdio.h>

static int
is_nil (const char *p)
{
  /* Copied from camel-imapx-input-stream.c */
  if (toupper (p[0]) == 'N' &&
      toupper (p[1]) == 'I' &&
      toupper (p[2]) == 'L' &&
      p[3] == 0)
    return 1;
  return 0;
}

int
main (void)
{
  const char *tokens[] = { "NIL", "nil", "Nil" };

  setlocale (LC_ALL, "");
  for (unsigned i = 0; i < sizeof tokens / sizeof *tokens; i++)
    printf ("\"%s\": %s\n", tokens[i], is_nil (tokens[i]) ? "NIL" : "expecting nstring (error)");
  return 0;
}
