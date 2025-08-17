# Coverage with pytest

To enable coverage in CI and locally, add this to your `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-q --cov=src/sqlcanon --cov-report=term-missing --cov-fail-under=85"
```

and install pytest-cov:

```bash
pip install pytest-cov
```