#!/usr/bin/env python3

import os
import sys
import json
import shutil
import argparse
from datetime import datetime
from openai import OpenAI, OpenAIError
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from prompt_toolkit import prompt, PromptSession
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML

from core.config import *
from core.commands import *
from core.memory import *

# === Runtime ===
console = Console()
client: OpenAI = None
rolling_summary = ""
recent_messages = []

MEMORY_INTRO = f"""You are a CLI assistant with limited, simulated memory. You do not have full access to past conversations,
but you may be provided with a rolling summary and the {memory_limit} most recent user-assistant exchanges.
When {memory_limit * 2} messages have accumulated, the system summarizes them to maintain context.

The user is interacting with you via the GPT CLI tool. The CLI supports the following commands:

--reset         Reset memory and exit.
--summary       Print the current memory summary.
--env           Edit the configuration file (.env).
--set-key       Set the OpenAI API key in the .env file.
--log           Show the conversation log.
--clear-log     Delete the conversation log.
--uninstall     Remove the CLI from the system.
"Input text"    Provide a one-shot prompt to receive a reply.

You can explain or refer to these options if the user asks how to use the GPT CLI.

Use only the information given to you. If something is missing or unclear, say so honestly.
Do not guess or fabricate facts from previous interactions."""

# === Answer Logic ===
def get_answer_blocking(prompt_text: str) -> str:
    global rolling_summary, recent_messages

    recent_messages.append({"role": "user", "content": prompt_text})

    messages = [{"role": "system", "content": f"INTRO: {MEMORY_INTRO}"}]
    if default_prompt:
        messages.append({"role": "system", "content": f"INSTRUCTIONS: {default_prompt}"})
    if rolling_summary:
        messages.append({"role": "system", "content": f"SUMMARY: {rolling_summary}"})
    messages.extend(recent_messages[-memory_limit:])

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except OpenAIError as e:
        return f"❌ OpenAI API error: {e}"

    reply = response.choices[0].message.content.strip()
    recent_messages.append({"role": "assistant", "content": reply})

    if len(recent_messages) >= memory_limit * 2:
        rolling_summary, recent_messages = summarize_recent(
            client, model, memory_path, rolling_summary, recent_messages, memory_limit, max_summary_tokens
        )

    save_memory(memory_path, rolling_summary, recent_messages)
    return reply

def get_answer_streaming(prompt_text: str) -> str:
    global rolling_summary, recent_messages

    recent_messages.append({"role": "user", "content": prompt_text})

    messages = [{"role": "system", "content": f"INTRO: {MEMORY_INTRO}"}]
    if default_prompt:
        messages.append({"role": "system", "content": f"INSTRUCTIONS: {default_prompt}"})
    if rolling_summary:
        messages.append({"role": "system", "content": f"SUMMARY: {rolling_summary}"})
    messages.extend(recent_messages[-memory_limit:])

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
    except OpenAIError as e:
        return f"❌ OpenAI API error: {e}"

    full_reply = ""
    console.print()
    console.print(Text("GPT:", style="bold"))

    for chunk in stream:
        content = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
        if content:
            full_reply += content
            print(content, end="", flush=True)

    print()
    console.print()

    recent_messages.append({"role": "assistant", "content": full_reply})

    if len(recent_messages) >= memory_limit * 2:
        rolling_summary, recent_messages = summarize_recent(
            client, model, memory_path, rolling_summary, recent_messages, memory_limit, max_summary_tokens
        )

    save_memory(memory_path, rolling_summary, recent_messages)
    return full_reply

def get_answer(prompt_text: str) -> str:
    return get_answer_streaming(prompt_text) if stream_enabled else get_answer_blocking(prompt_text)

# === Output ===
def write_to_log(prompt_text: str, response: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if log_file:
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] Prompt:\n{prompt_text}\n\nResponse:\n{response}\n{'-'*80}\n")
        os.chmod(log_file, 0o600)

