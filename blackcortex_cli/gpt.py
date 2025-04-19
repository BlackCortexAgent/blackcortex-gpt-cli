#!/usr/bin/env python3
"""
GPT CLI Entry Point

This script launches a command-line interface for interacting with the OpenAI API.
It supports interactive REPL or one-shot prompts, memory summarization, and various CLI options.
"""

import argparse
import os
import sys
from datetime import datetime

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
from blackcortex_cli.config import (
    api_key,
    default_prompt,
    log_file,
    max_summary_tokens,
    max_tokens,
    memory_limit,
    memory_path,
    model,
    temperature,
)
from blackcortex_cli.config import (
    stream_enabled as config_stream_enabled,
)
from blackcortex_cli.memory import load_memory, reset_memory, save_memory, summarize_recent

# === Runtime ===
console = Console()


class State:
    """Shared runtime state for the GPT CLI session."""

    client = None
    stream_enabled = config_stream_enabled
    rolling_summary = ""
    recent_messages = []


MEMORY_INTRO = f"""This is a CLI environment with simulated memory.
You do not have full access to previous conversations, but you may receive a rolling summary
and the {memory_limit} most recent user-assistant message pairs.
Once {memory_limit * 2} messages are reached, a summary is generated to retain context while
conserving memory.

The interface is powered by the GPT CLI tool, which supports the following command-line options:

positional arguments:
  input_data           One-shot prompt input

options:
  -h, --help           Show this help message and exit
  --no-markdown        Disable Markdown formatting
  --stream             Enable streaming responses
  --reset              Reset memory and exit
  --summary            Show the current memory summary
  --env                Edit the .env file
  --set-key [API_KEY]  Update the API key
  --ping               Ping OpenAI API
  --log                Print conversation log
  --clear-log          Clear the log
  --update             Update GPT CLI
  --uninstall          Uninstall GPT CLI
"""


# === Answer Logic ===
def get_answer_blocking(prompt_text: str) -> str:
    """Get OpenAI response synchronously (non-streaming)."""
    State.recent_messages.append({"role": "user", "content": prompt_text})

    messages = build_messages()

    try:
        response = State.client.chat.completions.create(
            model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
        )
    except OpenAIError as e:
        return f"❌ OpenAI API error: {e}"

    reply = response.choices[0].message.content.strip()
    State.recent_messages.append({"role": "assistant", "content": reply})

    check_memory_limit()
    return reply


def get_answer_streaming(prompt_text: str) -> str:
    """Get OpenAI response using streaming."""
    State.recent_messages.append({"role": "user", "content": prompt_text})
    messages = build_messages()

    try:
        stream = State.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
    except OpenAIError as e:
        return f"❌ OpenAI API error: {e}"

    full_reply = ""
    for chunk in stream:
        content = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
        if content:
            full_reply += content
            console.print(content, end="", soft_wrap=True)
    console.print()

    State.recent_messages.append({"role": "assistant", "content": full_reply})
    check_memory_limit()
    return full_reply


def get_answer(prompt_text: str) -> str:
    """Get an OpenAI response based on current streaming config."""
    return (
        get_answer_streaming(prompt_text)
        if State.stream_enabled
        else get_answer_blocking(prompt_text)
    )


def build_messages():
    """Assemble messages for the OpenAI API call."""
    messages = [{"role": "system", "content": f"INTRO: {MEMORY_INTRO}"}]
    if default_prompt:
        messages.append({"role": "system", "content": f"INSTRUCTIONS: {default_prompt}"})
    if State.rolling_summary:
        messages.append({"role": "system", "content": f"SUMMARY: {State.rolling_summary}"})
    messages.extend(State.recent_messages[-memory_limit:])
    return messages


def check_memory_limit():
    """Summarize memory if recent messages exceed threshold."""
    if len(State.recent_messages) >= memory_limit * 2:
        State.rolling_summary, State.recent_messages = summarize_recent(
            State.client,
            model,
            memory_path,
            State.rolling_summary,
            State.recent_messages,
            memory_limit,
            max_summary_tokens,
        )
    save_memory(memory_path, State.rolling_summary, State.recent_messages)


# === Output ===
def write_to_log(prompt_text: str, response: str):
    """Write prompt/response to log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Prompt:\n{prompt_text}\n\nResponse:\n{response}\n{'-' * 80}\n")
        os.chmod(log_file, 0o600)


# === REPL Mode ===
def run_interactive(markdown: bool):
    """Launch REPL prompt session."""
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


# === Early Exit Command Handlers ===
def handle_early_exits(args) -> bool:
    """Process early-exit flags such as --reset, --env, etc."""
    handlers = {
        "reset": lambda: reset_memory(memory_path),
        "env": command_env,
        "update": command_update,
        "uninstall": command_uninstall,
        "set_key": lambda: command_set_key(args.set_key),
        "ping": lambda: command_ping(api_key),
        "log": lambda: command_log(log_file),
        "clear_log": lambda: command_clear_log(log_file),
        "version": lambda: command_version(),
    }

    for arg_name, handler in handlers.items():
        if getattr(args, arg_name):
            handler()
            return True

    return False


# === Main Entrypoint ===
def main():
    """Main function for GPT CLI."""
    parser = argparse.ArgumentParser(
        prog="gpt",
        allow_abbrev=False,
        description=(
            "BLACKCORTEX GPT CLI — A conversational assistant with memory, "
            "config, and logging features."
        ),
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

    try:
        if not api_key:
            sys.stderr.write(
                "❌ Missing OPENAI_API_KEY. Set it in your environment or .env file.\n"
            )
            sys.exit(1)
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
