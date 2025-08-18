from typer.testing import CliRunner

from sqlcanon.cli.main import app

runner = CliRunner()


def test_cli_normalise_ok():
    res = runner.invoke(app, ["normalise", "select * from t where a in (2,1) and b=1"])
    assert res.exit_code == 0
    assert "SELECT * FROM t WHERE a IN" in res.stdout


def test_cli_keyword_case_lower():
    res = runner.invoke(app, ["normalise", "-k", "lower", "SELECT A FROM T"])
    assert res.exit_code == 0
    assert "select a from t" in res.stdout.lower()


def test_cli_keyword_case_bad_value():
    res = runner.invoke(app, ["normalise", "-k", "Mixed", "select 1"])
    assert res.exit_code != 0
    assert "keyword-case must be 'upper' or 'lower'" in (res.stdout + res.stderr)
