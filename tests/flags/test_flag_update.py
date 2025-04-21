import subprocess
from argparse import Namespace
from unittest.mock import patch

import pytest

from blackcortex_cli.flags.flag_update import handle_update


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run to simulate command execution."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = None
        yield mock_run


def test_handle_update_pipx_success(mock_subprocess_run):
    """Test handle_update with pipx available and successful upgrade."""
    with (
        patch("blackcortex_cli.flags.flag_update.read_name", return_value="blackcortex-gpt-cli"),
        patch("shutil.which", return_value="/usr/bin/pipx"),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
        patch("sys.exit") as mock_exit,
    ):
        handle_update(Namespace(), None)

        mock_subprocess_run.assert_called_once_with(
            ["pipx", "upgrade", "blackcortex-gpt-cli"], check=True
        )
        mock_print.assert_any_call("[bold cyan]Updating blackcortex-gpt-cli...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold green][+] blackcortex-gpt-cli updated successfully.[/bold green]"
        )
        mock_exit.assert_called_once_with(0)


def test_handle_update_pip_success(mock_subprocess_run):
    """Test handle_update with pipx unavailable and pip upgrade successful."""
    with (
        patch("blackcortex_cli.flags.flag_update.read_name", return_value="blackcortex-gpt-cli"),
        patch("shutil.which", return_value=None),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
        patch("sys.exit") as mock_exit,
    ):
        handle_update(Namespace(), None)

        mock_subprocess_run.assert_called_once_with(
            ["pip", "install", "--upgrade", "blackcortex-gpt-cli"], check=True
        )
        mock_print.assert_any_call("[bold cyan]Updating blackcortex-gpt-cli...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold green][+] blackcortex-gpt-cli updated successfully.[/bold green]"
        )
        mock_exit.assert_called_once_with(0)


def test_handle_update_failure(mock_subprocess_run):
    """Test handle_update with upgrade failure."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, ["pipx", "upgrade", "blackcortex-gpt-cli"]
    )
    with (
        patch("blackcortex_cli.flags.flag_update.read_name", return_value="blackcortex-gpt-cli"),
        patch("shutil.which", return_value="/usr/bin/pipx"),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
        patch("sys.exit") as mock_exit,
    ):
        handle_update(Namespace(), None)

        mock_subprocess_run.assert_called_once_with(
            ["pipx", "upgrade", "blackcortex-gpt-cli"], check=True
        )
        mock_print.assert_any_call("[bold cyan]Updating blackcortex-gpt-cli...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold red][x] Update failed:[/bold red] Command '['pipx', 'upgrade', 'blackcortex-gpt-cli']' returned non-zero exit status 1."
        )
        mock_print.assert_any_call(
            "You can manually upgrade with:\n"
            "   pip install --upgrade blackcortex-gpt-cli  or\n"
            "   pipx upgrade blackcortex-gpt-cli"
        )
        mock_exit.assert_called_once_with(0)


def test_handle_update_empty_package_name(mock_subprocess_run):
    """Test handle_update with an empty package name."""
    with (
        patch("blackcortex_cli.flags.flag_update.read_name", return_value=""),
        patch("shutil.which", return_value="/usr/bin/pipx"),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
        patch("sys.exit") as mock_exit,
    ):
        handle_update(Namespace(), None)

        mock_subprocess_run.assert_called_once_with(["pipx", "upgrade", ""], check=True)
        mock_print.assert_any_call("[bold cyan]Updating ...[/bold cyan]")
        mock_print.assert_any_call("[bold green][+]  updated successfully.[/bold green]")
        mock_exit.assert_called_once_with(0)
