# Contributing

Bug reports, false-positive reports and merge requests are welcome on
[GitLab](https://gitlab.com/rehimovv/dotless) (the GitHub repository is a
mirror).

## Running the tests

```bash
pip install -e '.[test]'
pytest
```

dotless has no runtime dependencies and supports Python 3.9 to 3.13; CI runs
the tests on all of them.

## Reporting a false positive

Please include the smallest piece of code that triggers the finding and the
`dotless` output. A false positive usually becomes a fixture in
`tests/fixtures/<language>/safe.*` plus a fix in `analysis.py` or
`scanner.py`.

## Adding a rule

1. **Measure first.** Every rule must be backed by a measurement, not by
   documentation. Add the call to the matching probe in `research/`
   (`probe.c`, `probe.vala`, `probe.py`, `probe.js` or `rust-probe/`) and run
   the `research:glibc` CI job (or `research/run.sh` on a glibc system with
   `tr_TR.UTF-8` and `az_AZ.UTF-8` generated). Only calls whose output differs
   between `C.UTF-8` and a Turkic locale get a rule.
2. Update the tables in `docs/research.md` with the new results.
3. Add the rule to `src/dotless/rules.py` and a matcher to
   `src/dotless/scanner.py`.
4. Add at least one positive case to `tests/fixtures/<language>/bad.*`
   (with an `EXPECT DLxxx high|low` marker on the line) and one negative case
   to `safe.*`. `tests/test_rules.py` checks that every rule has both.
5. Document the rule in `docs/rules.md` and the README table, and add a
   line to `CHANGELOG.md`.

## Commits

Small commits with a short imperative subject ("Add C towlower rule") are
easiest to review.
