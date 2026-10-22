#!/bin/sh
# Build and run every reproducer under C.UTF-8, tr_TR.UTF-8 and az_AZ.UTF-8.
# Expects Debian with the packages listed in .gitlab-ci.yml (reproducers job).
set -eu
cd "$(dirname "$0")"
EDS_COMMIT=${EDS_COMMIT:-e3d4270d1f61a48f0b428b3e2899ae6a320438eb}
mkdir -p out
GLIB="$(pkg-config --cflags --libs glib-2.0)"

dpkg-query -W -f='evolution-data-server ${Version}\n' evolution-data-server || true

RAW="https://gitlab.gnome.org/GNOME/evolution-data-server/-/raw/$EDS_COMMIT/src"

# Copied code must still match the scanned commit.
check_copied() {
    curl -fsSL -o "out/$(basename "$2")" "$RAW/$2"
    if grep -qF "$3" "out/$(basename "$2")"; then
        echo "copied code still present in $2: $3"
    else
        echo "copied code NOT found in $2: $3"; exit 1
    fi
}
check_copied imapx camel/providers/imapx/camel-imapx-input-stream.c "toupper (p[1]) == 'I' &&"
check_copied imapx camel/providers/imapx/camel-imapx-input-stream.c "toupper (token[1]) == 'I' &&"
check_copied ntlm camel/camel-sasl-ntlm.c "lm_password[i] = toupper ((guchar) password[i]);"

cc -o out/imapx eds-imapx-nil/repro.c

curl -fsSL -o out/openldap-extract.h \
  "https://gitlab.gnome.org/GNOME/evolution-data-server/-/raw/$EDS_COMMIT/src/addressbook/backends/ldap/openldap-extract.h"
cc -w -Iout -o out/ldap eds-ldap-extract/repro.c $GLIB

cc -o out/ntlm eds-ntlm-lm/repro.c $GLIB

for r in imapx ldap ntlm; do
    for l in C.UTF-8 tr_TR.UTF-8 az_AZ.UTF-8; do
        echo "== $r @ $l"
        LC_ALL=$l ./out/$r || echo "(exit $?)"
    done
done
