import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from blackcortex_cli.core.log_manager import LogManager


# Fixture for a temporary log file path
@pytest.fixture
def temp_log_file(tmp_path):
    """Provide a temporary file path for logging."""
    return str(tmp_path / "test.log")


# Fixture for a mocked console
@pytest.fixture
def mock_console():
    """Provide a mocked console object."""
    return MagicMock()


# Test initialization without console logging
def test_init_no_console(temp_log_file, mock_console):
    """Test LogManager initialization without console logging."""
    with patch("blackcortex_cli.core.log_manager.RichHandler") as mock_rich_handler:
        log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)

        assert log_manager.path == os.path.expanduser(temp_log_file)
        assert log_manager.permissions == 0o600
        assert log_manager.group is None
        assert log_manager.logger.level == logging.INFO
        assert not log_manager._file_handler_initialized
        assert len(log_manager.logger.handlers) == 0
        mock_rich_handler.assert_not_called()


# Test initialization with console logging
def test_init_with_console(temp_log_file, mock_console):
    """Test LogManager initialization with console logging."""
    with (
        patch("blackcortex_cli.core.log_manager.RichHandler") as mock_rich_handler,
        patch("blackcortex_cli.core.log_manager.console", mock_console),
    ):
        mock_handler = MagicMock()
        mock_rich_handler.return_value = mock_handler

        log_manager = LogManager(temp_log_file, log_level="DEBUG", log_to_console=True)

        assert log_manager.logger.level == logging.DEBUG
        assert len(log_manager.logger.handlers) == 1
        assert log_manager.logger.handlers[0] == mock_handler
        mock_rich_handler.assert_called_once_with(
            show_time=True, show_level=True, show_path=False, console=mock_console
        )
        mock_handler.setFormatter.assert_called_once()
        mock_handler.setLevel.assert_called_once_with(logging.INFO)


# Test initialization with invalid log level
def test_init_invalid_log_level(temp_log_file, mock_console):
    """Test LogManager initialization with an invalid log level."""
    log_manager = LogManager(temp_log_file, log_level="INVALID", log_to_console=False)
    assert log_manager.logger.level == logging.INFO  # Falls back to default


# Test _init_file_handler
def test_init_file_handler(temp_log_file, mock_console):
    """Test _init_file_handler sets up the file handler correctly."""
    with (
        patch("blackcortex_cli.core.log_manager.RotatingFileHandler") as mock_file_handler,
        patch(
            "blackcortex_cli.core.log_manager.LogManager._set_permissions"
        ) as mock_set_permissions,
    ):
        mock_handler = MagicMock()
        mock_handler.level = logging.INFO  # Set level to avoid TypeError
        mock_file_handler.return_value = mock_handler

        log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
        log_manager._init_file_handler()

        assert log_manager._file_handler_initialized
        mock_file_handler.assert_called_once_with(
            temp_log_file, maxBytes=1024 * 1024 * 10, backupCount=5, encoding="utf-8"
        )
        mock_handler.setLevel.assert_called_once_with(logging.INFO)
        mock_handler.setFormatter.assert_called_once()
        mock_set_permissions.assert_called_once()
        assert mock_handler in log_manager.logger.handlers


# Test _init_file_handler already initialized
def test_init_file_handler_already_initialized(temp_log_file, mock_console):
    """Test _init_file_handler does nothing if already initialized."""
    with patch("blackcortex_cli.core.log_manager.RotatingFileHandler") as mock_file_handler:
        log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
        log_manager._file_handler_initialized = True

        log_manager._init_file_handler()

        mock_file_handler.assert_not_called()


# Test _set_permissions with existing file
def test_set_permissions_existing_file(temp_log_file, mock_console, monkeypatch):
    """Test _set_permissions sets permissions for an existing log file."""
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    mock_chmod = MagicMock()
    monkeypatch.setattr(os, "chmod", mock_chmod)

    log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
    log_manager._set_permissions()

    mock_chmod.assert_called_once_with(temp_log_file, 0o660)


# Test _set_permissions with PermissionError
def test_set_permissions_permission_error(temp_log_file, mock_console, monkeypatch, capsys):
    """Test _set_permissions handles PermissionError."""
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    monkeypatch.setattr(os, "chmod", MagicMock(side_effect=PermissionError("Access denied")))

    log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
    log_manager._set_permissions()

    captured = capsys.readouterr()
    assert "Permission denied" in captured.out
    assert temp_log_file in captured.out
    assert "0o600" in captured.out


# Test _set_permissions with generic exception
def test_set_permissions_generic_error(temp_log_file, mock_console, monkeypatch, capsys):
    """Test _set_permissions handles generic exceptions."""
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    monkeypatch.setattr(os, "chmod", MagicMock(side_effect=Exception("Unknown error")))

    log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
    log_manager._set_permissions()

    captured = capsys.readouterr()
    assert "Failed to set permissions" in captured.out
    assert temp_log_file in captured.out
    assert "Unknown error" in captured.out


# Test _set_permissions with non-existent file
def test_set_permissions_non_existent_file(temp_log_file, mock_console, monkeypatch):
    """Test _set_permissions does nothing when the log file does not exist."""
    monkeypatch.setattr(os.path, "exists", lambda x: False)
    mock_chmod = MagicMock()
    monkeypatch.setattr(os, "chmod", mock_chmod)

    log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
    log_manager._set_permissions()

    mock_chmod.assert_not_called()


