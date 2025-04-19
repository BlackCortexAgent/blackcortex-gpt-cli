"""
This module provides CLI commands for managing GPT-CLI configuration,
OpenAI API key, logs, updates, and environment setup.
"""

import os
import pathlib
import shutil
import subprocess
import tomllib

from openai import OpenAI, OpenAIError
from prompt_toolkit import prompt
from rich.console import Console

console = Console()
ENV_PATH = os.path.expanduser("~/.gpt-cli/.env")


def read_project_metadata():
    pyproject_path = pathlib.Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    return {
        "name": project.get("name"),
        "version": project.get("version"),
        "description": project.get("description"),
        "authors": project.get("authors"),
    }


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
    meta = read_project_metadata()
    package_name = meta["name"]

    console.print(f"[bold cyan]🔄 Updating {package_name}...[/bold cyan]")
    try:
        if shutil.which("pipx"):
            subprocess.run(["pipx", "upgrade", package_name], check=True)
        else:
            subprocess.run(["pip", "install", "--upgrade", package_name], check=True)
        console.print(f"[bold green]✅ {package_name} updated successfully.[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Update failed:[/bold red] {e}")
        console.print(
            f"💡 You can manually upgrade with "
            f"'pip install --upgrade {package_name}' or "
            f"'pipx upgrade {package_name}'"
        )


def command_uninstall():
    """Uninstall the GPT CLI tool via pip or pipx."""
    meta = read_project_metadata()
    package_name = meta["name"]

    console.print(f"[bold cyan]🗑️ Uninstalling {package_name}...[/bold cyan]")
    try:
        if shutil.which("pipx"):
            subprocess.run(["pipx", "uninstall", package_name], check=True)
        else:
            subprocess.run(["pip", "uninstall", "-y", package_name], check=True)
        console.print(f"[bold green]✅ {package_name} uninstalled successfully.[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ Uninstall failed:[/bold red] {e}")
        console.print(
            f"💡 You can manually uninstall with "
            f"'pip uninstall {package_name}' or "
            f"'pipx uninstall {package_name}'"
        )


def command_version():
    """Display the current version."""
    meta = read_project_metadata()
    console.print(meta["version"])


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
