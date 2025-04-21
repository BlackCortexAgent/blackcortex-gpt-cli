import argparse
import importlib
import pkgutil
import sys
from unittest.mock import MagicMock, patch

import pytest

import blackcortex_cli.main as cli_main


@pytest.fixture
def mock_context(monkeypatch):
    config = MagicMock()
    config.api_key = "sk-test"
    config.stream_enabled = False
    config.markdown_enabled = False

    chat_manager = MagicMock()
    log_manager = MagicMock()

    context = MagicMock()
    context.config = config
    context.chat_manager = chat_manager
    context.log_manager = log_manager

    monkeypatch.setattr(cli_main, "Context", lambda *a, **kw: context)
    monkeypatch.setattr(cli_main, "ChatManager", lambda _: chat_manager)
    monkeypatch.setattr(cli_main, "LogManager", lambda *a, **kw: log_manager)

    return context


def test_main_runs_oneshot_with_input(monkeypatch, mock_context):
    """Test one-shot execution when input is provided via command line args."""
    monkeypatch.setattr(cli_main, "load_all_flags", lambda: None)

    args = MagicMock()
    args.input_data = ["Hello"]
    monkeypatch.setattr(cli_main, "parse_args", lambda: args)

    stdin = MagicMock()
    stdin.isatty.return_value = True
    monkeypatch.setattr(cli_main.sys, "stdin", stdin)

    monkeypatch.setattr(
        cli_main,
        "flag_registry",
        MagicMock(get_pre_handlers=lambda args: [], get_post_handlers=lambda args: []),
    )
    monkeypatch.setattr(cli_main, "run_oneshot", MagicMock())
    monkeypatch.setattr(cli_main, "ReplRunner", MagicMock())

    cli_main.main()
    cli_main.run_oneshot.assert_called_once()


def test_main_falls_back_to_repl(monkeypatch, mock_context):
    """Test REPL launch when no input is given and stdin is a terminal."""
    monkeypatch.setattr(cli_main, "load_all_flags", lambda: None)

    args = MagicMock()
    args.input_data = []
    monkeypatch.setattr(cli_main, "parse_args", lambda: args)

    stdin = MagicMock()
    stdin.isatty.return_value = True
    monkeypatch.setattr(cli_main.sys, "stdin", stdin)

    monkeypatch.setattr(
        cli_main,
        "flag_registry",
        MagicMock(get_pre_handlers=lambda args: [], get_post_handlers=lambda args: []),
    )
    monkeypatch.setattr(cli_main, "run_oneshot", MagicMock())

    repl_runner = MagicMock()
    monkeypatch.setattr(cli_main, "ReplRunner", lambda ctx: repl_runner)

    cli_main.main()
    repl_runner.run.assert_called_once()


def test_main_aborts_on_missing_api_key(monkeypatch):
    """Test behavior when API key is missing."""
    monkeypatch.setattr(cli_main, "load_all_flags", lambda: None)

    config = MagicMock()
    config.api_key = None
    monkeypatch.setattr(cli_main, "Config", lambda: config)

    log_manager = MagicMock()
    monkeypatch.setattr(cli_main, "LogManager", lambda *a, **kw: log_manager)

    monkeypatch.setattr(
        cli_main,
        "flag_registry",
        MagicMock(get_pre_handlers=lambda args: [], get_post_handlers=lambda args: []),
    )

    args = MagicMock()
    args.input_data = []
    monkeypatch.setattr(cli_main, "parse_args", lambda: args)

    stdin = MagicMock()
    stdin.isatty.return_value = True
    stdin.encoding = "utf-8"  # Set encoding to prevent TypeError in PromptSession
    monkeypatch.setattr(cli_main.sys, "stdin", stdin)

    # Define a mock exit that raises SystemExit
    def mock_exit(code):
        raise SystemExit(code)

    monkeypatch.setattr(cli_main.sys, "exit", mock_exit)

    # Expect SystemExit with code 1
    with pytest.raises(SystemExit) as exc_info:
        cli_main.main()
    assert exc_info.value.code == 1


def test_main_runs_pre_and_post_handlers(monkeypatch, mock_context):
    """Test that pre and post handlers are called and exit if required."""
    monkeypatch.setattr(cli_main, "load_all_flags", lambda: None)

    args = MagicMock()
    args.input_data = []
    monkeypatch.setattr(cli_main, "parse_args", lambda: args)

    handler_pre = MagicMock()
    handler_post = MagicMock()
    registry = MagicMock()
    registry.get_pre_handlers.return_value = [(handler_pre, True)]
    registry.get_post_handlers.return_value = [handler_post]
    monkeypatch.setattr(cli_main, "flag_registry", registry)

    monkeypatch.setattr(cli_main.sys, "stdin", MagicMock(isatty=lambda: True))
    monkeypatch.setattr(cli_main, "console", MagicMock())

    cli_main.main()
    handler_pre.assert_called_once()
    handler_post.assert_not_called()  # pre-handler with exit_after=True


