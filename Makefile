VENV_BIN := .venv/bin

# === Virtual Environment ===
install: ## Create virtualenv and install in editable mode with dev dependencies
	@echo "🔧 Creating virtual environment and installing dependencies..."
	python3 -m venv .venv
	@echo "⬆️  Upgrading pip, setuptools, and wheel..."
	$(VENV_BIN)/pip install --upgrade pip setuptools wheel
	@echo "📦 Installing project in editable mode with dev dependencies..."
	$(VENV_BIN)/pip install -e ".[dev]"
	@echo "🪝 Installing pre-commit hooks..."
	$(VENV_BIN)/pre-commit install

# === Uninstall ===
uninstall: ## Uninstall the editable package and remove egg-info
	@echo "🧹 Uninstalling editable package and cleaning metadata..."
	$(VENV_BIN)/pip uninstall -y blackcortex-gpt-cli || echo "⚠️  Package not found or already uninstalled."
	@echo "🗑️  Removing leftover egg-info..."
	rm -rf blackcortex_gpt_cli.egg-info
	@echo "🔥 Removing virtual environment..."
	rm -rf .venv

# === Formatting ===
format: ## Run Ruff to auto-fix lint issues
	@echo "🧼 Running Ruff to auto-fix formatting issues..."
	ruff check blackcortex_cli --fix

# === Clean, Build, Publish ===
clean: ## Remove build artifacts and cache
	@echo "🧹 Cleaning build artifacts and Python cache..."
	rm -rf dist build *.egg-info \
		__pycache__ .pytest_cache .ruff_cache \
		**/__pycache__ \
		**/*.pyc

build: clean ## Build sdist and wheel into dist/
	@echo "📦 Building source and wheel distribution..."
	python -m build

lint: ## Run Pylint on blackcortex_cli
	@echo "🔎 Running Pylint..."
	$(VENV_BIN)/pylint blackcortex_cli --fail-under=9.0

test: ## Run pytest on the tests/ directory
	@echo "🧪 Running tests..."
	PYTHONPATH=./ $(VENV_BIN)/pytest tests --testdox

check: lint test build ## Lint, test, build, and validate distributions
	@echo "✅ Running full project check (lint, test, build, validate)..."
	twine check dist/*

# === CI ===
ci: install lint test ## Run install, lint, and test steps for CI
	@echo "✅ CI check complete."

release: install check ## Run full release flow
	@echo "🚀 Ready to publish (all checks passed)."

publish: release ## Run all checks then upload to PyPI
	@echo "🚀 Publishing to PyPI..."
	twine upload dist/*

inspect: ## List contents of built source distribution tar.gz
	@echo "📂 Inspecting contents of source distribution..."
	tar -tzf dist/*.tar.gz

# === Help ===
help: ## Show this help message
	@echo "📖 Available make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
