#!/usr/bin/env python3

import os
import sys
import json
import argparse
from datetime import datetime
from openai import OpenAI, OpenAIError
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

# === Configuration Defaults ===
DEFAULT_MODEL = "gpt-4o"
DEFAULT_PROMPT = ""
DEFAULT_LOG_PATH = "~/.gpt.log"
DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_TOKENS = 4096
DEFAULT_MAX_SUMMARY_TOKENS = 2048
DEFAULT_MEMORY_PATH = "~/.gpt_memory.json"
DEFAULT_STREAM = "false"

MEMORY_INTRO = (
    "You are part of a CLI tool that retains memory across interactions."
    "You have access to a summary of prior conversations and the last 10 exchanges."
    "Answer as if you remember, even though memory is summarized and windowed."
)

# === Load .env if available ===
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# === Environment Setup ===
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    sys.stderr.write("❌ Missing OPENAI_API_KEY. Set it in your environment or .env file.\n")
    sys.exit(1)

model = os.getenv('OPENAI_MODEL', DEFAULT_MODEL)
default_prompt = os.getenv('OPENAI_DEFAULT_PROMPT', DEFAULT_PROMPT)
log_file = os.path.expanduser(os.getenv('OPENAI_LOGFILE', DEFAULT_LOG_PATH))
temperature = float(os.getenv('OPENAI_TEMPERATURE', DEFAULT_TEMPERATURE))
max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', DEFAULT_MAX_TOKENS))
max_summary_tokens = int(os.getenv('OPENAI_MAX_SUMMARY_TOKENS', DEFAULT_MAX_SUMMARY_TOKENS))
memory_path = os.path.expanduser(os.getenv('OPENAI_MEMORY_PATH', DEFAULT_MEMORY_PATH))
stream_enabled = os.getenv('OPENAI_STREAM_ENABLED', DEFAULT_STREAM).lower() == 'true'

# === Setup ===
try:
    client = OpenAI(api_key=api_key)
except OpenAIError as e:
    sys.stderr.write(f"❌ Failed to initialize OpenAI client: {e}\n")
    sys.exit(1)

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

    messages = [{"role": "system", "content": MEMORY_INTRO}]
    if default_prompt:
        messages.append({"role": "system", "content": default_prompt})
    if rolling_summary:
        messages.append({"role": "system", "content": f"Conversation summary so far: {rolling_summary}"})
    messages.extend(recent_messages[-10:])

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

    if len(recent_messages) >= 20:
        summarize_recent()

    save_memory()
    return reply

def get_answer_streaming(prompt_text: str) -> str:
    global rolling_summary, recent_messages

    recent_messages.append({"role": "user", "content": prompt_text})

    messages = [{"role": "system", "content": MEMORY_INTRO}]
    if default_prompt:
        messages.append({"role": "system", "content": default_prompt})
    if rolling_summary:
        messages.append({"role": "system", "content": f"Conversation summary so far: {rolling_summary}"})
    messages.extend(recent_messages[-10:])

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

    if len(recent_messages) >= 20:
        summarize_recent()

    save_memory()
    return full_reply

def get_answer(prompt_text: str) -> str:
    return get_answer_streaming(prompt_text) if stream_enabled else get_answer_blocking(prompt_text)

def summarize_recent():
    global rolling_summary, recent_messages

    batch = recent_messages[-20:]
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

def print_response(response: str):
    console.print()  # spacing before
    console.print(Text("GPT:", style="bold"))
    console.print(Markdown(response))
    console.print()  # spacing after

# === Main Loop ===
def run_interactive():
    console.print("[bold green]🧠 GPT CLI is ready. Type your question or 'exit' to quit.[/bold green]\n")
    while True:
        try:
            user_input = prompt(
                "You: ",
                history=FileHistory(os.path.expanduser("~/.gpt_history")),
                auto_suggest=AutoSuggestFromHistory()
            ).strip()

            # Clear the last input line
            sys.stdout.write("\033[F\033[K")
            sys.stdout.flush()

            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                console.print("\n[bold yellow]Goodbye![/bold yellow]")
                break

            console.print(Text("You:", style="bold"))
            console.print(Markdown(user_input))

            response = get_answer(user_input)
            if not stream_enabled:
                console.print()  # spacing before
                console.print(Text("GPT:", style="bold"))
                console.print(Markdown(response))
                console.print()  # spacing before
            write_to_log(user_input, response)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}\n")

def main():
    parser = argparse.ArgumentParser(description='GPT CLI with memory window and summary update.')
    parser.add_argument('--reset', action='store_true', help='Reset memory and exit')
    parser.add_argument('--env', action='store_true', help='Edit the .env file and exit')
    parser.add_argument('input_data', nargs='*', help='Input text for one-shot use')
    args = parser.parse_args()

    if args.reset:
        reset_memory()
        return
    
    if args.env:
        env_path = os.path.expanduser("~/.gpt-cli/.env")
        os.makedirs(os.path.dirname(env_path), exist_ok=True)
        editor = os.getenv('EDITOR', 'nano')
        os.system(f"{editor} {env_path}")
        return
    
    load_memory()

    if not sys.stdin.isatty():
        input_data = sys.stdin.read().strip()
    else:
        input_data = ' '.join(args.input_data)

    if input_data:
        response = get_answer_blocking(input_data)
        console.print(response)
        write_to_log(input_data, response)
    else:
        run_interactive()

if __name__ == '__main__':
    main()