def test_run_oneshot_prints_markdown(monkeypatch, mock_context):
    """Test Markdown output formatting when enabled."""
    mock_context.config.markdown_enabled = True
    mock_context.config.stream_enabled = False
    mock_context.chat_manager.get_answer.return_value = ("# Hello", {"tokens": 5}, "now")

    mock_print = MagicMock()
    monkeypatch.setattr(cli_main, "console", MagicMock(print=mock_print))

    with patch("rich.markdown.Markdown") as mock_md:
        cli_main.run_oneshot("Test input", MagicMock(), mock_context)
        mock_md.assert_called_once_with("# Hello")
        mock_print.assert_called_once_with(mock_md.return_value)


def test_run_oneshot_prints_plain(monkeypatch, mock_context):
    """Test plain output formatting when Markdown is disabled."""
    mock_context.config.markdown_enabled = False
    mock_context.config.stream_enabled = False
    mock_context.chat_manager.get_answer.return_value = ("Just text", {"tokens": 2}, "now")

    mock_print = MagicMock()
    monkeypatch.setattr(cli_main, "console", MagicMock(print=mock_print))

    cli_main.run_oneshot("Hi", MagicMock(), mock_context)
    mock_print.assert_called_once_with("Just text")


def test_run_oneshot_handles_streaming(monkeypatch, mock_context):
    """Test streaming output when stream_enabled is True."""
    mock_context.config.stream_enabled = True
    mock_context.config.markdown_enabled = False
    mock_context.chat_manager.get_answer.return_value = ("Streamed text", {"tokens": 3}, "now")

    mock_print = MagicMock()
    monkeypatch.setattr(cli_main, "console", MagicMock(print=mock_print))

    cli_main.run_oneshot("Stream me", MagicMock(), mock_context)
    mock_print.assert_not_called()  # Streaming should bypass direct console.print


def test_main_handles_chat_manager_error(monkeypatch, mock_context):
    """Test error handling when ChatManager raises an exception."""
    mock_context.chat_manager.get_answer.side_effect = Exception("ChatManager failed")

    args = MagicMock()
    args.input_data = ["Test"]
    monkeypatch.setattr(cli_main, "parse_args", lambda: args)

    monkeypatch.setattr(cli_main, "load_all_flags", lambda: None)
    monkeypatch.setattr(
        cli_main,
        "flag_registry",
        MagicMock(get_pre_handlers=lambda args: [], get_post_handlers=lambda args: []),
    )
    monkeypatch.setattr(cli_main.sys, "stdin", MagicMock(isatty=lambda: True))

    # Define a mock exit that raises SystemExit
    def mock_exit(code):
        raise SystemExit(code)

    monkeypatch.setattr(cli_main.sys, "exit", mock_exit)

    # Expect SystemExit with code 1
    with pytest.raises(SystemExit) as exc_info:
        cli_main.main()
    assert exc_info.value.code == 1


def test_load_all_flags(monkeypatch):
    """Test load_all_flags dynamically imports flag modules."""
    # Mock pkgutil.iter_modules to return a dummy module
    mock_iter_modules = MagicMock(return_value=[(None, "dummy_flag", True)])
    monkeypatch.setattr(pkgutil, "iter_modules", mock_iter_modules)

    # Mock importlib.import_module
    mock_import_module = MagicMock()
    monkeypatch.setattr(importlib, "import_module", mock_import_module)

    cli_main.load_all_flags()
    mock_iter_modules.assert_called_once_with(cli_main.blackcortex_cli.flags.__path__)
    mock_import_module.assert_called_once_with("blackcortex_cli.flags.dummy_flag")


def test_parse_args(monkeypatch):
    """Test parse_args sets up the parser and applies flags."""
    # Mock flag_registry.apply_to_parser
    mock_apply_to_parser = MagicMock()
    monkeypatch.setattr(cli_main.flag_registry, "apply_to_parser", mock_apply_to_parser)

    # Mock argparse.ArgumentParser
    with patch("argparse.ArgumentParser") as mock_parser_class:
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_args.return_value = argparse.Namespace(input_data=["test"])

        # Set sys.argv for parsing
        monkeypatch.setattr(sys, "argv", ["script.py", "test"])

        result = cli_main.parse_args()
        assert result.input_data == ["test"]
        mock_parser_class.assert_called_once_with(description="BlackCortex CLI")
        mock_parser.add_argument.assert_called_once_with(
            "input_data", nargs="*", default="", help="Input text for one-shot command processing."
        )
        mock_apply_to_parser.assert_called_once_with(mock_parser)
        mock_parser.parse_args.assert_called_once()


