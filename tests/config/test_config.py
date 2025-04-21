import importlib
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from blackcortex_cli.config import paths  # Import paths to reload it later
from blackcortex_cli.config.config import Config, load_env


# Fixture for mocked os
@pytest.fixture
def mock_os(monkeypatch):
    """Mock os and os.path functions."""
    monkeypatch.setattr(os, "makedirs", MagicMock())
    monkeypatch.setattr(os, "chmod", MagicMock())
    monkeypatch.setattr(os.path, "join", lambda *args: "/".join(args))
    monkeypatch.setattr(os, "getenv", MagicMock(return_value=None))
    return os


# Fixture for mocked CLI_PATH and ENV_PATH
@pytest.fixture
def mock_paths(monkeypatch):
    def mock_expanduser(path):
        if path == "~":
            return "/home/user"
        elif path.startswith("~/"):
            return os.path.join("/home/user", path[2:])
        return path

    monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
    importlib.reload(paths)
    return {"CLI_PATH": "/home/user/.gpt-cli", "ENV_PATH": "/home/user/.gpt-cli/.env"}


# Test load_env with dotenv available
def test_load_env_success(mock_os, mock_paths):
    """Test load_env when dotenv is available."""
    with patch("dotenv.load_dotenv") as mock_load_dotenv:
        result = load_env()

        assert result is True
        mock_os.makedirs.assert_called_once_with(mock_paths["CLI_PATH"], exist_ok=True)
        mock_os.chmod.assert_called_once_with(mock_paths["CLI_PATH"], 0o770)
        mock_load_dotenv.assert_any_call()
        mock_load_dotenv.assert_any_call(mock_paths["ENV_PATH"])


# Test load_env with dotenv unavailable
def test_load_env_no_dotenv(mock_os, mock_paths, monkeypatch):
    """Test load_env when dotenv is not available."""
    monkeypatch.setitem(sys.modules, "dotenv", None)  # Simulate dotenv not installed
    result = load_env()

    assert result is False
    mock_os.makedirs.assert_not_called()
    mock_os.chmod.assert_not_called()


# Test load_env with makedirs or chmod failure
def test_load_env_file_errors(mock_os, mock_paths):
    """Test load_env when makedirs or chmod fails."""
    with patch("dotenv.load_dotenv") as mock_load_dotenv:
        mock_os.makedirs.side_effect = OSError("Permission denied")
        result = load_env()

        assert result is True
        mock_os.makedirs.assert_called_once_with(mock_paths["CLI_PATH"], exist_ok=True)
        mock_os.chmod.assert_not_called()
        mock_load_dotenv.assert_any_call()
        mock_load_dotenv.assert_any_call(mock_paths["ENV_PATH"])


# Test Config initialization with environment variables
def test_config_with_env_vars(mock_os, mock_paths):
    """Test Config initialization with environment variables set."""
    mock_os.getenv.side_effect = lambda key, default=None: {
        "OPENAI_API_KEY": "test_key",
        "MODEL": "custom-model",
        "SUMMARY_MODEL": "summary-model",
        "DEFAULT_PROMPT": "Test prompt",
        "TEMPERATURE": "0.7",
        "MAX_TOKENS": "8192",
        "MEMORY_PATH": "/custom/path/memory.json",
        "HISTORY_PATH": "/custom/path/history",
        "MEMORY_LIMIT": "20",
        "MAX_SUMMARY_TOKENS": "4096",
        "LOG_FILE": "/custom/path/gpt.log",
        "LOG_LEVEL": "DEBUG",
        "LOG_TO_CONSOLE": "true",
        "MARKDOWN_ENABLED": "true",
        "STREAM_ENABLED": "true",
    }.get(key, default)

    with patch("blackcortex_cli.config.config.load_env"):
        config = Config()

        # API Credentials
        assert config.api_key == "test_key"

        # Model Configuration
        assert config.model == "custom-model"
        assert config.summary_model == "summary-model"
        assert config.default_prompt == "Test prompt"
        assert config.temperature == 0.7
        assert config.max_tokens == 8192

        # Memory and History
        assert config.memory_path == "/custom/path/memory.json"
        assert config.history_path == "/custom/path/history"
        assert config.memory_limit == 20
        assert config.max_summary_tokens == 4096

        # Logging
        assert config.log_file == "/custom/path/gpt.log"
        assert config.log_level == "DEBUG"
        assert config.log_to_console is True

        # Runtime Behavior
        assert config.markdown_enabled is True
        assert config.stream_enabled is True


# Test Config initialization with default values
def test_config_with_defaults(mock_os, mock_paths):
    """Test Config initialization with default values when env vars are unset."""
    mock_os.getenv.side_effect = lambda key, default=None: default

    with patch("blackcortex_cli.config.config.load_env"):
        config = Config()

        # API Credentials
        assert config.api_key is None

        # Model Configuration
        assert config.model == "gpt-4o"
        assert config.summary_model == "gpt-3.5-turbo"
        assert config.default_prompt == ""
        assert config.temperature == 0.5
        assert config.max_tokens == 4096

        # Memory and History
        assert config.memory_path == "/home/user/.gpt-cli/memory.json"
        assert config.history_path == "/home/user/.gpt-cli/history"
        assert config.memory_limit == 10
        assert config.max_summary_tokens == 2048

        # Logging
        assert config.log_file == "/home/user/.gpt-cli/gpt.log"
        assert config.log_level == "INFO"
        assert config.log_to_console is False

        # Runtime Behavior
        assert config.markdown_enabled is True  # Updated default from second config.py
        assert config.stream_enabled is False


# Test Config with invalid type conversions
def test_config_invalid_types(mock_os, mock_paths):
    """Test Config handles invalid environment variable types gracefully."""
    mock_os.getenv.side_effect = lambda key, default=None: {
        "TEMPERATURE": "invalid",  # Invalid float
        "MAX_TOKENS": "invalid",  # Invalid int
        "MEMORY_LIMIT": "invalid",  # Invalid int
        "MAX_SUMMARY_TOKENS": "invalid",  # Invalid int
    }.get(key, default)

    with patch("blackcortex_cli.config.config.load_env"), pytest.raises(ValueError):
        Config()


# Test Config when .env file is missing
def test_config_missing_env_file(mock_os, mock_paths):
    """Test Config when .env file is missing."""
    mock_os.getenv.side_effect = lambda key, default=None: default
    with (
        patch("dotenv.load_dotenv") as mock_load_dotenv,
        patch("os.path.exists", return_value=False),
    ):
        config = Config()
        assert config.api_key is None
        mock_load_dotenv.assert_any_call()
        mock_load_dotenv.assert_any_call(mock_paths["ENV_PATH"])


# Test Config with custom paths
def test_config_custom_paths(mock_os, mock_paths):
    """Test Config handles custom MEMORY_PATH, HISTORY_PATH, and LOG_FILE correctly."""
    mock_os.getenv.side_effect = lambda key, default=None: {
        "MEMORY_PATH": "/alternate/memory.json",
        "HISTORY_PATH": "/alternate/history",
        "LOG_FILE": "/alternate/gpt.log",
        "OPENAI_API_KEY": "test_key",
    }.get(key, default)

    with patch("blackcortex_cli.config.config.load_env"):
        config = Config()

        assert config.memory_path == "/alternate/memory.json"
        assert config.history_path == "/alternate/history"
        assert config.log_file == "/alternate/gpt.log"
        assert config.api_key == "test_key"
        # Verify defaults for other settings
        assert config.model == "gpt-4o"
        assert config.memory_limit == 10
        assert config.log_level == "INFO"
