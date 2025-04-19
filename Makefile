# === Config ===
VENV_DIR := .venv
VENV_BIN := $(VENV_DIR)/bin
PYTHON := python3

# === Local Development ===

install: ## Setup virtualenv and install dev dependencies
	@echo "🔧 Setting up virtual environment and installing dev dependencies..."
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_BIN)/pip install --upgrade pip setuptools wheel
	$(VENV_BIN)/pip install -e ".[dev]"

postinstall: ## Install pre-commit hooks
	@echo "🪝 Installing pre-commit hooks..."
	$(VENV_BIN)/pre-commit install

dev: install postinstall ## Full setup for local development
	@echo "✅ Dev environment is ready. Run: source .venv/bin/activate"

format: ## Auto-format code
	@echo "🧼 Auto-formatting with Ruff..."
	$(VENV_BIN)/ruff check blackcortex_cli --fix

lint: ## Lint project
	@echo "🔎 Linting..."
	$(VENV_BIN)/pylint blackcortex_cli --fail-under=9.0

test: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	PYTHONPATH=./ $(VENV_BIN)/pytest \
		--cov \
		--cov-report=term-missing \
		--testdox tests

check: lint test ## Run lint + tests + twine check
	@echo "📦 Building (venv)..."
	$(VENV_BIN)/python -m build
	@echo "🔎 Validating (venv)..."
	$(VENV_BIN)/twine check dist/*
	@echo "✅ Check complete."

clean: ## Remove build artifacts and caches
	@echo "🧹 Cleaning up..."
	rm -rf dist build *.egg-info .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.coverage" -delete

uninstall: ## Remove venv and uninstall package
	@echo "🧹 Uninstalling..."
	-$(VENV_BIN)/pip uninstall -y blackcortex-gpt-cli || true
	rm -rf $(VENV_DIR) blackcortex_gpt_cli.egg-info

help: ## Show available targets
	@echo "📖 Available make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# === CI / GitHub Actions ===

ci-release: clean ## CI: Run checks using system Python (no venv)
	@echo "🔍 Linting..."
	pylint blackcortex_cli --fail-under=9.0
	@echo "🧪 Testing with coverage..."
	PYTHONPATH=./ pytest \
		--cov \
		--cov-report=term-missing \
		--testdox tests
	@echo "📦 Building..."
	python -m build
	@echo "🔎 Validating..."
	twine check dist/*