def test_main_runs_post_handlers(monkeypatch, mock_context):
    """Test main runs post-handlers after input processing or no input."""
    monkeypatch.setattr(cli_main, "load_all_flags", lambda: None)

    args = MagicMock()
    args.input_data = []  # No input to trigger REPL
    monkeypatch.setattr(cli_main, "parse_args", lambda: args)

    handler_post = MagicMock()
    registry = MagicMock()
    registry.get_pre_handlers.return_value = []
    registry.get_post_handlers.return_value = [handler_post]
    monkeypatch.setattr(cli_main, "flag_registry", registry)

    stdin = MagicMock()
    stdin.isatty.return_value = True
    monkeypatch.setattr(cli_main.sys, "stdin", stdin)

    monkeypatch.setattr(cli_main, "console", MagicMock())
    repl_runner = MagicMock()
    monkeypatch.setattr(cli_main, "ReplRunner", lambda ctx: repl_runner)

    cli_main.main()
    handler_post.assert_called_once_with(args, mock_context)
    repl_runner.run.assert_not_called()  # Post-handler returns before REPL


def test_main_executes_post_handler(monkeypatch, mock_context):
    """Test main executes a single post-handler and returns."""
    monkeypatch.setattr(cli_main, "load_all_flags", lambda: None)

    args = MagicMock()
    args.input_data = []  # No input
    monkeypatch.setattr(cli_main, "parse_args", lambda: args)

    # Set up no pre-handlers, one post-handler
    handler_post = MagicMock()
    registry = MagicMock()
    registry.get_pre_handlers.return_value = []
    registry.get_post_handlers.return_value = [handler_post]
    monkeypatch.setattr(cli_main, "flag_registry", registry)

    # Mock stdin to simulate a terminal
    stdin = MagicMock()
    stdin.isatty.return_value = True
    monkeypatch.setattr(cli_main.sys, "stdin", stdin)

    # Mock console and ReplRunner
    monkeypatch.setattr(cli_main, "console", MagicMock())
    repl_runner = MagicMock()
    monkeypatch.setattr(cli_main, "ReplRunner", lambda ctx: repl_runner)

    cli_main.main()
    handler_post.assert_called_once_with(args, mock_context)
    repl_runner.run.assert_not_called()  # Post-handler causes return, skipping REPL


def test_main_runs_pre_and_post_handlers_no_exit(monkeypatch, mock_context):
    """Test main runs pre-handlers without exiting and reaches REPL."""
    monkeypatch.setattr(cli_main, "load_all_flags", lambda: None)

    args = MagicMock()
    args.input_data = []
    monkeypatch.setattr(cli_main, "parse_args", lambda: args)

    # Set up pre-handler only
    handler_pre = MagicMock()
    registry = MagicMock()
    registry.get_pre_handlers.return_value = [(handler_pre, False)]  # No exit
    registry.get_post_handlers.return_value = []  # No post-handlers
    monkeypatch.setattr(cli_main, "flag_registry", registry)

    # Mock stdin and console
    monkeypatch.setattr(cli_main.sys, "stdin", MagicMock(isatty=lambda: True))
    monkeypatch.setattr(cli_main, "console", MagicMock())

    # Mock REPL
    repl_runner = MagicMock()
    monkeypatch.setattr(cli_main, "ReplRunner", lambda ctx: repl_runner)

    cli_main.main()
    handler_pre.assert_called_once_with(args, mock_context)
    repl_runner.run.assert_called_once()


def test_main_handles_chat_manager_init_error(monkeypatch, mock_context):
    """Test main handles ChatManager initialization failure."""
    monkeypatch.setattr(cli_main, "load_all_flags", lambda: None)

    args = MagicMock()
    args.input_data = []
    monkeypatch.setattr(cli_main, "parse_args", lambda: args)

    # No pre/post handlers
    monkeypatch.setattr(
        cli_main,
        "flag_registry",
        MagicMock(get_pre_handlers=lambda args: [], get_post_handlers=lambda args: []),
    )

    # Mock stdin
    monkeypatch.setattr(cli_main.sys, "stdin", MagicMock(isatty=lambda: True))

    # Mock ChatManager to raise an exception
    def mock_chat_manager(config):
        raise Exception("Initialization failed")

    monkeypatch.setattr(cli_main, "ChatManager", mock_chat_manager)

    # Mock console and sys.exit
    mock_console = MagicMock()
    monkeypatch.setattr(cli_main, "console", mock_console)

    def mock_exit(code):
        raise SystemExit(code)

    monkeypatch.setattr(cli_main.sys, "exit", mock_exit)

    with pytest.raises(SystemExit) as exc_info:
        cli_main.main()
    assert exc_info.value.code == 1
    mock_context.log_manager.log_error.assert_called_once_with(
        "Failed to initialize OpenAI client: Initialization failed"
    )
    mock_console.print.assert_called_once_with(
        "[x] Failed to initialize OpenAI client: Initialization failed", style="red"
    )
