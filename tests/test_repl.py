"""
Unit tests for ReplRunner in blackcortex_cli.repl.

Covers REPL input handling, markdown rendering, streaming and blocking modes,
and logging of user interactions.
"""

from contextlib import nullcontext
from unittest.mock import MagicMock, patch

import pytest

from blackcortex_cli.repl import ReplRunner


@pytest.fixture
def dummy_chat():
    chat = MagicMock()
    chat.config.model = "gpt-3.5-turbo"
    chat.stream_enabled = False
    return chat


@pytest.fixture
def dummy_log():
    return MagicMock()


@patch("blackcortex_cli.repl.console.print")
@patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext())
def test_run_blocking_flow_with_exit(mock_patch_stdout, mock_console_print, dummy_chat, dummy_log):
    """
    Test REPL in blocking mode handles input and exits cleanly after 'exit'.
    """
    dummy_chat.get_answer.return_value = ("This is a test.", 42)

    runner = ReplRunner(chat=dummy_chat, log=dummy_log)
    runner.session.prompt = MagicMock(side_effect=["Say something", "exit"])
    runner.run()

    dummy_chat.get_answer.assert_called_once_with("Say something", return_usage=True)
    dummy_log.write.assert_called_once_with("Say something", "This is a test.")
    assert any("Goodbye" in str(args[0]) for args, _ in mock_console_print.call_args_list if args)


@patch("blackcortex_cli.repl.console.print")
@patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext())
def test_run_streaming_mode(mock_patch_stdout, mock_console_print, dummy_chat, dummy_log):
    """
    Test REPL in streaming mode handles input and exits cleanly.
    """
    dummy_chat.stream_enabled = True
    dummy_chat.get_answer.return_value = "Streamed response."

    runner = ReplRunner(chat=dummy_chat, log=dummy_log)
    runner.session.prompt = MagicMock(side_effect=["Stream this", "quit"])
    runner.run()

    dummy_chat.get_answer.assert_called_once_with("Stream this")
    dummy_log.write.assert_called_once_with("Stream this", "Streamed response.")
    assert any("Goodbye" in str(args[0]) for args, _ in mock_console_print.call_args_list if args)


@patch("blackcortex_cli.repl.console.print")
@patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext())
def test_run_handles_keyboard_interrupt(mock_patch_stdout, mock_print, dummy_chat, dummy_log):
    """
    Test REPL catches and prints friendly message on KeyboardInterrupt.
    """
    runner = ReplRunner(chat=dummy_chat, log=dummy_log)
    runner.session.prompt = MagicMock(side_effect=[KeyboardInterrupt, "exit"])
    runner.run()

    assert any("Interrupted" in str(call.args[0]) for call in mock_print.call_args_list)


@patch("blackcortex_cli.repl.console.print")
@patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext())
def test_run_handles_openai_error(mock_patch_stdout, mock_print, dummy_chat, dummy_log):
    """
    Test REPL handles OpenAIError or RuntimeError gracefully.
    """
    dummy_chat.get_answer.side_effect = RuntimeError("API crashed")

    runner = ReplRunner(chat=dummy_chat, log=dummy_log)
    runner.session.prompt = MagicMock(side_effect=["hello", "exit"])
    runner.run()

    assert any("Error" in str(args[0]) for args, _ in mock_print.call_args_list if args)


@patch("blackcortex_cli.repl.console.print")
@patch("blackcortex_cli.repl.patch_stdout", return_value=nullcontext())
def test_run_skips_empty_input(mock_patch_stdout, mock_print, dummy_chat, dummy_log):
    """
    Test REPL skips empty input and prompts again.
    """
    dummy_chat.get_answer.return_value = ("Skipped nothing", 0)

    runner = ReplRunner(chat=dummy_chat, log=dummy_log)
    runner.session.prompt = MagicMock(side_effect=["", "hello", "exit"])
    runner.run()

    dummy_chat.get_answer.assert_called_once_with("hello", return_usage=True)
    assert not any(
        "Skipped nothing" in str(args[0]) for args, _ in mock_print.call_args_list if args
    )
