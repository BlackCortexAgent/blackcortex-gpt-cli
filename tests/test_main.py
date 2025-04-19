"""
Unit tests for blackcortex_cli.main.

These tests validate CLI argument parsing, early exit commands, REPL invocation,
OpenAI key validation, and one-shot execution flow for both streaming and non-streaming modes.
"""

import argparse
import io
import sys
from unittest.mock import MagicMock

import pytest
from openai import OpenAIError

from blackcortex_cli import main
from blackcortex_cli.main import handle_early_exits, parse_args, run_oneshot


def test_parse_args_sets_flags(monkeypatch):
    """
    Test that command-line flags are parsed correctly from sys.argv.
    Verifies '--stream' and '--no-markdown' flags and positional arguments.
    """
    test_args = ["gpt", "-s", "--no-markdown", "Hello"]
    monkeypatch.setattr(sys, "argv", test_args)
    args = parse_args()
    assert args.stream
    assert not args.markdown
    assert args.input_data == ["Hello"]


def test_handle_early_exits_triggers_command(monkeypatch):
    """
    Test that handle_early_exits executes the appropriate handler and returns True.
    """

    class DummyArgs:
        env = True
        reset = update = uninstall = set_key = ping = log = clear_log = version = False

    called = {"done": False}
    monkeypatch.setattr("blackcortex_cli.main.command_env", lambda: called.update(done=True))
    assert handle_early_exits(DummyArgs())
    assert called["done"]


def test_run_oneshot_stream(monkeypatch):
    """
    Test run_oneshot in streaming mode logs the response correctly.
    """

    def mock_chat(prompt):
        return "streamed"

    mock_log = MagicMock()
    args = argparse.Namespace(stream=True, markdown=True)

    monkeypatch.setattr(
        "blackcortex_cli.main.chat_manager", type("C", (), {"get_answer": mock_chat})
    )
    monkeypatch.setattr("blackcortex_cli.main.log_manager", mock_log)

    run_oneshot("Hello", args)
    mock_log.write.assert_called_once_with("Hello", "streamed")


def test_main_exits_without_key(monkeypatch):
    """
    Test that main exits with an error when no API key is configured.
    """
    monkeypatch.setattr("blackcortex_cli.main.config", type("C", (), {"api_key": None}))
    monkeypatch.setattr("sys.stderr", io.StringIO())

    with pytest.raises(SystemExit):
        main.main()


def test_main_runs_repl(monkeypatch):
    """
    Test that main() starts the REPL when no prompt is provided and stdin is a TTY.
    """
    config_mock = type("C", (), {"api_key": "sk-123", "log_file": "/dev/null"})
    chat_mock = MagicMock()
    repl_mock = MagicMock()

    monkeypatch.setattr("blackcortex_cli.main.config", config_mock)
    monkeypatch.setattr("blackcortex_cli.main.ChatManager", lambda **kw: chat_mock)
    monkeypatch.setattr("blackcortex_cli.main.ReplRunner", lambda **kw: repl_mock)
    monkeypatch.setattr("blackcortex_cli.main.handle_early_exits", lambda args: False)
    monkeypatch.setattr("sys.stdin", io.StringIO(""))  # No stdin input
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr(
        "blackcortex_cli.main.parse_args",
        lambda: argparse.Namespace(
            input_data=[],
            stream=False,
            markdown=True,
            reset=False,
            env=False,
            update=False,
            uninstall=False,
            set_key=None,
            ping=False,
            log=False,
            clear_log=False,
            version=False,
        ),
    )

    main.main()
    repl_mock.run.assert_called_once()


def test_main_chat_init_fails(monkeypatch):
    """
    Test that main() exits and logs an error when ChatManager initialization fails.
    """
    monkeypatch.setattr("blackcortex_cli.main.config", type("C", (), {"api_key": "sk-123"}))
    monkeypatch.setattr(
        "blackcortex_cli.main.parse_args",
        lambda: argparse.Namespace(
            input_data=[],
            stream=False,
            markdown=False,
            reset=False,
            env=False,
            update=False,
            uninstall=False,
            set_key=None,
            ping=False,
            log=False,
            clear_log=False,
            version=False,
        ),
    )

    monkeypatch.setattr(
        "blackcortex_cli.main.ChatManager", lambda **kw: (_ for _ in ()).throw(OpenAIError("fail"))
    )
    monkeypatch.setattr("sys.stderr", io.StringIO())

    with pytest.raises(SystemExit):
        main.main()

    assert "Failed to initialize" in sys.stderr.getvalue()


def test_main_handles_early_exit(monkeypatch):
    """
    Test that main() terminates early when a flag like --env or --version is used.
    """
    monkeypatch.setattr("blackcortex_cli.main.config", type("C", (), {"api_key": "sk-123"}))
    monkeypatch.setattr("blackcortex_cli.main.ChatManager", lambda **kw: MagicMock())
    monkeypatch.setattr("blackcortex_cli.main.handle_early_exits", lambda args: True)

    monkeypatch.setattr(
        "blackcortex_cli.main.parse_args",
        lambda: argparse.Namespace(
            input_data=[],
            stream=False,
            markdown=True,
            reset=False,
            env=False,
            update=False,
            uninstall=False,
            set_key=None,
            ping=False,
            log=False,
            clear_log=False,
            version=False,
        ),
    )
    main.main()  # Should just exit quietly


def test_main_runs_oneshot_from_stdin(monkeypatch):
    """
    Test main() handles one-shot input piped via stdin correctly.
    """
    config_mock = type("C", (), {"api_key": "sk-123", "log_file": "/dev/null"})
    chat_mock = MagicMock()
    chat_mock.get_answer.return_value = ("Hello!", 42)
    log_mock = MagicMock()

    monkeypatch.setattr("blackcortex_cli.main.config", config_mock)
    monkeypatch.setattr("blackcortex_cli.main.ChatManager", lambda **kw: chat_mock)
    monkeypatch.setattr("blackcortex_cli.main.log_manager", log_mock)
    monkeypatch.setattr("blackcortex_cli.main.ReplRunner", MagicMock())
    monkeypatch.setattr("blackcortex_cli.main.handle_early_exits", lambda args: False)

    monkeypatch.setattr("sys.stdin", io.StringIO("What is AI?"))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    monkeypatch.setattr(
        "blackcortex_cli.main.parse_args",
        lambda: argparse.Namespace(
            input_data=[],
            stream=False,
            markdown=False,
            reset=False,
            env=False,
            update=False,
            uninstall=False,
            set_key=None,
            ping=False,
            log=False,
            clear_log=False,
            version=False,
        ),
    )

    main.main()
    chat_mock.get_answer.assert_called_once_with("What is AI?", return_usage=True)
