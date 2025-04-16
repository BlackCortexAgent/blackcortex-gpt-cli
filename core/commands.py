import os
import subprocess
from openai import OpenAI, OpenAIError
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import prompt

console = Console()

# === Edit the .env configuration file ===
def command_env():
    env_path = os.path.expanduser("~/.gpt-cli/.env")
    os.makedirs(os.path.dirname(env_path), exist_ok=True)
    editor = os.getenv('EDITOR', 'nano')  # Default to nano if EDITOR is not set
    try:
        subprocess.run([editor, env_path], check=True)
    except Exception as e:
        console.print(f"[bold red]❌ Failed to open editor:[/bold red] {e}")

# === Run the CLI update script ===
def command_update():
    install_path = os.path.expanduser("~/.gpt-cli/install.sh")
    if os.path.isfile(install_path):
        try:
            subprocess.run(["bash", install_path], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]❌ Update script failed:[/bold red] {e}")
    else:
        console.print("[bold red]❌ install.sh not found in ~/.gpt-cli[/bold red]")

# === Run the CLI uninstall script ===
def command_uninstall():
    uninstall_path = os.path.expanduser("~/.gpt-cli/uninstall.sh")
    if os.path.isfile(uninstall_path):
        try:
            subprocess.run(["bash", uninstall_path], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]❌ Uninstall script failed:[/bold red] {e}")
    else:
        console.print("[bold red]❌ uninstall.sh not found in ~/.gpt-cli[/bold red]")

# === Set and validate the OpenAI API key ===
def command_set_key(api_key):
    if api_key is None:
        console.print("[bold yellow]🔐 No API key provided. Please enter your OpenAI API key:[/bold yellow]")
        api_key = prompt("API Key: ").strip()

    console.print("[bold cyan]🔑 Validating API key...[/bold cyan]")
    try:
        # Try to list models to ensure the key is valid
        temp_client = OpenAI(api_key=api_key)
        temp_client.models.list()
    except OpenAIError as e:
        console.print(f"[bold red]❌ Invalid API key:[/bold red] {e}")
        return

    # Save key to the .env file
    env_path = os.path.expanduser("~/.gpt-cli/.env")
    os.makedirs(os.path.dirname(env_path), exist_ok=True)
    lines = []

    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    # Write or update OPENAI_API_KEY
    with open(env_path, "w") as f:
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

# === Ping the OpenAI API to test connectivity ===
def command_ping(api_key):
    console.print("[bold cyan]🔌 Pinging OpenAI API...[/bold cyan]")
    try:
        temp_client = OpenAI(api_key=api_key)
        temp_client.models.list()
        console.print("[bold green]✅ OpenAI API is reachable.[/bold green]")
    except OpenAIError as e:
        console.print(f"[bold red]❌ Failed to reach OpenAI API:[/bold red] {e}")

# === Print the full conversation log ===
def command_log(log_file):
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            console.print(f.read())
    else:
        console.print("[yellow]⚠️ No log file found.[/yellow]")

# === Delete the conversation log ===
def command_clear_log(log_file):
    if os.path.exists(log_file):
        os.remove(log_file)
        console.print("[bold green]🧹 Log file has been deleted.[/bold green]")
    else:
        console.print("[yellow]⚠️ No log file to delete.[/yellow]")

# === Display the current rolling summary of the conversation ===
def command_summary(rolling_summary: str, markdown: bool):
    if rolling_summary:
        console.print("[bold cyan]📋 Current Summary:[/bold cyan]\n")
        if markdown:
            console.print(Markdown(rolling_summary))
        else:
            console.print(rolling_summary)
    else:
        console.print("[yellow]⚠️ No summary available yet.[/yellow]")