# Test write with token usage
def test_write_with_token_usage(temp_log_file, mock_console):
    """Test write logs prompt, response, and token usage."""
    with (
        patch("blackcortex_cli.core.log_manager.RotatingFileHandler") as mock_file_handler,
        patch("blackcortex_cli.core.log_manager.LogManager._set_permissions"),
    ):
        mock_handler = MagicMock()
        mock_handler.level = logging.INFO
        logged_messages = []
        mock_handler.handle = lambda record: logged_messages.append(record.getMessage())
        mock_file_handler.return_value = mock_handler

        log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
        log_manager.write("Hello", "Hi there", token_usage=100)

        assert logged_messages == [
            "Prompt: Hello",
            "Response: Hi there",
            "[Token Usage: 100]",
            "-" * 80,
        ]


# Test write without token usage
def test_write_without_token_usage(temp_log_file, mock_console):
    """Test write logs prompt and response without token usage."""
    with (
        patch("blackcortex_cli.core.log_manager.RotatingFileHandler") as mock_file_handler,
        patch("blackcortex_cli.core.log_manager.LogManager._set_permissions"),
    ):
        mock_handler = MagicMock()
        mock_handler.level = logging.INFO
        logged_messages = []
        mock_handler.handle = lambda record: logged_messages.append(record.getMessage())
        mock_file_handler.return_value = mock_handler

        log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
        log_manager.write("Hello", "Hi there")

        assert logged_messages == ["Prompt: Hello", "Response: Hi there", "-" * 80]


# Test log_info
def test_log_info(temp_log_file, mock_console):
    """Test log_info logs an informational message."""
    with (
        patch("blackcortex_cli.core.log_manager.RotatingFileHandler") as mock_file_handler,
        patch("blackcortex_cli.core.log_manager.LogManager._set_permissions"),
    ):
        mock_handler = MagicMock()
        mock_handler.level = logging.INFO
        logged_messages = []
        mock_handler.handle = lambda record: logged_messages.append(record.getMessage())
        mock_file_handler.return_value = mock_handler

        log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
        log_manager.log_info("Test info")

        assert logged_messages == ["Test info"]


# Test log_error
def test_log_error(temp_log_file, mock_console):
    """Test log_error logs an error message."""
    with (
        patch("blackcortex_cli.core.log_manager.RotatingFileHandler") as mock_file_handler,
        patch("blackcortex_cli.core.log_manager.LogManager._set_permissions"),
    ):
        mock_handler = MagicMock()
        mock_handler.level = logging.INFO
        logged_messages = []
        mock_handler.handle = lambda record: logged_messages.append(record.getMessage())
        mock_file_handler.return_value = mock_handler

        log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
        log_manager.log_error("Test error")

        assert logged_messages == ["Test error"]


# Test log_debug
def test_log_debug(temp_log_file, mock_console):
    """Test log_debug logs a debug message."""
    with (
        patch("blackcortex_cli.core.log_manager.RotatingFileHandler") as mock_file_handler,
        patch("blackcortex_cli.core.log_manager.LogManager._set_permissions"),
    ):
        mock_handler = MagicMock()
        mock_handler.level = logging.DEBUG
        logged_messages = []
        mock_handler.handle = lambda record: logged_messages.append(record.getMessage())
        mock_file_handler.return_value = mock_handler

        log_manager = LogManager(temp_log_file, log_level="DEBUG", log_to_console=False)
        log_manager.log_debug("Test debug")

        assert logged_messages == ["Test debug"]


# Test show with existing non-empty file
def test_show_existing_non_empty_file(temp_log_file, capsys):
    """Test show displays contents of a non-empty log file."""
    with open(temp_log_file, "w", encoding="utf-8") as f:
        f.write("Log content")

    log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
    log_manager.show()

    captured = capsys.readouterr()
    assert "Log content" in captured.out


# Test show with existing empty file
def test_show_existing_empty_file(temp_log_file, capsys):
    """Test show handles an empty log file."""
    with open(temp_log_file, "w", encoding="utf-8") as f:
        f.write("")

    log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
    log_manager.show()

    captured = capsys.readouterr()
    assert "Log file is empty" in captured.out


# Test show with non-existent file
def test_show_non_existent_file(temp_log_file, capsys):
    """Test show handles a non-existent log file."""
    log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
    log_manager.show()

    captured = capsys.readouterr()
    assert "No log file found" in captured.out


# Test clear with existing file
def test_clear_existing_file(temp_log_file, capsys, monkeypatch):
    """Test clear deletes an existing log file."""
    with open(temp_log_file, "w", encoding="utf-8") as f:
        f.write("Log content")

    mock_remove = MagicMock()
    monkeypatch.setattr(os, "remove", mock_remove)

    log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
    log_manager.clear()

    captured = capsys.readouterr()
    assert "Log file has been deleted" in captured.out
    mock_remove.assert_called_once_with(temp_log_file)


# Test clear with non-existent file
def test_clear_non_existent_file(temp_log_file, capsys):
    """Test clear handles a non-existent log file."""
    log_manager = LogManager(temp_log_file, log_level="INFO", log_to_console=False)
    log_manager.clear()

    captured = capsys.readouterr()
    assert "No log file to delete" in captured.out
