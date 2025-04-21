import subprocess
from argparse import Namespace
from unittest.mock import patch

import pytest

from blackcortex_cli.flags.flag_uninstall import handle_uninstall


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run to simulate command execution."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = None
        yield mock_run


def test_handle_uninstall_pipx_success(mock_subprocess_run):
    """Test handle_uninstall with pipx available and successful uninstall."""
    with (
        patch("blackcortex_cli.flags.flag_uninstall.read_name", return_value="blackcortex-gpt-cli"),
        patch("shutil.which", return_value="/usr/bin/pipx"),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
        patch("sys.exit") as mock_exit,
    ):
        handle_uninstall(Namespace())

        mock_subprocess_run.assert_called_once_with(
            ["pipx", "uninstall", "blackcortex-gpt-cli"], check=True
        )
        mock_print.assert_any_call("[bold cyan]🗑️ Uninstalling blackcortex-gpt-cli...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold green][+] blackcortex-gpt-cli uninstalled successfully.[/bold green]"
        )
        mock_exit.assert_called_once_with(0)


def test_handle_uninstall_pip_success(mock_subprocess_run):
    """Test handle_uninstall with pipx unavailable and pip uninstall successful."""
    with (
        patch("blackcortex_cli.flags.flag_uninstall.read_name", return_value="blackcortex-gpt-cli"),
        patch("shutil.which", return_value=None),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
        patch("sys.exit") as mock_exit,
    ):
        handle_uninstall(Namespace())

        mock_subprocess_run.assert_called_once_with(
            ["pip", "uninstall", "-y", "blackcortex-gpt-cli"], check=True
        )
        mock_print.assert_any_call("[bold cyan]🗑️ Uninstalling blackcortex-gpt-cli...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold green][+] blackcortex-gpt-cli uninstalled successfully.[/bold green]"
        )
        mock_exit.assert_called_once_with(0)


def test_handle_uninstall_failure(mock_subprocess_run):
    """Test handle_uninstall with uninstall failure."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, ["pipx", "uninstall", "blackcortex-gpt-cli"]
    )
    with (
        patch("blackcortex_cli.flags.flag_uninstall.read_name", return_value="blackcortex-gpt-cli"),
        patch("shutil.which", return_value="/usr/bin/pipx"),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
        patch("sys.exit") as mock_exit,
    ):
        handle_uninstall(Namespace())

        mock_subprocess_run.assert_called_once_with(
            ["pipx", "uninstall", "blackcortex-gpt-cli"], check=True
        )
        mock_print.assert_any_call("[bold cyan]🗑️ Uninstalling blackcortex-gpt-cli...[/bold cyan]")
        mock_print.assert_any_call(
            "[bold red][x] Uninstall failed:[/bold red] Command '['pipx', 'uninstall', 'blackcortex-gpt-cli']' returned non-zero exit status 1."
        )
        mock_print.assert_any_call(
            "You can manually uninstall with 'pip uninstall blackcortex-gpt-cli' or 'pipx uninstall blackcortex-gpt-cli'"
        )
        mock_exit.assert_called_once_with(0)


def test_handle_uninstall_empty_package_name(mock_subprocess_run):
    """Test handle_uninstall with an empty package name."""
    with (
        patch("blackcortex_cli.flags.flag_uninstall.read_name", return_value=""),
        patch("shutil.which", return_value="/usr/bin/pipx"),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
        patch("sys.exit") as mock_exit,
    ):
        handle_uninstall(Namespace())

        mock_subprocess_run.assert_called_once_with(["pipx", "uninstall", ""], check=True)
        mock_print.assert_any_call("[bold cyan]🗑️ Uninstalling ...[/bold cyan]")
        mock_print.assert_any_call("[bold green][+]  uninstalled successfully.[/bold green]")
        mock_exit.assert_called_once_with(0)
