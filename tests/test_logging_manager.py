"""
Unit tests for LogManager in blackcortex_cli.logging.manager.

Covers log writing, display, and deletion behaviors.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from blackcortex_cli.logging.manager import LogManager


@pytest.fixture
def temp_log_file():
    """Fixture to provide a temporary log file path."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        yield tmp.name
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


def test_write_creates_and_appends_log(temp_log_file):
    """
    Test write() creates a log file and appends timestamped prompt-response entry.
    """
    manager = LogManager(temp_log_file)
    prompt = "What's the capital of France?"
    response = "Paris is the capital of France."

    manager.write(prompt, response)

    with open(temp_log_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Prompt:\nWhat's the capital of France?" in content
    assert "Response:\nParis is the capital of France." in content
    assert "-" * 80 in content
    assert os.stat(temp_log_file).st_mode & 0o777 == 0o600


@patch("blackcortex_cli.logging.manager.console.print")
def test_show_prints_log_contents(mock_print, temp_log_file):
    """
    Test show() prints log contents using rich console if log exists.
    """
    Path(temp_log_file).write_text("Log entry here\n", encoding="utf-8")
    manager = LogManager(temp_log_file)

    manager.show()

    mock_print.assert_called_once_with("Log entry here\n")


@patch("blackcortex_cli.logging.manager.console.print")
def test_show_handles_missing_file(mock_print, temp_log_file):
    """
    Test show() prints warning if log file does not exist.
    """
    os.unlink(temp_log_file)  # ensure the file does not exist
    manager = LogManager(temp_log_file)

    manager.show()

    mock_print.assert_called_once_with("[yellow]⚠️ No log file found.[/yellow]")


@patch("blackcortex_cli.logging.manager.console.print")
def test_clear_removes_existing_log(mock_print, temp_log_file):
    """
    Test clear() deletes the log file and prints success message.
    """
    Path(temp_log_file).write_text("To be deleted", encoding="utf-8")
    manager = LogManager(temp_log_file)

    manager.clear()

    assert not os.path.exists(temp_log_file)
    mock_print.assert_called_once_with("[bold green]🧹 Log file has been deleted.[/bold green]")


@patch("blackcortex_cli.logging.manager.console.print")
def test_clear_handles_missing_log(mock_print, temp_log_file):
    """
    Test clear() prints warning if there is no log file to delete.
    """
    os.unlink(temp_log_file)
    manager = LogManager(temp_log_file)

    manager.clear()

    mock_print.assert_called_once_with("[yellow]⚠️ No log file to delete.[/yellow]")
