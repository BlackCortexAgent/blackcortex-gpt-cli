from unittest.mock import MagicMock, patch

import pytest

from blackcortex_cli.core.context import Context
from blackcortex_cli.flags.flag_clear_history import clear_history


@pytest.fixture
def mock_context():
    """Fixture for a mocked Context object with a config."""
    config = MagicMock()
    config.history_path = "~/.gpt-cli/history"
    context = MagicMock(spec=Context)
    context.config = config
    return context


def test_clear_history_success(mock_context):
    """Test clear_history successfully deletes an existing history file."""
    with (
        patch("os.path.expanduser", return_value="/home/user/.gpt-cli/history"),
        patch("os.path.exists", return_value=True),
        patch("os.remove") as mock_remove,
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        clear_history(MagicMock(), mock_context)
        mock_remove.assert_called_once_with("/home/user/.gpt-cli/history")
        mock_print.assert_called_once_with(
            "[bold green][+] History file has been cleared.[/bold green]"
        )


def test_clear_history_permission_error(mock_context):
    """Test clear_history handles PermissionError when deleting the history file."""
    with (
        patch("os.path.expanduser", return_value="/home/user/.gpt-cli/history"),
        patch("os.path.exists", return_value=True),
        patch("os.remove", side_effect=PermissionError("Permission denied")),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        clear_history(MagicMock(), mock_context)
        mock_print.assert_called_once_with(
            "[bold red][x] Permission denied when clearing history file.[/bold red]"
        )


def test_clear_history_generic_error(mock_context):
    """Test clear_history handles generic exceptions when deleting the history file."""
    with (
        patch("os.path.expanduser", return_value="/home/user/.gpt-cli/history"),
        patch("os.path.exists", return_value=True),
        patch("os.remove", side_effect=OSError("Disk full")),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        clear_history(MagicMock(), mock_context)
        mock_print.assert_called_once_with(
            "[bold red][x] Failed to clear history file: Disk full[/bold red]"
        )


def test_clear_history_no_file(mock_context):
    """Test clear_history when the history file does not exist."""
    with (
        patch("os.path.expanduser", return_value="/home/user/.gpt-cli/history"),
        patch("os.path.exists", return_value=False),
        patch("os.remove") as mock_remove,
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        clear_history(MagicMock(), mock_context)
        mock_remove.assert_not_called()
        mock_print.assert_called_once_with("[yellow][-] No history file to clear.[/yellow]")
