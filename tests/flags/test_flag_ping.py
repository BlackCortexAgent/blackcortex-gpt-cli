from argparse import Namespace
from unittest.mock import Mock, patch

import pytest
from openai import OpenAIError

from blackcortex_cli.config.config import Config
from blackcortex_cli.core.context import Context
from blackcortex_cli.core.log_manager import LogManager
from blackcortex_cli.flags.flag_ping import handle_ping


# Fixture to prevent .gpt-cli directory creation
@pytest.fixture(autouse=True)
def prevent_gpt_cli_dir(monkeypatch):
    """Mock file system operations to prevent .gpt-cli directory creation."""
    monkeypatch.setattr("os.makedirs", Mock())
    monkeypatch.setattr("os.chmod", Mock(side_effect=OSError("Mocked chmod")))
    # Mock load_env to prevent .env loading and directory creation
    monkeypatch.setattr("blackcortex_cli.config.config.load_env", lambda: False)
    yield


# Fixture for a test context with a mocked Config and LogManager
@pytest.fixture
def context(tmp_path, monkeypatch):
    """Create a test context with a mocked Config and LogManager."""
    # Mock Config to avoid real initialization
    config = Mock(spec=Config)
    config.log_file = str(tmp_path / "gpt.log")
    config.api_key = "test_api_key"
    log_manager = LogManager(config.log_file)
    log_manager.logger = Mock(spec=["info", "error", "debug", "addHandler"])
    log_manager._init_file_handler = Mock()
    return Context(config, log_manager)


def test_handle_ping_success(monkeypatch, context):
    """Test handle_ping with a successful API call."""
    # Mock OpenAI client
    mock_client = Mock()
    mock_client.models.list.return_value = None
    mock_openai = Mock(return_value=mock_client)
    monkeypatch.setattr("blackcortex_cli.flags.flag_ping.OpenAI", mock_openai)

    # Mock console.print to capture output
    with patch("blackcortex_cli.utils.console.console.print") as mock_print:
        handle_ping(Namespace(), context)
        mock_print.assert_any_call("[bold cyan]Pinging OpenAI API...[/bold cyan]")
        mock_print.assert_any_call("[bold green][+] OpenAI API is reachable.[/bold green]")

    # Verify API key and client call
    mock_openai.assert_called_once_with(api_key="test_api_key")
    mock_client.models.list.assert_called_once()


def test_handle_ping_openai_error(monkeypatch, context):
    """Test handle_ping with an OpenAIError."""
    # Mock OpenAI client to raise OpenAIError
    mock_client = Mock()
    mock_client.models.list.side_effect = OpenAIError("API connection failed")
    mock_openai = Mock(return_value=mock_client)
    monkeypatch.setattr("blackcortex_cli.flags.flag_ping.OpenAI", mock_openai)

    # Mock console.print to capture output
    with patch("blackcortex_cli.utils.console.console.print") as mock_print:
        handle_ping(Namespace(), context)
        mock_print.assert_any_call("[bold cyan]Pinging OpenAI API...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold red][x] Failed to reach OpenAI API:[/bold red] API connection failed"
        )

    # Verify API key and client call
    mock_openai.assert_called_once_with(api_key="test_api_key")
    mock_client.models.list.assert_called_once()


def test_handle_ping_invalid_api_key(monkeypatch, context):
    """Test handle_ping with an invalid API key causing OpenAIError."""
    # Mock OpenAI client to raise OpenAIError for invalid key
    mock_client = Mock()
    mock_client.models.list.side_effect = OpenAIError("Invalid API key")
    mock_openai = Mock(return_value=mock_client)
    monkeypatch.setattr("blackcortex_cli.flags.flag_ping.OpenAI", mock_openai)

    # Mock console.print to capture output
    with patch("blackcortex_cli.utils.console.console.print") as mock_print:
        handle_ping(Namespace(), context)
        mock_print.assert_any_call("[bold cyan]Pinging OpenAI API...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold red][x] Failed to reach OpenAI API:[/bold red] Invalid API key"
        )

    # Verify API key and client call
    mock_openai.assert_called_once_with(api_key="test_api_key")
    mock_client.models.list.assert_called_once()
