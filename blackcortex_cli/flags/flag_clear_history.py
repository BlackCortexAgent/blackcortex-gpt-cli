# blackcortex_cli/flags/flag_clear_history.py

"""
Defines the --clear-history flag for the GPT CLI to delete the REPL command history file.
"""

import argparse
import os

from blackcortex_cli.core.context import Context
from blackcortex_cli.core.flag_registry import Flag, flag_registry
from blackcortex_cli.utils.console import console


def clear_history(_: argparse.Namespace, context: Context):
    """
    Delete the REPL history file specified in the configuration.

    Args:
        _: Parsed argparse namespace (unused).
        context: The CLI context containing config with the history file path.
    """
    history_path = os.path.expanduser(context.config.history_path)
    if os.path.exists(history_path):
        try:
            os.remove(history_path)
            console.print("[bold green][+] History file has been cleared.[/bold green]")
        except PermissionError:
            console.print("[bold red][x] Permission denied when clearing history file.[/bold red]")
        except Exception as e:
            console.print(f"[bold red][x] Failed to clear history file: {e}[/bold red]")
    else:
        console.print("[yellow][-] No history file to clear.[/yellow]")


flag_registry.register(
    Flag(
        name="clear-history",
        short="ch",
        long="clear-history",
        help="Clear prompt history",
        action="store_true",
        category="Session",
        post_handler=clear_history,
        exit_after=True,
    )
)
