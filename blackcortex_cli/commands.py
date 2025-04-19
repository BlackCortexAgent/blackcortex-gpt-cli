"""
This module provides CLI commands for managing GPT-CLI configuration,
OpenAI API key, logs, updates, and environment setup.
"""

import os
import shutil
import subprocess

from openai import OpenAI, OpenAIError
from prompt_toolkit import prompt
from rich.console import Console
from rich.markdown import Markdown

console = Console()
ENV_PATH = os.path.expanduser("~/.gpt-cli/.env")


def command_env():
    """Open the .env configuration file in the user's default editor."""
    os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
    editor = os.getenv("EDITOR", "nano")
    try:
        subprocess.run([editor, ENV_PATH], check=True)
    except Exception as e:
        console.print(f"[bold red]❌ Failed to open editor:[/bold red] {e}")


def command_update():
    """Update the GPT CLI tool via pip or pipx."""
    console.print("[bold cyan]🔄 Updating GPT CLI...[/bold cyan]")
    try:
        if shutil.which("pipx"):
            subprocess.run(["pipx", "upgrade", "konijima-gpt-cli"], check=True)
        else:
            subprocess.run(["pip", "install", "--upgrade", "konijima-gpt-cli"], check=True)
        console.print("[bold green]✅ GPT CLI updated successfully.[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Update failed:[/bold red] {e}")
        console.print(
            "💡 You can manually upgrade with "
            "'pip install --upgrade konijima-gpt-cli' or "
            "'pipx upgrade konijima-gpt-cli'"
        )


def command_uninstall():
    """Uninstall the GPT CLI tool via pip or pipx."""
    console.print("[bold cyan]🗑️ Uninstalling GPT CLI...[/bold cyan]")
    try:
        if shutil.which("pipx"):
            subprocess.run(["pipx", "uninstall", "konijima-gpt-cli"], check=True)
        else:
            subprocess.run(["pip", "uninstall", "-y", "konijima-gpt-cli"], check=True)
        console.print("[bold green]✅ GPT CLI uninstalled successfully.[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Uninstall failed:[/bold red] {e}")
        console.print(
            "💡 You can manually uninstall with "
            "'pip uninstall konijima-gpt-cli' or "
            "'pipx uninstall konijima-gpt-cli'"
        )


def command_set_key(api_key):
    """Set and validate the OpenAI API key, saving it to the .env file."""
    if api_key is None:
        console.print(
            "[bold yellow]🔐 No API key provided. Please enter your OpenAI API key:[/bold yellow]"
        )
        api_key = prompt("API Key: ").strip()

    console.print("[bold cyan]🔑 Validating API key...[/bold cyan]")
    try:
        temp_client = OpenAI(api_key=api_key)
        temp_client.models.list()
    except OpenAIError as e:
        console.print(f"[bold red]❌ Invalid API key:[/bold red] {e}")
        return

    os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        found = False
        for line in lines:
            if "OPENAI_API_KEY=" in line:
                f.write(f"OPENAI_API_KEY={api_key}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"OPENAI_API_KEY={api_key}\n")

    console.print("[bold green]✅ API key saved and validated.[/bold green]")


def command_ping(api_key):
    """Test OpenAI API connectivity with the provided API key."""
    console.print("[bold cyan]🔌 Pinging OpenAI API...[/bold cyan]")
    try:
        temp_client = OpenAI(api_key=api_key)
        temp_client.models.list()
        console.print("[bold green]✅ OpenAI API is reachable.[/bold green]")
    except OpenAIError as e:
        console.print(f"[bold red]❌ Failed to reach OpenAI API:[/bold red] {e}")


def command_log(log_file):
    """Display the full conversation log from the specified file."""
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            console.print(f.read())
    else:
        console.print("[yellow]⚠️ No log file found.[/yellow]")


def command_clear_log(log_file):
    """Delete the conversation log file if it exists."""
    if os.path.exists(log_file):
        os.remove(log_file)
        console.print("[bold green]🧹 Log file has been deleted.[/bold green]")
    else:
        console.print("[yellow]⚠️ No log file to delete.[/yellow]")


def command_summary(rolling_summary: str, markdown: bool):
    """Display the current rolling conversation summary."""
    if rolling_summary:
        console.print("[bold cyan]📋 Current Summary:[/bold cyan]\n")
        if markdown:
            console.print(Markdown(rolling_summary))
        else:
            console.print(rolling_summary)
    else:
        console.print("[yellow]⚠️ No summary available yet.[/yellow]")
