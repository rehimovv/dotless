#!/bin/sh
# Build and run every reproducer under C.UTF-8, tr_TR.UTF-8 and az_AZ.UTF-8.
# Expects Debian with the packages listed in .gitlab-ci.yml (reproducers job).
set -eu
cd "$(dirname "$0")"
EDS_COMMIT=${EDS_COMMIT:-e3d4270d1f61a48f0b428b3e2899ae6a320438eb}
mkdir -p out
GLIB="$(pkg-config --cflags --libs gio-2.0)"

dpkg-query -W -f='evolution-data-server ${Version}\n' evolution-data-server || true

cc -o out/imapx eds-imapx-nil/repro.c $GLIB -ldl
IMAPX=$(find /usr/lib -name libcamelimapx.so | head -1)

curl -fsSL -o out/openldap-extract.h \
  "https://gitlab.gnome.org/GNOME/evolution-data-server/-/raw/$EDS_COMMIT/src/addressbook/backends/ldap/openldap-extract.h"
cc -w -Iout -o out/ldap eds-ldap-extract/repro.c $GLIB

cc -o out/ntlm eds-ntlm-lm/repro.c $GLIB

for r in "imapx $IMAPX" ldap ntlm; do
    set -- $r
    for l in C.UTF-8 tr_TR.UTF-8 az_AZ.UTF-8; do
        echo "== $1 @ $l"
        LC_ALL=$l REPRO_DEBUG=${REPRO_DEBUG:-} ./out/"$@" || echo "(exit $?)"
    done
done
