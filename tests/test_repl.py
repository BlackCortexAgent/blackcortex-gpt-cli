import os
from contextlib import nullcontext
from unittest.mock import MagicMock, patch

import pytest
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from blackcortex_cli.core.context import Context
from blackcortex_cli.repl import FilteredFileHistory, ReplRunner


@pytest.fixture
def mock_context():
    """Fixture for a mocked Context object with chat_manager and log_manager."""
    context = MagicMock(spec=Context)
    context.config = MagicMock()
    context.config.stream_enabled = False
    context.config.markdown_enabled = False
    context.config.model = "gpt-4o"
    context.config.history_path = "~/.gpt-cli/history"
    context.chat_manager = MagicMock()
    context.chat_manager.get_answer.return_value = ("Response", 10, "2025-04-21 12:00:00")
    context.log_manager = MagicMock()
    return context


@pytest.fixture
def temp_history_file(tmp_path):
    """Fixture for a temporary history file."""
    history_file = tmp_path / "history"
    return str(history_file)


@pytest.fixture
def mock_prompt_session(monkeypatch):
    """Fixture to mock PromptSession."""
    from prompt_toolkit.shortcuts import PromptSession

    mock_session = MagicMock(spec=PromptSession)
    mock_constructor = MagicMock(return_value=mock_session)
    monkeypatch.setattr("blackcortex_cli.repl.PromptSession", mock_constructor)
    return mock_constructor, mock_session


def test_filtered_file_history_init(temp_history_file, monkeypatch):
    """Test FilteredFileHistory initialization and permission setting."""
    mock_chmod = MagicMock()
    monkeypatch.setattr(os, "chmod", mock_chmod)
    monkeypatch.setattr(os.path, "exists", lambda x: True)

    history = FilteredFileHistory(temp_history_file)

    assert history.filename == temp_history_file
    mock_chmod.assert_called_once_with(temp_history_file, 0o660)


def test_filtered_file_history_init_no_file(temp_history_file, monkeypatch):
    """Test FilteredFileHistory when the history file does not exist."""
    mock_chmod = MagicMock()
    monkeypatch.setattr(os, "chmod", mock_chmod)
    monkeypatch.setattr(os.path, "exists", lambda x: False)

    FilteredFileHistory(temp_history_file)

    mock_chmod.assert_not_called()


def test_filtered_file_history_append_string(temp_history_file, monkeypatch):
    """Test append_string filters 'exit' and 'quit' and sets permissions."""
    mock_chmod = MagicMock()
    monkeypatch.setattr(os, "chmod", mock_chmod)
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    mock_append = MagicMock()
    monkeypatch.setattr("prompt_toolkit.history.FileHistory.append_string", mock_append)

    history = FilteredFileHistory(temp_history_file)

    history.append_string("test command")
    mock_append.assert_called_once_with("test command")
    mock_chmod.assert_called_with(temp_history_file, 0o660)

    mock_append.reset_mock()
    mock_chmod.reset_mock()
    history.append_string("exit")
    mock_append.assert_not_called()
    mock_chmod.assert_not_called()

    history.append_string("QUIT")
    mock_append.assert_not_called()
    mock_chmod.assert_not_called()


def test_filtered_file_history_permission_error(temp_history_file, monkeypatch, capsys):
    """Test _set_permissions handles PermissionError."""
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    monkeypatch.setattr(os, "chmod", MagicMock(side_effect=PermissionError("Access denied")))

    FilteredFileHistory(temp_history_file)

    captured = capsys.readouterr()
    assert "Permission denied when setting" in captured.out
    assert temp_history_file in captured.out
    assert "0o660" in captured.out


def test_filtered_file_history_generic_error(temp_history_file, monkeypatch, capsys):
    """Test _set_permissions handles generic exceptions."""
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    monkeypatch.setattr(os, "chmod", MagicMock(side_effect=Exception("Unknown error")))

    FilteredFileHistory(temp_history_file)

    captured = capsys.readouterr()
    assert "Failed to set permissions for" in captured.out
    assert temp_history_file in captured.out
    assert "Unknown" in captured.out


def test_repl_runner_init(mock_context, temp_history_file, mock_prompt_session):
    """Test ReplRunner initialization with context and history."""
    mock_constructor, mock_session = mock_prompt_session
    mock_context.config.history_path = temp_history_file

    repl = ReplRunner(mock_context)

    assert repl.context == mock_context
    assert repl.session == mock_session
    mock_constructor.assert_called_once()
    call_args = mock_constructor.call_args.kwargs
    assert call_args["history"].filename == os.path.expanduser(temp_history_file)
    assert isinstance(call_args["auto_suggest"], AutoSuggestFromHistory)


def test_repl_runner_run_welcome_message(mock_context, mock_prompt_session, capsys):
    """Test ReplRunner displays welcome message on run."""
    mock_constructor, mock_session = mock_prompt_session
    mock_session.prompt.side_effect = ["exit"]

    repl = ReplRunner(mock_context)
    repl.run()

    captured = capsys.readouterr()
    assert "BlackCortex GPT CLI is ready. Type 'exit' to quit." in captured.out


def test_repl_runner_run_exit_command(mock_context, mock_prompt_session, capsys):
    """Test ReplRunner exits on 'exit' or 'quit' commands."""
    mock_constructor, mock_session = mock_prompt_session
    mock_session.prompt.side_effect = ["exit"]

    repl = ReplRunner(mock_context)
    repl.run()

    captured = capsys.readouterr()
    assert "Goodbye!" in captured.out

    mock_session.prompt.side_effect = ["quit"]
    repl.run()
    assert "Goodbye!" in capsys.readouterr().out


