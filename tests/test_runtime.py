import sys

from dotless import runtime

ECHO_LOCALE = [sys.executable, "-c", "import os; print(os.environ['LC_ALL'][:2], os.environ['LANGUAGE'])"]


def test_env_for_sets_locale_and_keeps_messages_untranslated():
    env = runtime.env_for("tr_TR.UTF-8")
    assert env["LC_ALL"] == env["LANG"] == "tr_TR.UTF-8"
    assert env["LANGUAGE"] == "en"


def test_identical_runs_have_no_report():
    a = runtime.Result("C.UTF-8", 0, "integer\n", "")
    assert runtime.compare(a, runtime.Result("tr_TR.UTF-8", 0, "integer\n", "")) == []


def test_turkic_letters_are_pointed_out():
    a = runtime.Result("C.UTF-8", 0, "integer\n", "")
    b = runtime.Result("tr_TR.UTF-8", 1, "ınteger\n", "")
    report = "\n".join(runtime.compare(a, b))
    assert "exit status" in report and "ı" in report and "Turkic case mapping" in report


def test_run_once_passes_locale():
    res = runtime.run_once(ECHO_LOCALE, "tr_TR.UTF-8", 30, None)
    assert res.returncode == 0 and res.stdout.split() == ["tr", "en"]


def test_run_once_missing_command():
    assert runtime.run_once(["dotless-no-such-command"], "C.UTF-8", 5, None).error


def test_run_compare_detects_difference(monkeypatch, capsys):
    monkeypatch.setattr(runtime, "available_locales", lambda: None)
    assert runtime.run_compare(ECHO_LOCALE, ["tr_TR.UTF-8"], "C.UTF-8", 30, None) == 1
    assert "differs" in capsys.readouterr().out


def test_run_compare_same_output(monkeypatch, capsys):
    monkeypatch.setattr(runtime, "available_locales", lambda: None)
    cmd = [sys.executable, "-c", "print('same')"]
    assert runtime.run_compare(cmd, ["tr_TR.UTF-8"], "C.UTF-8", 30, None) == 0


def test_missing_locale_is_reported(monkeypatch, capsys):
    monkeypatch.setattr(runtime, "available_locales", lambda: {"c.utf8"})
    assert runtime.run_compare(ECHO_LOCALE, ["tr_TR.UTF-8"], "C.UTF-8", 30, None) == 2
    assert "localedef -i tr_TR -f UTF-8" in capsys.readouterr().err
