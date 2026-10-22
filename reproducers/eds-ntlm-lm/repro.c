/* evolution-data-server: NTLM LM hash input in Turkic locales.
 *
 * camel-sasl-ntlm.c, ntlm_lanmanager_hash() upper-cases the password with
 *     lm_password[i] = toupper ((guchar) password[i]);
 * The LanManager algorithm needs ASCII upper case. In tr_TR.UTF-8 /
 * az_AZ.UTF-8 glibc leaves 'i' unchanged, so the DES key - and thus the LM
 * response - differs from what the server computes for the same password.
 *
 * The function is static, so this program runs the same loop (copied from
 * the scanned commit) next to the locale-independent g_ascii_toupper().
 * dotless rates this site "low" (it cannot see that the buffer is a hash
 * input); it was picked up while reviewing low findings.
 */
#include <ctype.h>
#include <locale.h>
#include <stdio.h>
#include <string.h>
#include <glib.h>

static void
show (const char *label, const unsigned char *buf)
{
  printf ("%-18s", label);
  for (int i = 0; i < 14; i++)
    printf ("%02x", buf[i]);
  printf ("  \"%.14s\"\n", buf);
}

int
main (void)
{
  const char *password = "admin1";
  unsigned char lm_password[15], expected[15];
  int i;

  setlocale (LC_ALL, "");

  /* Same loop as ntlm_lanmanager_hash(). */
  for (i = 0; i < 14 && password && password[i]; i++)
    lm_password[i] = toupper ((unsigned char) password[i]);
  for (; i < 15; i++)
    lm_password[i] = '\0';

  for (i = 0; i < 14 && password[i]; i++)
    expected[i] = g_ascii_toupper (password[i]);
  for (; i < 15; i++)
    expected[i] = '\0';

  show ("toupper():", lm_password);
  show ("g_ascii_toupper():", expected);
  printf ("LM key input %s\n", memcmp (lm_password, expected, 15) == 0 ? "matches" : "DIFFERS");
  return 0;
}