def test_repl_runner_run_empty_input(mock_context, mock_prompt_session):
    """Test ReplRunner skips empty input."""
    mock_constructor, mock_session = mock_prompt_session
    mock_session.prompt.side_effect = ["", "exit"]

    repl = ReplRunner(mock_context)
    repl.run()

    mock_context.chat_manager.get_answer.assert_not_called()


def test_repl_runner_run_non_streaming(mock_context, mock_prompt_session, capsys):
    """Test ReplRunner processes input in non-streaming mode."""
    mock_constructor, mock_session = mock_prompt_session
    mock_context.config.stream_enabled = False
    mock_context.config.markdown_enabled = True
    mock_session.prompt.side_effect = ["Hello", "exit"]
    mock_context.chat_manager.get_answer.return_value = ("# Response", 10, "2025-04-21 12:00:00")

    with (
        patch("blackcortex_cli.repl.print_wrapped") as mock_print_wrapped,
        patch("blackcortex_cli.utils.console.console.status", return_value=nullcontext()),
        patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext()),
    ):
        repl = ReplRunner(mock_context)
        repl.run()

    assert mock_print_wrapped.call_count == 1
    mock_context.log_manager.write.assert_called_once_with("Hello", "# Response", 10)
    captured = capsys.readouterr()
    assert "gpt-4o  •  10 tokens  •  2025-04-21 12:00:00" in captured.out


def test_repl_runner_run_streaming(mock_context, mock_prompt_session, capsys):
    """Test ReplRunner processes input in streaming mode."""
    mock_constructor, mock_session = mock_prompt_session
    mock_context.config.stream_enabled = True
    mock_context.config.markdown_enabled = False
    mock_session.prompt.side_effect = ["Stream me", "exit"]
    mock_context.chat_manager.get_answer.return_value = (
        "Streamed response",
        15,
        "2025-04-21 12:00:00",
    )

    with patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext()):
        repl = ReplRunner(mock_context)
        repl.run()

    mock_context.log_manager.write.assert_called_once_with("Stream me", "Streamed response", 15)
    captured = capsys.readouterr()
    assert "gpt-4o  •  15 tokens  •  2025-04-21 12:00:00" in captured.out


def test_repl_runner_run_openai_error(mock_context, mock_prompt_session, capsys):
    """Test ReplRunner handles OpenAIError."""
    from openai import OpenAIError

    mock_constructor, mock_session = mock_prompt_session
    mock_session.prompt.side_effect = ["Test", "exit"]
    mock_context.chat_manager.get_answer.side_effect = OpenAIError("API failure")

    with patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext()):
        repl = ReplRunner(mock_context)
        repl.run()

    mock_context.log_manager.log_error.assert_called_once_with("Error occurred: API failure")
    captured = capsys.readouterr()
    assert "Error: API failure" in captured.out


def test_repl_runner_run_runtime_error(mock_context, mock_prompt_session, capsys):
    """Test ReplRunner handles RuntimeError."""
    mock_constructor, mock_session = mock_prompt_session
    mock_session.prompt.side_effect = ["Test", "exit"]
    mock_context.chat_manager.get_answer.side_effect = RuntimeError("Unexpected error")

    with patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext()):
        repl = ReplRunner(mock_context)
        repl.run()

    mock_context.log_manager.log_error.assert_called_once_with("Error occurred: Unexpected error")
    captured = capsys.readouterr()
    assert "Error: Unexpected error" in captured.out


def test_repl_runner_run_no_token_usage(mock_context, mock_prompt_session, capsys):
    """Test ReplRunner handles None token_usage."""
    mock_constructor, mock_session = mock_prompt_session
    mock_context.config.stream_enabled = False
    mock_context.config.markdown_enabled = False
    mock_session.prompt.side_effect = ["Test", "exit"]
    mock_context.chat_manager.get_answer.return_value = ("Response", None, "2025-04-21 12:00:00")

    with (
        patch("blackcortex_cli.utils.console.console.status", return_value=nullcontext()),
        patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext()),
    ):
        repl = ReplRunner(mock_context)
        repl.run()

    captured = capsys.readouterr()
    assert "gpt-4o  •  N/A tokens  •  2025-04-21 12:00:00" in captured.out
    mock_context.log_manager.write.assert_called_once_with("Test", "Response", None)


def test_repl_runner_run_invalid_history_path(mock_context, mock_prompt_session, capsys):
    """Test ReplRunner with an invalid history file path."""
    mock_constructor, mock_session = mock_prompt_session
    mock_context.config.history_path = "/invalid/path/history"
    mock_session.prompt.side_effect = ["exit"]

    with patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext()):
        repl = ReplRunner(mock_context)
        repl.run()

    captured = capsys.readouterr()
    assert "BlackCortex GPT CLI is ready" in captured.out


def test_repl_runner_run_keyboard_interrupt(mock_context, mock_prompt_session, capsys):
    """Test ReplRunner handles KeyboardInterrupt and continues until 'exit'."""
    mock_constructor, mock_session = mock_prompt_session
    mock_session.prompt.side_effect = [KeyboardInterrupt, "exit"]

    with patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext()):
        repl = ReplRunner(mock_context)
        repl.run()

    mock_context.log_manager.log_info.assert_called_once_with("User interrupted the session")
    mock_context.chat_manager.get_answer.assert_not_called()
    captured = capsys.readouterr()
    assert "Interrupted. Type 'exit' to quit." in captured.out
    assert "Goodbye!" in captured.out
