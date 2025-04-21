# blackcortex_cli/flags/flag_update.py

"""
Flag handler for updating the BlackCortex GPT CLI using pip or pipx.
"""

import argparse
import shutil
import subprocess
import sys

from blackcortex_cli.core.flag_registry import Flag, flag_registry
from blackcortex_cli.utils.console import console
from blackcortex_cli.utils.metadata import read_name


def handle_update(_: argparse.Namespace, context):
    """
    Update the CLI tool via pip or pipx.

    Attempts to upgrade the installed package using pipx if available,
    otherwise falls back to pip. Displays the update status.
    """
    package_name = read_name()

    console.print(f"[bold cyan]Updating {package_name}...[/bold cyan]")
    try:
        if shutil.which("pipx"):
            subprocess.run(["pipx", "upgrade", package_name], check=True)
        else:
            subprocess.run(["pip", "install", "--upgrade", package_name], check=True)
        console.print(f"[bold green][+] {package_name} updated successfully.[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red][x] Update failed:[/bold red] {e}")
        console.print(
            f"You can manually upgrade with:\n"
            f"   pip install --upgrade {package_name}  or\n"
            f"   pipx upgrade {package_name}"
        )
    sys.exit(0)


# Register the --update flag
flag_registry.register(
    Flag(
        name="update",
        short="u",
        long="update",
        help="Update the CLI tool",
        action="store_true",
        category="System",
        pre_handler=handle_update,
        exit_after=True,
    )
)
