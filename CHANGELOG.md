# Changelog

All notable changes to this project are documented in this file. The format
is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-24

First release.

### Added

- `dotless scan` for C/C++, Vala, Python, JavaScript (gjs) and Rust, with a
  lexer that ignores comments and string contents.
- Nine rules (DL001–DL009), each backed by measurements under `C.UTF-8`,
  `tr_TR.UTF-8`, `az_AZ.UTF-8` and `tr_TR.ISO-8859-9` on glibc
  (`docs/research.md`).
- Severity analysis: **high** when the result is compared with an ASCII
  constant containing the affected letter, or used as a lookup key; findings
  that compare only with constants without i/I are not reported.
- Output formats: text, JSON, SARIF 2.1.0 and GitLab Code Quality.
- `[tool.dotless]` configuration in `pyproject.toml` (`exclude`,
  `min-severity`, `disable`; Python 3.11+).
- `--disable`, `--color`, `--force-exclude`, `--config`, `--no-config` and
  `--exit-zero` options; exit status 0/1/2.
- Inline suppression with `dotless: ignore`, `dotless: ignore[RULE]` and
  `dotless: ignore-file`.
- `dotless run -- COMMAND` to compare a program's output under Turkish and
  Azerbaijani locales with `C.UTF-8`.
- pre-commit hook, GitLab CI template and GitHub Actions example.

[1.0.0]: https://gitlab.com/rehimovv/dotless/-/releases/v1.0.0
