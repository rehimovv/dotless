import io
import pathlib
import re

import pytest

from dotless import cli, config
from dotless.scanner import EXTENSIONS

ROOT = pathlib.Path(__file__).parent.parent
BAD_C = 'int f (const char *s) { return strcasecmp (s, "ini") == 0; }\n'
BAD_TOUPPER = "int g (int c) { return toupper (c) == 'I'; }\n"
needs_tomllib = pytest.mark.skipif(config.tomllib is None, reason="needs Python 3.11+")


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.c").write_text(BAD_C)
    (tmp_path / "src" / "b.c").write_text(BAD_TOUPPER)
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "v.c").write_text(BAD_C)
    return tmp_path


def run(capsys, *argv):
    rc = cli.main(list(argv))
    out = capsys.readouterr()
    return rc, out.out, out.err


def test_version(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["--version"])
    assert e.value.code == 0
    assert re.fullmatch(r"dotless \d+\.\d+\.\d+\n", capsys.readouterr().out)


def test_exit_codes(project, capsys):
    assert run(capsys, "scan", "src/a.c")[0] == 1
    (project / "ok.c").write_text("int x;\n")
    assert run(capsys, "scan", "ok.c")[0] == 0
    assert run(capsys, "scan", "--exit-zero", "src")[0] == 0
    assert run(capsys, "scan", "missing")[0] == 2
    rc, _, err = run(capsys, "scan", "--disable", "DL999", "src")
    assert rc == 2 and "unknown rule" in err
    with pytest.raises(SystemExit) as e:
        cli.main(["scan", "--format", "xml", "src"])
    assert e.value.code == 2


def test_disable_rule(project, capsys):
    rc, out, _ = run(capsys, "scan", "--disable", "DL002", "src")
    assert rc == 1 and "DL002" not in out and "DL001" in out
    assert run(capsys, "scan", "--disable", "DL001", "--disable", "DL002", "src")[0] == 0


def test_color(project, capsys, monkeypatch):
    assert "\033[" in run(capsys, "scan", "--color", "always", "src")[1]
    assert "\033[" not in run(capsys, "scan", "--color", "never", "src")[1]
    # auto: pytest captures stdout, which is not a terminal
    assert "\033[" not in run(capsys, "scan", "src")[1]


def test_use_color_auto():
    class Tty(io.StringIO):
        def isatty(self):
            return True

    assert cli.use_color("auto", Tty())
    assert not cli.use_color("auto", io.StringIO())
    assert cli.use_color("never", Tty()) is False


def test_no_color_env(monkeypatch):
    class Tty(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setenv("NO_COLOR", "1")
    assert not cli.use_color("auto", Tty())
    assert cli.use_color("always", Tty())


def test_force_exclude_for_named_files(project, capsys):
    assert run(capsys, "scan", "--exclude", "vendor", "vendor/v.c")[0] == 1
    assert run(capsys, "scan", "--exclude", "vendor", "--force-exclude", "vendor/v.c")[0] == 0
    assert run(capsys, "scan", "--exclude", "*.c", "--force-exclude", "src/a.c")[0] == 0


@needs_tomllib
def test_config_from_pyproject(project, capsys):
    (project / "pyproject.toml").write_text(
        '[tool.dotless]\nexclude = ["vendor"]\nmin-severity = "high"\ndisable = ["DL001"]\n'
    )
    rc, out, _ = run(capsys, "scan", ".")
    assert rc == 1
    assert "vendor" not in out and "DL001" not in out and "src/a.c" in out
    # command line options win
    rc, out, _ = run(capsys, "scan", "--no-config", ".")
    assert "vendor/v.c" in out and "DL001" in out


@needs_tomllib
def test_config_found_in_parent_directory(project, capsys, monkeypatch):
    (project / "pyproject.toml").write_text('[tool.dotless]\ndisable = ["DL002"]\n')
    monkeypatch.chdir(project / "src")
    rc, out, _ = run(capsys, "scan", "a.c")
    assert rc == 0


@needs_tomllib
@pytest.mark.parametrize(
    "body,message",
    [
        ('[tool.dotless]\nexclud = ["x"]\n', "unknown key"),
        ('[tool.dotless]\nmin-severity = "medium"\n', "min-severity"),
        ('[tool.dotless]\ndisable = ["DL999"]\n', "unknown rule"),
        ('[tool.dotless]\nexclude = "vendor"\n', "list of strings"),
        ("[tool.dotless\n", "pyproject.toml"),
    ],
)
def test_config_errors(project, capsys, body, message):
    (project / "pyproject.toml").write_text(body)
    rc, _, err = run(capsys, "scan", "src")
    assert rc == 2 and message in err


def test_explicit_config_file(project, capsys):
    (project / "other.toml").write_text('[tool.dotless]\ndisable = ["DL001", "DL002"]\n')
    rc = run(capsys, "scan", "--config", "other.toml", "src")[0]
    assert rc == (0 if config.tomllib else 1)
    assert run(capsys, "scan", "--config", "nope.toml", "src")[0] == 2


def test_config_ignored_without_tomllib(project, capsys, monkeypatch):
    monkeypatch.setattr(config, "tomllib", None)
    (project / "pyproject.toml").write_text('[tool.dotless]\ndisable = ["DL001", "DL002"]\n')
    rc, _, err = run(capsys, "scan", "src")
    assert rc == 1 and "needs Python 3.11" in err


def test_pyproject_without_table_is_fine(project, capsys):
    (project / "pyproject.toml").write_text('[project]\nname = "x"\n')
    assert run(capsys, "scan", "src")[0] == 1


def test_unreadable_file_is_reported(project, capsys, monkeypatch):
    import builtins

    real_open = builtins.open

    def fake_open(path, *a, **kw):
        if str(path).endswith("b.c"):
            raise PermissionError(13, "Permission denied")
        return real_open(path, *a, **kw)

    monkeypatch.setattr(builtins, "open", fake_open)
    rc, out, err = run(capsys, "scan", "src")
    assert rc == 1 and "cannot read" in err and "b.c" in err


def test_unwritable_output(project, capsys):
    assert run(capsys, "scan", "-o", str(project / "no" / "such" / "dir.txt"), "src")[0] == 2


def test_pre_commit_hook_matches_supported_extensions():
    text = (ROOT / ".pre-commit-hooks.yaml").read_text()
    files = re.search(r"files: '(.+)'", text).group(1)
    for ext in EXTENSIONS:
        assert re.search(files, "x" + ext), ext
    assert not re.search(files, "x.txt")
    assert "--force-exclude" in text
