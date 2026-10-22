"""Turn probe output (results.tsv) into a Markdown table.

A row is marked locale-dependent when the result under any Turkic locale
differs from the C.UTF-8 result.
"""

import collections
import sys

TURKIC = ("tr_", "az_")

rows = collections.OrderedDict()
locales = []
for line in open(sys.argv[1], encoding="ascii"):
    lang, api, loc, result = line.rstrip("\n").split("\t")
    rows.setdefault((lang, api), {})[loc] = result
    if loc not in locales:
        locales.append(loc)

print("| Language | API | " + " | ".join(locales) + " | Locale-dependent? |")
print("|---" * (len(locales) + 3) + "|")
for (lang, api), res in rows.items():
    base = res.get("C.UTF-8")
    dep = any(
        loc.startswith(TURKIC) and r != base and r != "FAILED" for loc, r in res.items()
    )
    cells = [f"`{res.get(l, '-')}`" for l in locales]
    api = api.replace("|", "\\|")
    print(f"| {lang} | `{api}` | " + " | ".join(cells) + f" | {'**YES**' if dep else 'no'} |")
