# Contributing to `blackcortex-gpt-cli`

Welcome! 🎉 Whether you're fixing bugs, proposing features, or submitting code — your contributions help shape a better terminal AI experience.

This project is a terminal-based conversational assistant powered by OpenAI, featuring persistent memory, markdown rendering, streaming responses, and local tool integration.

---

## 🧰 Development Setup

### 1. Clone and Set Up

```bash
git clone https://github.com/BlackCortexAgent/blackcortex-gpt-cli.git
cd blackcortex-gpt-cli
make dev
```

> This sets up a `.venv`, installs all dev dependencies, and configures pre-commit hooks.

### 2. Activate the Environment

#### 🖥️ In your terminal:

```bash
source .venv/bin/activate
```

#### 🧠 In **Visual Studio Code**:

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
2. Search: `Python: Select Interpreter`
3. Choose the one that ends in:

   ```
   .venv/bin/python
   ```

> If you don't see it, click `Enter interpreter path...` and manually browse to `.venv/bin/python`.

✅ This ensures linting, test discovery, and debugging all use your virtualenv.

---

## 🧪 Run Tests

Run all tests using:

```bash
make ci-test
```

Tests are powered by `pytest` with `pytest-testdox` for human-readable output.

---

## 🧼 Linting and Formatting

We enforce clean code with:

- [`ruff`](https://docs.astral.sh/ruff/) (auto-formatting, linting)
- `pylint` (static analysis)

### Format:

```bash
make format
```

### Lint:

```bash
make lint
```

---

## ✅ Pre-Commit Checks

We use [pre-commit](https://pre-commit.com) to run formatting and code quality checks automatically:

```bash
pre-commit install
```

To run all checks manually:

```bash
pre-commit run --all-files
```

---

## 🔁 Local CI Check

Run a full validation before a commit or release:

```bash
make check
```

This runs:

- Linting (requires pylint ≥ 9.0)
- Tests
- Coverage enforcement (≥ 90%)
- Build and validate with Twine

---

## ✏️ Contribution Guidelines

- Add or update tests under `tests/`
- Run `make format && make lint` before pushing your changes

---

## 🚀 CI/CD

GitHub Actions automatically:

- Lint and test every PR (`check.yml`)
- Build and publish tagged releases to PyPI (`publish.yml`)

You can replicate the release check locally with:

```bash
make ci-release-venv
```

---

## 📜 License

By contributing, you agree that your code will be released under the [MIT License](LICENSE).

---

## 🙏 Thanks

Every PR, issue, or suggestion improves `blackcortex-gpt-cli`. We appreciate your help in making this better for everyone.
