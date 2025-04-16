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
from prompt_toolkit.output import ColorDepth, DummyOutput
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML

# === Configuration Defaults ===
DEFAULT_MODEL = "gpt-4o"
DEFAULT_PROMPT = ""
DEFAULT_LOG_PATH = "~/.gpt.log"
DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_TOKENS = 4096
DEFAULT_MAX_SUMMARY_TOKENS = 2048
DEFAULT_MEMORY_PATH = "~/.gpt_memory.json"
DEFAULT_STREAM = "false"
DEFAULT_MEMORY_LIMIT = 10

# === Load .env if available ===
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# === Environment Setup ===
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL', DEFAULT_MODEL)
default_prompt = os.getenv('OPENAI_DEFAULT_PROMPT', DEFAULT_PROMPT)
log_file = os.path.expanduser(os.getenv('OPENAI_LOGFILE', DEFAULT_LOG_PATH))
temperature = float(os.getenv('OPENAI_TEMPERATURE', DEFAULT_TEMPERATURE))
max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', DEFAULT_MAX_TOKENS))
max_summary_tokens = int(os.getenv('OPENAI_MAX_SUMMARY_TOKENS', DEFAULT_MAX_SUMMARY_TOKENS))
memory_path = os.path.expanduser(os.getenv('OPENAI_MEMORY_PATH', DEFAULT_MEMORY_PATH))
memory_limit = int(os.getenv('OPENAI_MEMORY_LIMIT', DEFAULT_MEMORY_LIMIT))
stream_enabled = os.getenv('OPENAI_STREAM_ENABLED', DEFAULT_STREAM).lower() == 'true'

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

# Prepare client variable
client: OpenAI
console = Console()
rolling_summary = ""
recent_messages = []

# === Memory Management ===
def load_memory():
    global rolling_summary, recent_messages
    if os.path.exists(memory_path):
        with open(memory_path, 'r') as f:
            data = json.load(f)
            rolling_summary = data.get("summary", "")
            recent_messages = data.get("recent", [])
    else:
        reset_memory()

def save_memory():
    with open(memory_path, 'w') as f:
        json.dump({"summary": rolling_summary, "recent": recent_messages}, f, indent=2)
    os.chmod(memory_path, 0o600)

def reset_memory():
    global rolling_summary, recent_messages
    rolling_summary = ""
    recent_messages = []
    if os.path.exists(memory_path):
        os.remove(memory_path)
        console.print("[bold yellow]🧹 Memory reset.[/bold yellow]\n")

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
        summarize_recent()

    save_memory()
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
    console.print()  # spacing before
    console.print(Text("GPT:", style="bold"))

    for chunk in stream:
        content = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
        if content:
            full_reply += content
            print(content, end="", flush=True)

    print()  # newline
    console.print()  # spacing after

    recent_messages.append({"role": "assistant", "content": full_reply})

    if len(recent_messages) >= memory_limit * 2:
        summarize_recent()

    save_memory()
    return full_reply

def get_answer(prompt_text: str) -> str:
    return get_answer_streaming(prompt_text) if stream_enabled else get_answer_blocking(prompt_text)

def summarize_recent():
    global rolling_summary, recent_messages

    batch = recent_messages[-(memory_limit * 2):]
    summary_prompt = (
        f"Here is the current summary of our conversation:\n{rolling_summary}\n\n"
        f"Please update it with the following messages:\n" +
        "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in batch])
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a summarizer that maintains a concise summary of a conversation."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0,
            max_tokens=max_summary_tokens
        )
        rolling_summary = response.choices[0].message.content.strip()
        recent_messages.clear()
    except OpenAIError as e:
        console.print(f"[bold red]Summary failed:[/bold red] {e}")

# === Output ===
def write_to_log(prompt_text: str, response: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if log_file:
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] Prompt:\n{prompt_text}\n\nResponse:\n{response}\n{'-'*80}\n")
        os.chmod(log_file, 0o600)

def print_response(response: str):
    console.print()  # spacing before
    console.print(Text("GPT:", style="bold"))
    console.print(Markdown(response))
    console.print()  # spacing after

def clear_last_lines(n: int = 1):
    # Move up and clear each of the last n lines
    for _ in range(n):
        sys.stdout.write("\033[F\033[K")
    sys.stdout.flush()

def clear_input_lines(user_input: str, prompt_text: str = "You: "):
    width = shutil.get_terminal_size().columns
    total_len = len(prompt_text) + len(user_input)
    lines = (total_len // width) + 1  # Add 1 to always cover remainder
    clear_last_lines(lines)

# === Main Loop ===
def run_interactive(markdown: bool):
    console.print("[bold green]🧠 GPT CLI is ready. Type your question or 'exit' to quit.[/bold green]\n")

    session = PromptSession(
        history=FileHistory(os.path.expanduser("~/.gpt_history")),
        auto_suggest=AutoSuggestFromHistory()
    )
    
    while True:
        try:
            with patch_stdout():
                user_input = session.prompt(HTML('<ansibrightblue><b>You:</b></ansibrightblue> '), color_depth=ColorDepth.TRUE_COLOR).strip()

            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                console.print("\n[bold yellow]Goodbye![/bold yellow]")
                break

            clear_input_lines(user_input)
            console.print(Text("You", style="bright_blue bold"))
            if markdown:
                console.print(Markdown(user_input))
            else:
                console.print(user_input)

            response = get_answer(user_input)
            if not stream_enabled:
                console.print()
                console.print(Text("Assistant", style="bright_magenta bold"))
                if markdown:
                    console.print(Markdown(response))
                else:
                    console.print(response)
                console.print()
                console.rule(style="grey")
                console.print()
            
            write_to_log(user_input, response)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}\n")

