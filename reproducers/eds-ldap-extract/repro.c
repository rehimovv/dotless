/* evolution-data-server: openldap-extract.h schema and URL parsing in
 * Turkic locales.
 *
 * ldap_str2objectclass() matches the AUXILIARY keyword with
 * strcasecmp (sval, "AUXILIARY"), and ldap_url_parse() matches the scheme
 * with strncasecmp (p, "ldapi://", 8). Both fail for a different-case
 * spelling in tr_TR.UTF-8 / az_AZ.UTF-8.
 *
 * Compiles the real header from evolution-data-server (fetched at the
 * scanned commit by run.sh). Note: e-book-backend-ldap.c only includes this
 * header when building against Sun LDAP (#ifdef SUNLDAP).
 */
#include <locale.h>
#include <stdio.h>
#include <stdlib.h>
#include <glib.h>

/* Normally provided by <ldap.h>. */
#define LDAP_SCOPE_BASE     0
#define LDAP_SCOPE_ONELEVEL 1
#define LDAP_SCOPE_SUBTREE  2

#include "openldap-extract.h"

static const char *
kind_name (int kind)
{
  switch (kind)
    {
    case LDAP_SCHEMA_ABSTRACT: return "ABSTRACT";
    case LDAP_SCHEMA_STRUCTURAL: return "STRUCTURAL";
    case LDAP_SCHEMA_AUXILIARY: return "AUXILIARY";
    default: return "?";
    }
}

int
main (void)
{
  const char *classes[] = {
    "( 1.3.6.1.4.1.42.2.27.4.2.1 NAME 'javaContainer' AUXILIARY MUST cn )",
    "( 1.3.6.1.4.1.42.2.27.4.2.1 NAME 'javaContainer' auxiliary MUST cn )",
  };
  const char *urls[] = { "ldapi://%2fvar%2frun%2fslapd.sock/", "LDAPI://%2fvar%2frun%2fslapd.sock/" };

  setlocale (LC_ALL, "");

  for (gsize i = 0; i < G_N_ELEMENTS (classes); i++)
    {
      int code = 0;
      const char *err = NULL;
      LDAPObjectClass *oc = ldap_str2objectclass (classes[i], &code, &err, 0);

      if (oc)
        printf ("objectclass %s: kind %s\n", i ? "auxiliary" : "AUXILIARY", kind_name (oc->oc_kind));
      else
        printf ("objectclass %s: parse error %d at \"%s\"\n", i ? "auxiliary" : "AUXILIARY", code, err ? err : "");
      if (oc)
        ldap_objectclass_free (oc);
    }

  for (gsize i = 0; i < G_N_ELEMENTS (urls); i++)
    {
      LDAPURLDesc *lud = NULL;
      int rc = ldap_url_parse (urls[i], &lud);

      printf ("ldap_url_parse(%s): rc=%d%s\n", i ? "LDAPI://" : "ldapi://", rc,
              rc == 0 ? " (ok)" : " (error)");
      if (lud)
        ldap_free_urldesc (lud);
    }
  return 0;
}
