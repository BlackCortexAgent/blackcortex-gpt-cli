import os
from argparse import Namespace
from unittest.mock import Mock, call, mock_open, patch

import pytest
from openai import OpenAIError

from blackcortex_cli.flags.flag_set_key import handle_set_key


@pytest.fixture
def env_path(tmp_path):
    """Return a temporary .env path."""
    return str(tmp_path / ".gpt-cli" / ".env")


def test_handle_set_key_cli_success_existing_file(monkeypatch, env_path):
    """Test handle_set_key with a valid CLI-provided API key, updating existing .env file."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.get_env_path", lambda: env_path)
    mock_client = Mock()
    mock_client.models.list.return_value = None
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.OpenAI", lambda **kwargs: mock_client)

    mock_file = mock_open(read_data="OPENAI_API_KEY=old_key\nOTHER=val\n")
    with (
        patch("os.makedirs") as mock_makedirs,
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_file),
        patch("os.chmod") as mock_chmod,
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        handle_set_key(Namespace(set_key="new_key"), None)

        mock_makedirs.assert_called_once_with(os.path.dirname(env_path), exist_ok=True)
        mock_chmod.assert_called_once_with(env_path, 0o660)
        mock_print.assert_any_call("[bold cyan]Validating API key...[/bold cyan]")
        mock_print.assert_any_call("[bold green][+] API key saved and validated.[/bold green]")

        # Verify file write
        write_calls = mock_file().write.call_args_list
        assert call("OPENAI_API_KEY=new_key\n") in write_calls
        assert call("OTHER=val\n") in write_calls


def test_handle_set_key_cli_success_new_file(monkeypatch, env_path):
    """Test handle_set_key with a valid CLI-provided API key, creating new .env file."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.get_env_path", lambda: env_path)
    mock_client = Mock()
    mock_client.models.list.return_value = None
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.OpenAI", lambda **kwargs: mock_client)

    mock_file = mock_open()
    with (
        patch("os.makedirs") as mock_makedirs,
        patch("os.path.exists", return_value=False),
        patch("builtins.open", mock_file),
        patch("os.chmod") as mock_chmod,
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        handle_set_key(Namespace(set_key="new_key"), None)

        mock_makedirs.assert_called_once_with(os.path.dirname(env_path), exist_ok=True)
        mock_chmod.assert_called_once_with(env_path, 0o660)
        mock_print.assert_any_call("[bold cyan]Validating API key...[/bold cyan]")
        mock_print.assert_any_call("[bold green][+] API key saved and validated.[/bold green]")

        # Verify file write
        mock_file().write.assert_called_once_with("OPENAI_API_KEY=new_key\n")


def test_handle_set_key_prompt_success(monkeypatch, env_path):
    """Test handle_set_key with a valid interactively provided API key."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.get_env_path", lambda: env_path)
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.prompt", lambda _: "new_key")
    mock_client = Mock()
    mock_client.models.list.return_value = None
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.OpenAI", lambda **kwargs: mock_client)

    mock_file = mock_open()
    with (
        patch("os.makedirs") as mock_makedirs,
        patch("os.path.exists", return_value=False),
        patch("builtins.open", mock_file),
        patch("os.chmod") as mock_chmod,
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        handle_set_key(Namespace(set_key="__PROMPT__"), None)

        mock_makedirs.assert_called_once_with(os.path.dirname(env_path), exist_ok=True)
        mock_chmod.assert_called_once_with(env_path, 0o660)
        mock_print.assert_any_call(
            "[bold yellow][-] No API key provided. Please enter your OpenAI API key:[/bold yellow]"
        )
        mock_print.assert_any_call("[bold cyan]Validating API key...[/bold cyan]")
        mock_print.assert_any_call("[bold green][+] API key saved and validated.[/bold green]")

        # Verify file write
        mock_file().write.assert_called_once_with("OPENAI_API_KEY=new_key\n")


def test_handle_set_key_invalid_key(monkeypatch, env_path):
    """Test handle_set_key with an invalid API key."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.get_env_path", lambda: env_path)
    mock_client = Mock()
    mock_client.models.list.side_effect = OpenAIError("Invalid API key")
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.OpenAI", lambda **kwargs: mock_client)

    with patch("blackcortex_cli.utils.console.console.print") as mock_print:
        handle_set_key(Namespace(set_key="invalid_key"), None)
        mock_print.assert_any_call("[bold cyan]Validating API key...[/bold cyan]")
        mock_print.assert_any_call("[bold red][x] Invalid API key[/bold red]")


def test_handle_set_key_prompt_cancelled(monkeypatch, env_path):
    """Test handle_set_key when the prompt is cancelled."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.get_env_path", lambda: env_path)
    monkeypatch.setattr(
        "blackcortex_cli.flags.flag_set_key.prompt", Mock(side_effect=KeyboardInterrupt)
    )

    with patch("blackcortex_cli.utils.console.console.print") as mock_print:
        handle_set_key(Namespace(set_key="__PROMPT__"), None)
        mock_print.assert_any_call(
            "[bold yellow][-] No API key provided. Please enter your OpenAI API key:[/bold yellow]"
        )
        mock_print.assert_any_call("[bold red][x] API key prompt cancelled.[/bold red]")


def test_handle_set_key_makedirs_oserror(monkeypatch, env_path):
    """Test handle_set_key with OSError during directory creation."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.get_env_path", lambda: env_path)
    mock_client = Mock()
    mock_client.models.list.return_value = None
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.OpenAI", lambda **kwargs: mock_client)

    with (
        patch("os.makedirs", side_effect=OSError("Permission denied")),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        handle_set_key(Namespace(set_key="new_key"), None)
        mock_print.assert_any_call("[bold cyan]Validating API key...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold red][x] Failed to write .env file:[/bold red] Permission denied"
        )


def test_handle_set_key_write_oserror(monkeypatch, env_path):
    """Test handle_set_key with OSError during file write."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.get_env_path", lambda: env_path)
    mock_client = Mock()
    mock_client.models.list.return_value = None
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.OpenAI", lambda **kwargs: mock_client)

    with (
        patch("os.makedirs"),
        patch("os.path.exists", return_value=False),
        patch("builtins.open", side_effect=OSError("Write error")),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        handle_set_key(Namespace(set_key="new_key"), None)
        mock_print.assert_any_call("[bold cyan]Validating API key...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold red][x] Failed to write .env file:[/bold red] Write error"
        )


def test_handle_set_key_chmod_oserror(monkeypatch, env_path):
    """Test handle_set_key with OSError during chmod."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.get_env_path", lambda: env_path)
    mock_client = Mock()
    mock_client.models.list.return_value = None
    monkeypatch.setattr("blackcortex_cli.flags.flag_set_key.OpenAI", lambda **kwargs: mock_client)

    mock_file = mock_open()
    with (
        patch("os.makedirs"),
        patch("os.path.exists", return_value=False),
        patch("builtins.open", mock_file),
        patch("os.chmod", side_effect=OSError("Permission denied")),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        handle_set_key(Namespace(set_key="new_key"), None)
        mock_print.assert_any_call("[bold cyan]Validating API key...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold red][x] Failed to write .env file:[/bold red] Permission denied"
        )
