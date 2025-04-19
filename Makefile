VENV_BIN := .venv/bin

# === Setup ===
install: ## Create virtualenv and install dev dependencies
	@echo "🔧 Creating virtual environment and installing dependencies..."
	python3 -m venv .venv
	@echo "⬆️  Upgrading pip, setuptools, and wheel..."
	$(VENV_BIN)/pip install --upgrade pip setuptools wheel
	@echo "📦 Installing in editable mode with [dev] extras..."
	$(VENV_BIN)/pip install -e ".[dev]"
	@echo "🪝 Installing pre-commit hooks..."
	$(VENV_BIN)/pre-commit install

uninstall: ## Remove package, virtualenv, and metadata
	@echo "🧹 Uninstalling package and cleaning virtual environment..."
	$(VENV_BIN)/pip uninstall -y blackcortex-gpt-cli || echo "⚠️  Package not found or already uninstalled."
	rm -rf blackcortex_gpt_cli.egg-info .venv

# === Lint, Format, Test ===
format: ## Auto-fix formatting issues with Ruff
	@echo "🧼 Formatting with Ruff..."
	ruff check blackcortex_cli --fix

lint: ## Run Pylint
	@echo "🔎 Linting with Pylint..."
	$(VENV_BIN)/pylint blackcortex_cli --fail-under=9.0

test: ## Run Pytest with testdox
	@echo "🧪 Running tests..."
	PYTHONPATH=./ $(VENV_BIN)/pytest tests --testdox

# === Build & Distribution ===
clean: ## Remove build artifacts and Python cache
	@echo "🧹 Cleaning up..."
	rm -rf dist build *.egg-info .pytest_cache .ruff_cache \
		__pycache__ **/__pycache__ **/*.pyc

build: clean ## Build source and wheel distributions
	@echo "📦 Building distribution..."
	python -m build

validate: ## Check package with Twine
	@echo "🔍 Validating build artifacts..."
	twine check dist/*

# === Composite Targets ===
check: lint test build validate ## Full local validation suite
	@echo "✅ All checks passed."

release: install check ## Full local release prep (venv-based)
	@echo "🚀 Release flow complete."

publish: release ## Publish to PyPI
	@echo "🚀 Publishing to PyPI..."
	twine upload dist/*

# === CI Entry Point ===
ci-release: clean ## Run lint/test/build/validate using system Python (no venv)
	@echo "🔎 Linting..."
	pylint blackcortex_cli --fail-under=9.0
	@echo "🧪 Testing..."
	PYTHONPATH=./ pytest tests --testdox
	@echo "📦 Building..."
	python -m build
	@echo "🔍 Validating..."
	twine check dist/*

# === Inspect ===
inspect: ## List contents of the built source tarball
	@echo "📂 Inspecting package contents..."
	tar -tzf dist/*.tar.gz

# === Help ===
help: ## Show all Make targets with descriptions
	@echo "📖 Available make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
