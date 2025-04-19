import os
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

from rich.markdown import Markdown

from blackcortex_cli import commands


def test_command_version(capsys):
    """Test that command_version prints the version from pyproject.toml."""
    with patch("blackcortex_cli.commands.read_project_metadata", return_value={"version": "1.2.3"}):
        commands.command_version()
        captured = capsys.readouterr()
        assert "1.2.3" in captured.out


def test_command_update_with_pip(monkeypatch):
    """Test update fallback to pip when pipx is not available."""
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    with patch("subprocess.run") as mock_run, patch(
        "blackcortex_cli.commands.read_project_metadata", return_value={"name": "my-cli"}
    ):
        commands.command_update()
        mock_run.assert_called_with(["pip", "install", "--upgrade", "my-cli"], check=True)


def test_command_update_failure():
    """Test update failure fallback with pip."""
    with patch(
        "blackcortex_cli.commands.read_project_metadata", return_value={"name": "cli"}
    ), patch("shutil.which", return_value=None), patch(
        "subprocess.run", side_effect=subprocess.CalledProcessError(1, "pip")
    ), patch("blackcortex_cli.commands.console.print") as mock_print:
        commands.command_update()
        assert any("❌ Update failed:" in str(call) for call in mock_print.call_args_list)


def test_command_uninstall_with_pipx():
    """Test uninstall using pipx."""
    with patch("shutil.which", return_value="/usr/bin/pipx"), patch(
        "subprocess.run"
    ) as mock_run, patch(
        "blackcortex_cli.commands.read_project_metadata", return_value={"name": "my-cli"}
    ):
        commands.command_uninstall()
        mock_run.assert_called_with(["pipx", "uninstall", "my-cli"], check=True)


def test_command_uninstall_failure():
    """Test uninstall command failure."""
    with patch(
        "blackcortex_cli.commands.read_project_metadata", return_value={"name": "cli"}
    ), patch("shutil.which", return_value=None), patch(
        "subprocess.run", side_effect=subprocess.CalledProcessError(1, "pip")
    ), patch("blackcortex_cli.commands.console.print") as mock_print:
        commands.command_uninstall()
        assert any("❌ Uninstall failed:" in str(call) for call in mock_print.call_args_list)


def test_command_set_key_valid(monkeypatch):
    """Test saving a valid API key."""
    mock_client = MagicMock()
    mock_client.models.list.return_value = ["model"]
    monkeypatch.setattr("blackcortex_cli.commands.OpenAI", lambda api_key: mock_client)

    with tempfile.TemporaryDirectory() as tmpdir, patch(
        "blackcortex_cli.commands.ENV_PATH", os.path.join(tmpdir, ".env")
    ), patch("blackcortex_cli.commands.console.print") as mock_print:
        commands.command_set_key("sk-test-key")
        mock_print.assert_any_call("[bold green]✅ API key saved and validated.[/bold green]")


def test_command_set_key_prompt(monkeypatch):
    """Test command_set_key with interactive prompt flow."""
    monkeypatch.setattr("blackcortex_cli.commands.prompt", lambda msg: "sk-from-prompt")

    mock_client = MagicMock()
    mock_client.models.list.return_value = ["model"]
    monkeypatch.setattr("blackcortex_cli.commands.OpenAI", lambda api_key: mock_client)

    with tempfile.TemporaryDirectory() as tmpdir, patch(
        "blackcortex_cli.commands.ENV_PATH", os.path.join(tmpdir, ".env")
    ), patch("blackcortex_cli.commands.console.print") as mock_print:
        commands.command_set_key(None)
        mock_print.assert_any_call("[bold green]✅ API key saved and validated.[/bold green]")
        with open(os.path.join(tmpdir, ".env"), "r", encoding="utf-8") as f:
            assert "OPENAI_API_KEY=sk-from-prompt" in f.read()


def test_command_ping_success():
    """Test ping command with successful API call."""
    mock_client = MagicMock()
    mock_client.models.list.return_value = ["model"]
    with patch("blackcortex_cli.commands.OpenAI", return_value=mock_client), patch(
        "blackcortex_cli.commands.console.print"
    ) as mock_print:
        commands.command_ping("test-key")
        mock_print.assert_any_call("[bold green]✅ OpenAI API is reachable.[/bold green]")


def test_command_ping_failure():
    """Test ping failure when API is unreachable or key is invalid."""
    with patch(
        "blackcortex_cli.commands.OpenAI", side_effect=commands.OpenAIError("invalid key")
    ), patch("blackcortex_cli.commands.console.print") as mock_print:
        commands.command_ping("invalid-key")
        mock_print.assert_any_call(
            "[bold red]❌ Failed to reach OpenAI API:[/bold red] invalid key"
        )


def test_command_log_shows_contents(tmp_path):
    """Test command_log prints file contents if file exists."""
    log_file = tmp_path / "log.txt"
    log_file.write_text("test log content")
    with patch("blackcortex_cli.commands.console.print") as mock_print:
        commands.command_log(str(log_file))
        mock_print.assert_called_with("test log content")


def test_command_log_missing_file(tmp_path):
    """Test command_log when the file does not exist."""
    log_file = tmp_path / "missing.txt"
    with patch("blackcortex_cli.commands.console.print") as mock_print:
        commands.command_log(str(log_file))
        mock_print.assert_called_with("[yellow]⚠️ No log file found.[/yellow]")


def test_command_clear_log_deletes(tmp_path):
    """Test command_clear_log deletes the log file."""
    log_file = tmp_path / "log.txt"
    log_file.write_text("some logs")
    commands.command_clear_log(str(log_file))
    assert not log_file.exists()


def test_command_clear_log_missing_file(tmp_path):
    """Test command_clear_log when file is missing."""
    log_file = tmp_path / "nope.log"
    with patch("blackcortex_cli.commands.console.print") as mock_print:
        commands.command_clear_log(str(log_file))
        mock_print.assert_called_with("[yellow]⚠️ No log file to delete.[/yellow]")


def test_command_summary_plain(capsys):
    """Test command_summary without markdown formatting."""
    commands.command_summary("plain summary", markdown=False)
    output = capsys.readouterr().out
    assert "plain summary" in output


def test_command_summary_markdown():
    """Test command_summary prints a Markdown object."""
    with patch("blackcortex_cli.commands.console.print") as mock_print:
        commands.command_summary("**Bold**", markdown=True)

        assert any(
            isinstance(call.args[0], Markdown) for call in mock_print.call_args_list
        ), "Expected a Markdown object to be printed"


def test_command_env_editor_failure(monkeypatch):
    """Test command_env when the editor command fails."""
    monkeypatch.setenv("EDITOR", "nonexistent-editor")
    with patch("subprocess.run", side_effect=Exception("fail")), patch(
        "blackcortex_cli.commands.console.print"
    ) as mock_print:
        commands.command_env()
        mock_print.assert_any_call("[bold red]❌ Failed to open editor:[/bold red] fail")
