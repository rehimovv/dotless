#!/bin/sh
# Build every probe that has a toolchain available and run it under each
# locale. Writes out/results.tsv and out/results.md.
set -eu
cd "$(dirname "$0")"
mkdir -p out
: > out/results.tsv

LOCALES=${LOCALES:-"C.UTF-8 en_US.UTF-8 tr_TR.UTF-8 az_AZ.UTF-8 tr_TR.ISO-8859-9"}

run() {
    for l in $LOCALES; do
        LC_ALL=$l LANG=$l "$@" "$l" >> out/results.tsv || true
    done
}

if command -v cc >/dev/null; then
    if pkg-config --exists glib-2.0 2>/dev/null; then
        cc -std=c99 -D_GNU_SOURCE -DHAVE_GLIB probe.c -o out/probe-c $(pkg-config --cflags --libs glib-2.0)
    else
        cc -std=c99 -D_GNU_SOURCE probe.c -o out/probe-c
    fi
    run ./out/probe-c
fi
if command -v valac >/dev/null; then
    valac -q probe.vala -o out/probe-vala
    run ./out/probe-vala
fi
command -v python3 >/dev/null && run python3 probe.py
command -v node >/dev/null && run node probe.js
command -v gjs >/dev/null && run gjs probe.js
if command -v cargo >/dev/null; then
    (cd rust-probe && cargo build -q --release ${RUST_FEATURES:+--features "$RUST_FEATURES"})
    run ./rust-probe/target/release/rust-probe
fi

python3 table.py out/results.tsv > out/results.md
cat out/results.md
