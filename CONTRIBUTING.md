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

> This creates a `.venv`, installs dependencies, and links the CLI.

### 2. Activate Environment

```bash
source .venv/bin/activate
```

---

## 🧪 Testing

Run tests with:

```bash
make test
```

Tests use `pytest` with `pytest-testdox` for clean output.

---

## 🧼 Formatting and Linting

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

### Format code:

```bash
make format
```

### Lint code:

```bash
make lint
```

### Full check (lint + test + build):

```bash
make check
```

---

## ✅ Pre-commit Hooks

Set up [pre-commit](https://pre-commit.com) to enforce formatting and quality before each commit:

```bash
pre-commit install
```

You can run hooks manually with:

```bash
pre-commit run --all-files
```

---

## ✏️ Making Contributions

- Add or update tests in the `tests/` directory
- Follow the existing CLI pattern (see `gpt.py`, `commands.py`)
- Use `config.py` for environment-based settings
- Use `memory.py` for memory logic; it is shared across CLI sessions
- Run `make format` before submitting a PR

---

## 📜 Licensing

All contributions are licensed under the terms of the [MIT License](LICENSE).

---

## 🙏 Thank You

Thank you for contributing to `blackcortex-gpt-cli`!