def command_env():
    env_path = os.path.expanduser("~/.gpt-cli/.env")
    os.makedirs(os.path.dirname(env_path), exist_ok=True)
    editor = os.getenv('EDITOR', 'nano')
    os.system(f"{editor} {env_path}")

def command_uninstall():
    uninstall_path = os.path.expanduser("~/.gpt-cli/uninstall.sh")
    if os.path.isfile(uninstall_path):
        os.system(f"bash {uninstall_path}")
    else:
        console.print("[bold red]❌ uninstall.sh not found in ~/.gpt-cli[/bold red]")

def command_set_key(key):
    if key is None:
        console.print("[bold yellow]🔐 No API key provided. Please enter your OpenAI API key:[/bold yellow]")
        key = prompt("API Key: ").strip()
    
    console.print("[bold cyan]🔑 Validating API key...[/bold cyan]")
    try:
        temp_client = OpenAI(api_key=key)
        temp_client.models.list()
    except OpenAIError as e:
        console.print(f"[bold red]❌ Invalid API key:[/bold red] {e}")
        return

    # If validation passed, write to .env
    env_path = os.path.expanduser("~/.gpt-cli/.env")
    os.makedirs(os.path.dirname(env_path), exist_ok=True)

    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    with open(env_path, "w") as f:
        found = False
        for line in lines:
            # Check if the line contains OPENAI_API_KEY, regardless of position or comment
            if "OPENAI_API_KEY=" in line:
                f.write(f"OPENAI_API_KEY={key}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"OPENAI_API_KEY={key }\n")

    console.print("[bold green]✅ API key saved and validated.[/bold green]")

def command_log():
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            console.print(f.read())
    else:
        console.print("[yellow]⚠️ No log file found.[/yellow]")

def command_clear_log():
    if os.path.exists(log_file):
        os.remove(log_file)
        console.print("[bold green]🗑 Log file deleted.[/bold green]")
    else:
        console.print("[yellow]⚠️ No log file to delete.[/yellow]")

def command_summary(markdown: bool):
    load_memory()
    if rolling_summary:
        console.print("[bold cyan]📋 Current Summary:[/bold cyan]\n")
        if markdown:
            console.print(Markdown(rolling_summary))
        else:
            console.print(rolling_summary)
    else:
        console.print("[yellow]⚠️ No summary available yet.[/yellow]")

def main():
    parser = argparse.ArgumentParser(
        prog='gpt',
        description='🧠 GPT CLI — A conversational assistant with memory, config, and logging features.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    # Settings
    parser.add_argument(
        '--no-markdown',
        dest='markdown',
        action='store_false',
        help='Disable Markdown formatting in responses'
    )
    parser.set_defaults(markdown=True)

    # Optional utilities
    parser.add_argument('--reset', action='store_true', help='Reset memory and exit')
    parser.add_argument('--summary', action='store_true', help='Show the current memory summary')
    parser.add_argument('--env', action='store_true', help='Edit the .env file')
    parser.add_argument('--set-key', nargs='?', const=None, metavar='API_KEY', help='Update and validate the OpenAI API key in .env (optional: pass key or use interactive mode)')

    # Logs
    parser.add_argument('--log', action='store_true', help='Print conversation log')
    parser.add_argument('--clear-log', action='store_true', help='Delete the conversation log')

    # System
    parser.add_argument('--uninstall', action='store_true', help='Uninstall GPT CLI from your system')
    parser.add_argument('input_data', nargs='*', help='Input text for one-shot use')

    args = parser.parse_args()

    if args.reset:
        reset_memory()
        return
    
    if args.env:
        command_env()
        return
    
    if args.uninstall:
        command_uninstall()
        return
    
    if args.set_key is not None or '--set-key' in sys.argv:
        command_set_key(args.set_key)
        return

    if args.log:
        command_log()
        return

    if args.clear_log:
        command_clear_log()
        return
    
    if args.summary:
        command_summary(args.markdown)
        return

    # === Setup ===
    try:
        if not api_key:
            sys.stderr.write("❌ Missing OPENAI_API_KEY. Set it in your environment or .env file.\n")
            sys.exit(1)

        global client
        client = OpenAI(api_key=api_key)
    except OpenAIError as e:
        sys.stderr.write(f"❌ Failed to initialize OpenAI client: {e}\n")
        sys.exit(1)

    load_memory()

    if not sys.stdin.isatty():
        input_data = sys.stdin.read().strip()
    else:
        input_data = ' '.join(args.input_data)

    if input_data:
        response = get_answer_blocking(input_data)
        if args.markdown:
            console.print(Markdown(response))
        else:
            console.print(response)
        write_to_log(input_data, response)
    else:
        run_interactive(args.markdown)

if __name__ == '__main__':
    main()
