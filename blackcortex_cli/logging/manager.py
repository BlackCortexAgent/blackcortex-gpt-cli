"""
LogManager for GPT CLI.

Handles persistent storage of prompt-response pairs with timestamped entries.
Also provides utilities to view and clear the log file.
"""

import os
from datetime import datetime

from rich.console import Console

console = Console()


class LogManager:
    """
    Manages interaction logs for the GPT CLI tool.
    """

    def __init__(self, path: str):
        self.path = os.path.expanduser(path)

    def write(self, prompt_text: str, response: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Prompt:\n{prompt_text}\n\nResponse:\n{response}\n{'-' * 80}\n")
        os.chmod(self.path, 0o600)

    def show(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                console.print(f.read())
        else:
            console.print("[yellow]⚠️ No log file found.[/yellow]")

    def clear(self):
        if os.path.exists(self.path):
            os.remove(self.path)
            console.print("[bold green]🧹 Log file has been deleted.[/bold green]")
        else:
            console.print("[yellow]⚠️ No log file to delete.[/yellow]")
