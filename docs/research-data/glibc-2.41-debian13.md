| Language | API | C.UTF-8 | en_US.UTF-8 | tr_TR.UTF-8 | az_AZ.UTF-8 | tr_TR.ISO-8859-9 | Locale-dependent? |
|---|---|---|---|---|---|---|---|
| c | `tolower('I')` | `i` | `i` | `I` | `I` | `\xfd` | **YES** |
| c | `toupper('i')` | `I` | `I` | `i` | `i` | `\xdd` | **YES** |
| c | `tolower() loop on "INTEGER"` | `integer` | `integer` | `Integer` | `Integer` | `\xfdnteger` | **YES** |
| c | `toupper() loop on "integer"` | `INTEGER` | `INTEGER` | `iNTEGER` | `iNTEGER` | `\xddNTEGER` | **YES** |
| c | `strcasecmp("INTEGER", "integer")` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `strncasecmp("FILE", "file", 4)` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `strcasestr("MIME-INFO", "info") != NULL` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `towlower(L'I')` | `U+0069` | `U+0069` | `U+0131` | `U+0131` | `U+0131` | **YES** |
| c | `towupper(L'i')` | `U+0049` | `U+0049` | `U+0130` | `U+0130` | `U+0130` | **YES** |
| c | `wcscasecmp(L"INTEGER", L"integer")` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `isupper('I') (control)` | `y` | `y` | `y` | `y` | `y` | no |
| c | `g_utf8_strdown("INTEGER")` | `integer` | `integer` | `\xc4\xb1nteger` | `\xc4\xb1nteger` | `\xc4\xb1nteger` | **YES** |
| c | `g_utf8_strup("integer")` | `INTEGER` | `INTEGER` | `\xc4\xb0NTEGER` | `\xc4\xb0NTEGER` | `\xc4\xb0NTEGER` | **YES** |
| c | `g_utf8_casefold("INTEGER")` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| c | `g_unichar_tolower('I')` | `U+0069` | `U+0069` | `U+0069` | `U+0069` | `U+0069` | no |
| c | `g_unichar_toupper('i')` | `U+0049` | `U+0049` | `U+0049` | `U+0049` | `U+0049` | no |
| c | `g_ascii_strdown("INTEGER")` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| c | `g_ascii_strup("integer")` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| c | `g_ascii_tolower('I')` | `i` | `i` | `i` | `i` | `i` | no |
| c | `g_ascii_toupper('i')` | `I` | `I` | `I` | `I` | `I` | no |
| c | `g_ascii_strcasecmp("INTEGER", "integer")` | `equal` | `equal` | `equal` | `equal` | `equal` | no |
| c | `g_ascii_strncasecmp("FILE", "file", 4)` | `equal` | `equal` | `equal` | `equal` | `equal` | no |
| c | `g_strcasecmp("INTEGER", "integer") [deprecated]` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `g_strncasecmp("FILE", "file", 4) [deprecated]` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| c | `g_strdown("INTEGER") [deprecated]` | `integer` | `integer` | `Integer` | `Integer` | `\xfdnteger` | **YES** |
| c | `g_strup("integer") [deprecated]` | `INTEGER` | `INTEGER` | `iNTEGER` | `iNTEGER` | `\xddNTEGER` | **YES** |
| c | `g_str_match_string("integer", "INTEGER", FALSE)` | `equal` | `equal` | `equal` | `equal` | `equal` | no |
| c | `sign(g_utf8_collate("integer", "INTEGER"))` | `1` | `-1` | `1` | `1` | `1` | no |
| vala | `string.down()` | `integer` | `integer` | `\304\261nteger` | `\304\261nteger` | `\304\261nteger` | **YES** |
| vala | `string.up()` | `INTEGER` | `INTEGER` | `\304\260NTEGER` | `\304\260NTEGER` | `\304\260NTEGER` | **YES** |
| vala | `string.casefold()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| vala | `string.ascii_down()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| vala | `string.ascii_up()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| vala | `string.down() == "integer"` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| vala | `unichar.tolower('I')` | `U+0069` | `U+0069` | `U+0069` | `U+0069` | `U+0069` | no |
| vala | `unichar.toupper('i')` | `U+0049` | `U+0049` | `U+0049` | `U+0049` | `U+0049` | no |
| vala | `string.collate() sign` | `1` | `-1` | `1` | `1` | `1` | no |
| python | `str.lower()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| python | `str.upper()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| python | `str.casefold()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| python | `bytes.lower()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| python | `bytes.upper()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| python | `re.IGNORECASE (str)` | `match` | `match` | `match` | `match` | `match` | no |
| python | `re.IGNORECASE\|re.LOCALE (bytes)` | `match` | `match` | `NO match` | `NO match` | `NO match` | **YES** |
| python | `locale.strxfrm order I<i` | `True` | `False` | `True` | `True` | `True` | no |
| python | `GLib.utf8_strdown() via gi` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| python | `GLib.utf8_strup() via gi` | `INTEGER` | `INTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | **YES** |
| python | `GLib.ascii_strdown() via gi` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| node | `Intl default locale` | `en-US` | `en-US` | `tr-TR` | `az-AZ` | `tr-TR` | **YES** |
| node | `toLowerCase()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| node | `toUpperCase()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| node | `toLocaleLowerCase()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| node | `toLocaleUpperCase()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| node | `toLocaleLowerCase(undefined)` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| node | `toLocaleLowerCase([])` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| node | `toLocaleLowerCase('en-US')` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| node | `toLocaleLowerCase('tr')` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | no |
| node | `localeCompare(..., {sensitivity: 'base'}) === 0` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| node | `/integer/i.test("INTEGER")` | `match` | `match` | `match` | `match` | `match` | no |
| gjs | `Intl default locale` | `en-US` | `en-US` | `tr-TR` | `az-AZ` | `tr-TR` | **YES** |
| gjs | `toLowerCase()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| gjs | `toUpperCase()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| gjs | `toLocaleLowerCase()` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| gjs | `toLocaleUpperCase()` | `INTEGER` | `INTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | **YES** |
| gjs | `toLocaleLowerCase(undefined)` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| gjs | `toLocaleLowerCase([])` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| gjs | `toLocaleLowerCase('en-US')` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| gjs | `toLocaleLowerCase('tr')` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | no |
| gjs | `localeCompare(..., {sensitivity: 'base'}) === 0` | `equal` | `equal` | `NOT equal` | `NOT equal` | `NOT equal` | **YES** |
| gjs | `/integer/i.test("INTEGER")` | `match` | `match` | `match` | `match` | `match` | no |
| gjs | `GLib.utf8_strdown()` | `integer` | `integer` | `\u0131nteger` | `\u0131nteger` | `\u0131nteger` | **YES** |
| gjs | `GLib.utf8_strup()` | `INTEGER` | `INTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | `\u0130NTEGER` | **YES** |
| gjs | `GLib.ascii_strdown()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| rust | `str::to_lowercase()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| rust | `str::to_uppercase()` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | `INTEGER` | no |
| rust | `str::to_ascii_lowercase()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| rust | `str::eq_ignore_ascii_case()` | `equal` | `equal` | `equal` | `equal` | `equal` | no |
| rust | `g_utf8_strdown() without setlocale()` | `integer` | `integer` | `integer` | `integer` | `integer` | no |
| rust | `g_utf8_strdown() after setlocale(LC_ALL, "")` | `integer` | `integer` | `\u{131}nteger` | `\u{131}nteger` | `\u{131}nteger` | **YES** |
