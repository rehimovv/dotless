| Language | API | C.UTF-8 | tr_TR.UTF-8 | az_AZ.UTF-8 | Locale-dependent? |
|---|---|---|---|---|---|
| c | `tolower('I')` | `i` | `i` | `i` | no |
| c | `toupper('i')` | `I` | `I` | `I` | no |
| c | `tolower() loop on "INTEGER"` | `integer` | `integer` | `integer` | no |
| c | `toupper() loop on "integer"` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| c | `strcasecmp("INTEGER", "integer")` | `equal` | `equal` | `equal` | no |
| c | `strncasecmp("FILE", "file", 4)` | `equal` | `equal` | `equal` | no |
| c | `towlower(L'I')` | `U+0069` | `U+0069` | `U+0069` | no |
| c | `towupper(L'i')` | `U+0049` | `U+0049` | `U+0049` | no |
| c | `wcscasecmp(L"INTEGER", L"integer")` | `equal` | `equal` | `equal` | no |
| c | `isupper('I') (control)` | `y` | `y` | `y` | no |
| python | `str.lower()` | `integer` | `integer` | `integer` | no |
| python | `str.upper()` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| python | `str.casefold()` | `integer` | `integer` | `integer` | no |
| python | `bytes.lower()` | `integer` | `integer` | `integer` | no |
| python | `bytes.upper()` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| python | `re.IGNORECASE (str)` | `match` | `match` | `match` | no |
| python | `re.IGNORECASE\|re.LOCALE (bytes)` | `match` | `match` | `match` | no |
| python | `locale.strxfrm order I<i` | `True` | `True` | `True` | no |
| python | `GLib via gi` | `unavailable (No module named 'gi')` | `unavailable (No module named 'gi')` | `unavailable (No module named 'gi')` | no |
