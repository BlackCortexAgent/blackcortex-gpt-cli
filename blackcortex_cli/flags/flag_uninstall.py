# blackcortex_cli/flags/flag_uninstall.py

"""
Flag definition for uninstalling the BlackCortex GPT CLI.
"""

import argparse
import shutil
import subprocess
import sys

from blackcortex_cli.core.flag_registry import Flag, flag_registry
from blackcortex_cli.utils.console import console
from blackcortex_cli.utils.metadata import read_name


def handle_uninstall(_: argparse.Namespace):
    """
    Handler for the --uninstall flag to remove the CLI tool.

    Attempts to uninstall the CLI using pipx if available, otherwise falls back to pip.
    Displays appropriate messages based on success or failure and exits after execution.
    """
    package_name = read_name()

    console.print(f"[bold cyan]🗑️ Uninstalling {package_name}...[/bold cyan]")
    try:
        if shutil.which("pipx"):
            subprocess.run(["pipx", "uninstall", package_name], check=True)
        else:
            subprocess.run(["pip", "uninstall", "-y", package_name], check=True)
        console.print(f"[bold green][+] {package_name} uninstalled successfully.[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red][x] Uninstall failed:[/bold red] {e}")
        console.print(
            f"You can manually uninstall with "
            f"'pip uninstall {package_name}' or "
            f"'pipx uninstall {package_name}'"
        )
    sys.exit(0)


# Register the --uninstall flag
flag_registry.register(
    Flag(
        name="uninstall",
        short="x",
        long="uninstall",
        help="Uninstall the CLI tool",
        action="store_true",
        category="System",
        pre_handler=handle_uninstall,
        exit_after=True,
    )
)
