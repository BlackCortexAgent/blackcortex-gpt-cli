"""
Unit tests for Config class in blackcortex_cli.config.loader.

These tests verify that the configuration loader correctly interprets environment variables,
applies defaults when needed, and resolves paths appropriately. Includes hot reloading of
the config module between tests to apply new environment settings.
"""

import importlib
import os
from unittest.mock import patch

import pytest


@pytest.fixture
def reset_config_module():
    """
    Fixture to reload the config module after environment changes.

    Ensures that blackcortex_cli.config.loader is re-imported with fresh values.
    """
    if "blackcortex_cli.config.loader" in globals():
        import sys

        sys.modules.pop("blackcortex_cli.config.loader", None)
    yield
    importlib.reload(importlib.import_module("blackcortex_cli.config.loader"))


@patch("blackcortex_cli.config.loader.load_dotenv")
def test_config_defaults(mock_dotenv, monkeypatch, reset_config_module):
    """
    Test that Config falls back to default values when environment variables are not set.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_LOGFILE", raising=False)
    monkeypatch.delenv("OPENAI_TEMPERATURE", raising=False)
    monkeypatch.delenv("OPENAI_MAX_TOKENS", raising=False)
    monkeypatch.delenv("OPENAI_STREAM_ENABLED", raising=False)

    from blackcortex_cli.config.loader import Config

    cfg = Config()

    assert cfg.api_key is None
    assert cfg.model == "gpt-4o"


def test_config_env_loading(monkeypatch, reset_config_module):
    """
    Test that Config correctly loads values from environment variables.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
    monkeypatch.setenv("OPENAI_LOGFILE", "~/logs/log.txt")
    monkeypatch.setenv("OPENAI_TEMPERATURE", "0.9")
    monkeypatch.setenv("OPENAI_MAX_TOKENS", "1000")
    monkeypatch.setenv("OPENAI_MEMORY_LIMIT", "99")
    monkeypatch.setenv("OPENAI_STREAM_ENABLED", "true")

    from blackcortex_cli.config.loader import Config

    cfg = Config()

    assert cfg.api_key == "sk-test-123"
    assert cfg.model == "gpt-4"
    assert cfg.temperature == 0.9
    assert cfg.max_tokens == 1000
    assert cfg.memory_limit == 99
    assert cfg.stream_enabled is True


def test_config_expands_user_path(monkeypatch, reset_config_module):
    """
    Test that Config expands '~' in paths like memory_path and log_file to absolute paths.
    """
    monkeypatch.setenv("OPENAI_LOGFILE", "~/mygpt.log")
    monkeypatch.setenv("OPENAI_MEMORY_PATH", "~/mem.json")

    from blackcortex_cli.config.loader import Config

    cfg = Config()

    assert not cfg.log_file.startswith("~")
    assert not cfg.memory_path.startswith("~")
    assert os.path.isabs(cfg.log_file)
    assert os.path.isabs(cfg.memory_path)
