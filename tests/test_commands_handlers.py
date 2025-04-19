"""
Unit tests for blackcortex_cli.commands.handlers.

This module validates the CLI command handlers such as `command_env`, `command_update`,
`command_uninstall`, `command_set_key`, `command_version`, and `command_ping`.
It ensures correct behavior under normal and failure conditions, including subprocess handling,
environment file updates, and OpenAI client interaction.
"""

import pathlib
import shutil
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from blackcortex_cli.commands import handlers


@pytest.fixture
def mock_env_path(tmp_path):
    """
    Fixture to create a temporary .env path and override the global ENV_PATH.
    """
    env_path = tmp_path / ".gpt-cli" / ".env"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    handlers.ENV_PATH = str(env_path)
    return env_path


@pytest.fixture
def mock_metadata():
    """
    Fixture providing sample metadata for a mock pyproject.toml.
    """
    return {
        "name": "blackcortex-gpt-cli",
        "version": "1.2.3",
        "description": "Test CLI",
        "authors": ["Test Author"],
    }


def test_read_project_metadata_returns_expected_keys(monkeypatch):
    """
    Test that read_project_metadata returns correct project metadata from pyproject.toml.
    """
    fake_toml = b"""
[project]
name = "testcli"
version = "0.1.0"
description = "test"
authors = ["tester"]
"""
    mock_path = tempfile.TemporaryDirectory()
    file_path = pathlib.Path(mock_path.name) / "pyproject.toml"
    file_path.write_bytes(fake_toml)

    monkeypatch.setattr(handlers, "__file__", str(file_path))
    meta = handlers.read_project_metadata()
    assert meta["name"] == "testcli"
    assert meta["version"] == "0.1.0"


def test_command_env_uses_editor(monkeypatch):
    """
    Test that command_env opens the editor set in EDITOR environment variable.
    """
    monkeypatch.setenv("EDITOR", "vim")
    mock_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", mock_run)
    handlers.command_env()
    mock_run.assert_called_once()
    assert "vim" in mock_run.call_args[0][0]


def test_command_update_runs_pip(monkeypatch, mock_metadata):
    """
    Test that command_update uses pip fallback when pipx is not available.
    """
    monkeypatch.setattr(handlers, "read_project_metadata", lambda: mock_metadata)
    monkeypatch.setattr(shutil, "which", lambda x: None)
    mock_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", mock_run)
    handlers.command_update()
    assert "pip" in mock_run.call_args[0][0]


def test_command_uninstall_uses_pipx(monkeypatch, mock_metadata):
    """
    Test that command_uninstall uses pipx when it is available in the system.
    """
    monkeypatch.setattr(handlers, "read_project_metadata", lambda: mock_metadata)
    monkeypatch.setattr(shutil, "which", lambda x: True)
    mock_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", mock_run)
    handlers.command_uninstall()
    assert "pipx" in mock_run.call_args[0][0]


def test_command_version_prints(monkeypatch, capsys, mock_metadata):
    """
    Test that command_version outputs the correct version to the console.
    """
    monkeypatch.setattr(handlers, "read_project_metadata", lambda: mock_metadata)
    handlers.command_version()
    captured = capsys.readouterr()
    assert mock_metadata["version"] in captured.out


def test_command_set_key_sets_and_validates(monkeypatch, mock_env_path):
    """
    Test that a valid API key is written to .env after prompt validation.
    """
    mock_client = MagicMock()
    monkeypatch.setattr(handlers, "OpenAI", lambda api_key: mock_client)
    monkeypatch.setattr(handlers, "prompt", lambda x: "sk-test-123")
    handlers.command_set_key(None)
    content = mock_env_path.read_text()
    assert "OPENAI_API_KEY=sk-test-123" in content


def test_command_set_key_replaces_existing(monkeypatch, mock_env_path):
    """
    Test that OPENAI_API_KEY in .env is replaced if it already exists.
    """
    mock_env_path.write_text("OPENAI_API_KEY=oldkey\nSOME_VAR=1\n")
    monkeypatch.setattr(handlers, "OpenAI", lambda api_key: MagicMock())
    handlers.command_set_key("newkey")
    content = mock_env_path.read_text()
    assert "OPENAI_API_KEY=newkey" in content
    assert "oldkey" not in content


def test_command_ping_success(monkeypatch, capsys):
    """
    Test that command_ping reports success when API is reachable.
    """
    monkeypatch.setattr(handlers, "OpenAI", lambda api_key: MagicMock())
    handlers.command_ping("sk-123")
    captured = capsys.readouterr()
    assert "reachable" in captured.out


def test_command_ping_failure(monkeypatch, capsys):
    """
    Test that command_ping reports failure when OpenAI API call fails.
    """
    mock_client = MagicMock()
    mock_client.models.list.side_effect = handlers.OpenAIError("fail")
    monkeypatch.setattr(handlers, "OpenAI", lambda api_key: mock_client)
    handlers.command_ping("sk-123")
    captured = capsys.readouterr()
    assert "Failed to reach" in captured.out


@patch.object(handlers.console, "print")
def test_command_env_handles_exception(mock_print, monkeypatch):
    """
    Test that command_env gracefully handles exceptions from subprocess.run.
    """
    monkeypatch.setenv("EDITOR", "badeditor")
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **kw: (_ for _ in ()).throw(Exception("fail"))
    )
    handlers.command_env()
    mock_print.assert_called_once()


@patch.object(handlers.console, "print")
def test_command_update_handles_error(mock_print, monkeypatch):
    """
    Test that command_update prints a failure message if pip/pipx fails.
    """
    monkeypatch.setattr(handlers, "read_project_metadata", lambda: {"name": "testcli"})
    monkeypatch.setattr(shutil, "which", lambda x: None)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: (_ for _ in ()).throw(subprocess.CalledProcessError(1, "fail")),
    )
    handlers.command_update()
    assert any("Update failed" in str(c.args[0]) for c in mock_print.call_args_list)


@patch.object(handlers.console, "print")
def test_command_update_missing_metadata(mock_print, monkeypatch):
    """
    Test that command_update raises FileNotFoundError if pyproject.toml is missing.
    """
    monkeypatch.setattr(
        handlers,
        "read_project_metadata",
        lambda: (_ for _ in ()).throw(FileNotFoundError("not found")),
    )
    with pytest.raises(FileNotFoundError):
        handlers.command_update()


@patch.object(handlers.console, "print")
def test_command_uninstall_handles_error(mock_print, monkeypatch):
    """
    Test that command_uninstall prints error message when subprocess fails.
    """
    monkeypatch.setattr(handlers, "read_project_metadata", lambda: {"name": "testcli"})
    monkeypatch.setattr(shutil, "which", lambda x: True)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: (_ for _ in ()).throw(subprocess.CalledProcessError(1, "fail")),
    )
    handlers.command_uninstall()
    assert any("Uninstall failed" in str(c.args[0]) for c in mock_print.call_args_list)


@patch.object(handlers.console, "print")
def test_command_set_key_invalid(mock_print, monkeypatch):
    """
    Test that command_set_key prints an error when OpenAI key validation fails.
    """

    def broken_client(api_key):
        mock = MagicMock()
        mock.models.list.side_effect = handlers.OpenAIError("bad key")
        return mock

    monkeypatch.setattr(handlers, "OpenAI", broken_client)
    handlers.command_set_key("sk-invalid")
    assert any("Invalid API key" in str(c.args[0]) for c in mock_print.call_args_list)
