"""
Main entry point for the BlackCortex GPT CLI.

This module initializes the CLI, parses command-line arguments, sets up the configuration,
and either processes a one-shot command or starts the REPL interface.
"""

import argparse
import importlib
import pkgutil
import sys

import blackcortex_cli.flags
from blackcortex_cli.config.config import Config
from blackcortex_cli.core.chat_manager import ChatManager
from blackcortex_cli.core.context import Context
from blackcortex_cli.core.flag_registry import flag_registry
from blackcortex_cli.core.log_manager import LogManager
from blackcortex_cli.repl import ReplRunner
from blackcortex_cli.utils.console import console


def load_all_flags() -> None:
    """
    Dynamically load all flag modules from the flags package.

    Iterates through modules in the blackcortex_cli.flags package and imports them,
    registering their flags in the global flag registry.
    """
    for _, name, _ in pkgutil.iter_modules(blackcortex_cli.flags.__path__):
        importlib.import_module(f"blackcortex_cli.flags.{name}")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Sets up the CLI parser, applies all registered flags, and returns parsed arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="BlackCortex CLI")
    parser.add_argument(
        "input_data", nargs="*", default="", help="Input text for one-shot command processing."
    )
    flag_registry.apply_to_parser(parser)
    return parser.parse_args()


def run_oneshot(input_data: str, args: argparse.Namespace, context: Context) -> None:
    """
    Handle a one-shot command with input text and print the result.

    Args:
        input_data (str): Text prompt to send to the assistant.
        args (argparse.Namespace): Parsed CLI arguments.
        context (Context): Runtime context containing configuration and managers.
    """
    try:
        chat_manager = context.chat_manager
        response, token_usage, timestamp = chat_manager.get_answer(input_data, return_usage=True)

        if not context.config.stream_enabled:
            if context.config.markdown_enabled:
                from rich.markdown import Markdown

                console.print(Markdown(response))
            else:
                console.print(response)

        context.log_manager.write(input_data, response, token_usage)
    except Exception as e:
        context.log_manager.log_error(f"Error in one-shot command: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def main() -> None:
    """
    Launch the BlackCortex GPT CLI.

    Loads flags, parses arguments, configures services, and executes either a one-shot command
    or launches the REPL interface.
    """
    load_all_flags()
    args = parse_args()

    config = Config()
    log_manager = LogManager(config.log_file, config.log_level)
    context = Context(config, log_manager)

    for handler, exit_after in flag_registry.get_pre_handlers(args):
        handler(args, context)
        if exit_after:
            return

    if not config.api_key:
        log_manager.log_error("Missing OPENAI_API_KEY")
        console.print(
            "[x] Missing OPENAI_API_KEY. Set it in your environment or .env file.", style="red"
        )
        sys.exit(1)

    try:
        chat_manager = ChatManager(config)
        context.chat_manager = chat_manager
    except Exception as e:
        log_manager.log_error(f"Failed to initialize OpenAI client: {e}")
        console.print(f"[x] Failed to initialize OpenAI client: {e}", style="red")
        sys.exit(1)

    for handler in flag_registry.get_post_handlers(args):
        handler(args, context)
        return

    input_data = sys.stdin.read().strip() if not sys.stdin.isatty() else " ".join(args.input_data)

    if input_data:
        run_oneshot(input_data, args, context)
    else:
        ReplRunner(context).run()


if __name__ == "__main__":
    main()
