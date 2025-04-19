# Contributing to `blackcortex-gpt-cli`

Welcome! 🎉 Whether you're reporting bugs, proposing features, or submitting code — your contributions make this project better.

This project is a terminal-based conversational assistant powered by OpenAI, with persistent memory, markdown rendering, and streaming support.

---

## 🧰 Development Setup

### 1. Clone and Install

```bash
git clone https://github.com/BlackCortexAgent/blackcortex-gpt-cli.git
cd blackcortex-gpt-cli
make install
```

> This creates a `.venv`, installs dependencies, and sets up pre-commit hooks.

### 2. Activate the Virtual Environment

```bash
source .venv/bin/activate
```

---

## 🧪 Testing

Run the full test suite with:

```bash
make test
```

Tests use `pytest` with `pytest-testdox` for clean, readable output.

---

## 🧼 Linting and Formatting

We use [Ruff](https://docs.astral.sh/ruff/) and `pylint` for code quality and formatting.

### Auto-format code:

```bash
make format
```

### Run linter:

```bash
make lint
```

---

## ✅ Full Local Check

To run all checks before a commit or release:

```bash
make check
```

This runs lint, tests, builds the package, and validates it with Twine.

---

## 🪝 Pre-commit Hooks

We use [pre-commit](https://pre-commit.com) to enforce formatting and standards:

```bash
pre-commit install
```

Run hooks manually with:

```bash
pre-commit run --all-files
```

---

## ✏️ Making Contributions

- Add or update tests in the `tests/` directory
- Follow CLI structure in `gpt.py` and `commands.py`
- Use `config.py` for environment-based settings
- Use `memory.py` for memory logic (persistent JSON + summarization)
- Run `make format && make lint` before submitting your PR

---

## 🚀 CI/CD

Our GitHub Actions workflows ensure:

- Every PR is linted, tested, and validated (`check.yml`)
- Tagged releases are built and published to PyPI (`publish.yml`)
- Contributors can run CI logic locally using:

```bash
make ci-release
```

---

## 📜 Licensing

By contributing, you agree that your code is licensed under the [MIT License](LICENSE).

---

## 🙏 Thank You

We appreciate every issue, suggestion, and PR. Thank you for helping improve `blackcortex-gpt-cli`!