def clear_last_lines(n: int = 1):
    for _ in range(n):
        sys.stdout.write("\033[F\033[K")
    sys.stdout.flush()

def clear_input_lines(user_input: str, prompt_text: str = "You: "):
    width = shutil.get_terminal_size().columns
    lines = (len(prompt_text) + len(user_input)) // width + 1
    clear_last_lines(lines)

# === REPL Mode ===
def run_interactive(markdown: bool):
    console.print("[bold green]🧠 GPT CLI is ready. Type your question or 'exit' to quit.[/bold green]\n")

    session = PromptSession(
        history=FileHistory(os.path.expanduser("~/.gpt_history")),
        auto_suggest=AutoSuggestFromHistory()
    )

    while True:
        try:
            with patch_stdout():
                user_input = session.prompt(
                    HTML('<ansibrightblue><b>You:</b></ansibrightblue> '),
                    color_depth=ColorDepth.TRUE_COLOR
                ).strip()

            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                console.print("\n[bold yellow]Goodbye![/bold yellow]")
                break

            clear_input_lines(user_input)
            console.print(Text("You", style="bright_blue bold"))
            console.print(Markdown(user_input) if markdown else user_input)

            with console.status("", spinner="simpleDots"):
                response = get_answer(user_input)

            if not stream_enabled:
                console.print()
                console.print(Text("Assistant", style="bright_magenta bold"))
                console.print(Markdown(response) if markdown else response)
                console.print()
                console.rule(style="grey")
                console.print()
            
            write_to_log(user_input, response)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}\n")

# === Main Entrypoint ===
def main():
    global rolling_summary, recent_messages, client

    parser = argparse.ArgumentParser(
        prog='gpt',
        allow_abbrev=False,
        description='🧠 GPT CLI — A conversational assistant with memory, config, and logging features.',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('--no-markdown', dest='markdown', action='store_false', help='Disable Markdown formatting')
    parser.set_defaults(markdown=True)

    parser.add_argument('--reset', action='store_true', help='Reset memory and exit')
    parser.add_argument('--summary', action='store_true', help='Show the current memory summary')
    parser.add_argument('--env', action='store_true', help='Edit the .env file')
    parser.add_argument('--set-key', nargs='?', const=None, metavar='API_KEY', help='Update the API key')
    parser.add_argument('--ping', action='store_true', help='Ping OpenAI API')
    parser.add_argument('--log', action='store_true', help='Print conversation log')
    parser.add_argument('--clear-log', action='store_true', help='Clear the log')
    parser.add_argument('--update', action='store_true', help='Update GPT CLI')
    parser.add_argument('--uninstall', action='store_true', help='Uninstall GPT CLI')
    parser.add_argument('input_data', nargs='*', help='One-shot prompt input')

    args = parser.parse_args()

    if args.reset:
        reset_memory(memory_path)
        return
    if args.env: return command_env()
    if args.update: return command_update()
    if args.uninstall: return command_uninstall()
    if args.set_key is not None or '--set-key' in sys.argv:
        return command_set_key(args.set_key)
    if args.ping: return command_ping(api_key)
    if args.log: return command_log(log_file)
    if args.clear_log: return command_clear_log(log_file)

    try:
        if not api_key:
            sys.stderr.write("❌ Missing OPENAI_API_KEY. Set it in your environment or .env file.\n")
            sys.exit(1)
        client = OpenAI(api_key=api_key)
    except OpenAIError as e:
        sys.stderr.write(f"❌ Failed to initialize OpenAI client: {e}\n")
        sys.exit(1)

    # Load memory from file
    rolling_summary, recent_messages = load_memory(memory_path)

    input_data = sys.stdin.read().strip() if not sys.stdin.isatty() else ' '.join(args.input_data)
    if input_data:
        response = get_answer_blocking(input_data)
        console.print(Markdown(response) if args.markdown else response)
        write_to_log(input_data, response)
    else:
        run_interactive(args.markdown)

if __name__ == '__main__':
    main()
