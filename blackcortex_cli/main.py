#!/usr/bin/env python3
"""
GPT CLI Entry Point

This script launches a command-line interface for interacting with the OpenAI API.
It supports interactive REPL or one-shot prompts, memory summarization, and various CLI options.
"""

import argparse
import os
import sys

from openai import OpenAI, OpenAIError
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text

from blackcortex_cli.chat import State, get_answer
from blackcortex_cli.commands import (
    command_clear_log,
    command_env,
    command_log,
    command_ping,
    command_set_key,
    command_uninstall,
    command_update,
    command_version,
)
from blackcortex_cli.config import api_key, memory_path
from blackcortex_cli.logging import write_to_log
from blackcortex_cli.memory import load_memory, reset_memory

console = Console()


def run_interactive(markdown: bool):
    """
    Start an interactive REPL session for user input and assistant response.

    This function initializes a prompt session with command history and auto-suggestions.
    It captures user input, fetches a response from the OpenAI API, renders it with optional
    Markdown formatting, and logs the interaction. Users can exit the session with 'exit' or 'quit'.
    """
    console.print("[bold green]🧠 GPT CLI is ready. Type 'exit' to quit.[/bold green]\n")
    session = PromptSession(
        history=FileHistory(os.path.expanduser("~/.gpt_history")),
        auto_suggest=AutoSuggestFromHistory(),
    )
    while True:
        try:
            with patch_stdout():
                user_input = session.prompt(
                    HTML("<ansibrightblue><b>You: </b></ansibrightblue>"),
                    color_depth=ColorDepth.TRUE_COLOR,
                ).strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                console.print("\n[bold yellow]Goodbye![/bold yellow]")
                break
            console.print(Text("GPT:", style="bold green"), end=" ")
            response = get_answer(user_input)
            console.print(Markdown(response) if markdown else response)
            console.rule(style="grey")
            console.print()
            write_to_log(user_input, response)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
        except (OpenAIError, RuntimeError) as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}\n")


def handle_early_exits(args) -> bool:
    """
    Handle early-exit command-line flags such as --reset, --env, etc.

    Executes associated side-effect commands and returns True if any matched,
    terminating the normal CLI flow afterward.
    """
    handlers = {
        "reset": lambda: reset_memory(memory_path),
        "env": command_env,
        "update": command_update,
        "uninstall": command_uninstall,
        "set_key": lambda: command_set_key(args.set_key),
        "ping": lambda: command_ping(api_key),
        "log": lambda: command_log(),
        "clear_log": lambda: command_clear_log(),
        "version": command_version,
    }
    for arg_name, handler in handlers.items():
        if getattr(args, arg_name):
            handler()
            return True
    return False


def main():
    """
    Main entry point for the GPT CLI application.

    Parses command-line arguments, sets up the OpenAI client, loads memory state,
    and dispatches to either REPL or one-shot prompt mode depending on input.
    Handles early-exit commands and validates required environment configuration.
    """
    parser = argparse.ArgumentParser(
        prog="gpt",
        allow_abbrev=False,
        description="BLACKCORTEX GPT CLI — A conversational assistant with memory.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--no-markdown", dest="markdown", action="store_false", help="Disable Markdown formatting"
    )
    parser.set_defaults(markdown=True)
    parser.add_argument(
        "--stream", dest="stream", action="store_true", help="Enable streaming responses"
    )
    parser.set_defaults(stream=False)
    for flag in [
        "reset",
        "summary",
        "env",
        "ping",
        "log",
        "clear_log",
        "update",
        "uninstall",
        "version",
    ]:
        parser.add_argument(
            f"--{flag.replace('_', '-')}",
            dest=flag,
            action="store_true",
            help=f"{flag.replace('_', ' ').capitalize()}",
        )
    parser.add_argument(
        "--set-key", nargs="?", const=None, metavar="API_KEY", help="Update the API key"
    )
    parser.add_argument("input_data", nargs="*", help="One-shot prompt input")
    args = parser.parse_args()

    State.stream_enabled = args.stream
    if handle_early_exits(args):
        return
    if not api_key:
        sys.stderr.write("❌ Missing OPENAI_API_KEY. Set it in your environment or .env file.\n")
        sys.exit(1)
    try:
        State.client = OpenAI(api_key=api_key)
    except OpenAIError as e:
        sys.stderr.write(f"❌ Failed to initialize OpenAI client: {e}\n")
        sys.exit(1)
    State.rolling_summary, State.recent_messages = load_memory(memory_path)
    input_data = sys.stdin.read().strip() if not sys.stdin.isatty() else " ".join(args.input_data)
    if input_data:
        response = get_answer(input_data)
        if not args.stream:
            console.print(Markdown(response) if args.markdown else response)
        write_to_log(input_data, response)
    else:
        run_interactive(args.markdown)


if __name__ == "__main__":
    main()
