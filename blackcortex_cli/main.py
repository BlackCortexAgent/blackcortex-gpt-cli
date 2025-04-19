#!/usr/bin/env python3
"""
GPT CLI Entry Point

This script launches a command-line interface for interacting with the OpenAI API.
It supports interactive REPL or one-shot prompts, memory summarization, and various CLI options.
"""

import argparse
import sys

from openai import OpenAIError
from rich.console import Console
from rich.markdown import Markdown

from blackcortex_cli.commands.handlers import (
    command_env,
    command_ping,
    command_set_key,
    command_uninstall,
    command_update,
    command_version,
)
from blackcortex_cli.config.loader import Config
from blackcortex_cli.core.chat import ChatManager
from blackcortex_cli.logging.manager import LogManager
from blackcortex_cli.repl import ReplRunner

console = Console()
config = Config()
log_manager = LogManager(config.log_file)
chat_manager: ChatManager = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gpt",
        allow_abbrev=False,
        description="BLACKCORTEX GPT CLI — A conversational assistant with memory.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Output and streaming options
    parser.add_argument(
        "-m",
        "--no-markdown",
        dest="markdown",
        action="store_false",
        help="Disable Markdown formatting in responses",
    )
    parser.add_argument(
        "-s",
        "--stream",
        dest="stream",
        action="store_true",
        help="Stream assistant responses token-by-token",
    )

    # CLI operational flags
    parser.add_argument("-r", "--reset", action="store_true", help="Reset context memory")
    parser.add_argument("-e", "--env", action="store_true", help="Open configuration file")
    parser.add_argument("-u", "--update", action="store_true", help="Update the CLI tool")
    parser.add_argument("-x", "--uninstall", action="store_true", help="Uninstall the CLI tool")
    parser.add_argument(
        "-k",
        "--set-key",
        dest="set_key",
        nargs="?",
        const="__PROMPT__",  # Sentinel value to signal interactive prompt
        metavar="API_KEY",
        help="Set or update OpenAI API key (prompt if value omitted)",
    )
    parser.add_argument("-p", "--ping", action="store_true", help="Test OpenAI API connectivity")
    parser.add_argument("-l", "--log", action="store_true", help="Display conversation log")
    parser.add_argument("-c", "--clear-log", action="store_true", help="Clear the conversation log")
    parser.add_argument("-v", "--version", action="store_true", help="Display current version")

    parser.add_argument("input_data", nargs="*", help="Send one-shot prompt input")

    return parser.parse_args()


def handle_early_exits(args: argparse.Namespace) -> bool:
    handlers = {
        "reset": lambda: chat_manager.memory.reset(),
        "env": command_env,
        "update": command_update,
        "uninstall": command_uninstall,
        "set_key": lambda: command_set_key(None if args.set_key == "__PROMPT__" else args.set_key),
        "ping": lambda: command_ping(config.api_key),
        "log": lambda: log_manager.show(),
        "clear_log": lambda: log_manager.clear(),
        "version": command_version,
    }
    for name, handler in handlers.items():
        if getattr(args, name):
            handler()
            return True
    return False


def run_oneshot(input_data: str, args: argparse.Namespace):
    if args.stream:
        response = chat_manager.get_answer(input_data)
    else:
        response, _ = chat_manager.get_answer(input_data, return_usage=True)
        if args.markdown:
            console.print(Markdown(response))
        else:
            console.print(response)
    log_manager.write(input_data, response)


def main():
    args = parse_args()

    if handle_early_exits(args):
        return

    if not config.api_key:
        sys.stderr.write("❌ Missing OPENAI_API_KEY. Set it in your environment or .env file.\n")
        sys.exit(1)

    global chat_manager
    try:
        chat_manager = ChatManager(config=config, stream=args.stream)
    except OpenAIError as e:
        sys.stderr.write(f"❌ Failed to initialize OpenAI client: {e}\n")
        sys.exit(1)

    input_data = sys.stdin.read().strip() if not sys.stdin.isatty() else " ".join(args.input_data)
    if input_data:
        run_oneshot(input_data, args)
    else:
        ReplRunner(chat=chat_manager, log=log_manager, markdown=args.markdown).run()


if __name__ == "__main__":
    main()
