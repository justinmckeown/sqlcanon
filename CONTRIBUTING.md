# 🤝 Contributing to `sqlcanon`

Thanks for your interest in improving `sqlcanon`! This guide covers **how to work on the project**, coding standards, and what we expect in pull requests. It complements the main `README.md`, which explains **what the project does** and how to **use** it.

---

## 🧭 Where to start

- **Good first issues:** small refactors, test gaps, docs improvements.
- **Feature ideas:** open an issue first to discuss design/impact before coding.
- **Bug reports:** include steps to reproduce, expected vs. actual behaviour, and environment info.

> Tip: If you're adding a new normalization pass, see the “Passes” section below for a step‑by‑step checklist.

---

## 🛠️ Dev Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e .[dev]
```

Sanity checks:
```bash
ruff check .
mypy src/sqlcanon
pytest -q
```

---

## 🧩 Project Layout (recap)

```
src/sqlcanon/
  __init__.py
  protocols.py
  parsing/
  passes/
  hashing/
  config/
  cli/
tests/
```

- **Library code** lives under `src/sqlcanon`.
- **Tests** mirror the package structure under `tests`.

---

## 🧪 Testing Guidelines

- Prefer **unit tests** close to the code under test.
- Add **regression tests** for any bug you fix.
- For new passes, include:
  - Behaviour tests (what the pass does)
  - **Idempotence** test: running the pass twice doesn’t change the result
  - **Safety** test: pass does not trigger on unsupported/ambiguous cases
- Use **temporary files/dirs** via `tmp_path` where needed.
- Keep test names descriptive: `test_<module>_<behaviour>()`.

Run tests:
```bash
pytest -q
```

---

## 🧹 Style & Quality

- **Imports & style**: `ruff check . --fix`
- **Formatting**: `ruff format .`
- **Types**: `mypy src/sqlcanon` (be conservative; prefer explicit `list[str]`, `X | None`)
- **Docstrings**: public classes/functions should have short docstrings with examples when helpful.

Ruff config lives in `pyproject.toml` (`[tool.ruff]` and `[tool.ruff.lint]`).

---

## 🌱 Adding a New Normalization Pass

1. Create a file in `src/sqlcanon/passes/`, e.g. `my_new_pass.py`.
2. Implement the **interface**:
   ```python
   from ..protocols import AstNode
   from ..config.model import Config
   from .base import BasePass

   class MyNewPass(BasePass):
       name = "my_new_pass"
       def apply(self, ast: AstNode, cfg: Config) -> AstNode:
           # transform ast.text conservatively and deterministically
           return AstNode(ast.text)
   ```
3. Register it in `_PASS_REGISTRY` in `src/sqlcanon/__init__.py`:
   ```python
   from .passes.my_new_pass import MyNewPass
   _PASS_REGISTRY["my_new_pass"] = MyNewPass
   ```
4. Add tests in `tests/test_passes_<name>.py` covering behaviour, idempotence, and safety.
5. (Optional) Document the pass in the README’s “Pass Catalog”.

**Design principles:**
- **Determinism**: same input → same output (order, spacing, placeholders).
- **Conservatism**: avoid transforms that can change semantics (e.g., reordering with `OR` at top level).
- **Isolation**: a pass should do one job (SRP) and compose cleanly with others.

---

## 🔒 Security & Safety Notes

- Treat all input SQL as **untrusted text** — never execute queries.
- Keep transforms **structure‑aware** where possible; be explicit about “safe vs. aggressive” behaviour.
- Consider adding fuzz/property tests for parsers or regex‑heavy logic.

---

## 🌿 Branching & Commits

- Branch from `main`: `feat/<short-desc>`, `fix/<short-desc>`, `docs/<short-desc>`.
- Use clear commit messages. Conventional Commits are welcome but not required:
  - `feat: add normalize_literals pass`
  - `fix: prevent predicate reordering when OR present`
  - `test: add idempotence tests for sort_in_list`

---

## ✅ Pull Request Checklist

- [ ] Tests added/updated and passing locally (`pytest -q`)
- [ ] Lint & format clean (`ruff check .`, `ruff format .`)
- [ ] Types pass (`mypy src/sqlcanon`)
- [ ] README/docs updated if behaviour is user‑visible
- [ ] Clear description of motivation, approach, and trade‑offs

> Keep PRs focused and small where possible. If the change is large, split it into reviewable chunks.

---

## 📦 Releases (maintainers)

- Update version in `pyproject.toml` (follow semver).
- Tag the release: `git tag -a v0.x.y -m "Release v0.x.y" && git push --tags`
- (Optional) Build & publish to PyPI when ready.

---

## 🧑‍⚖️ Code of Conduct

Be kind, constructive, and respectful. By participating, you agree to foster a welcoming community. If you’d like a formal document, add `CODE_OF_CONDUCT.md` (Contributor Covenant is widely used).

---

## 🙌 Thanks

Your improvements make `sqlcanon` better for everyone. Thank you for contributing!
