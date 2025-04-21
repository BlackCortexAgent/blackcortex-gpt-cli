# blackcortex_cli/flags/flag_version.py

"""
Defines the --version flag for displaying the current version of the BlackCortex GPT CLI.
"""

import argparse

from blackcortex_cli.core.flag_registry import Flag, flag_registry
from blackcortex_cli.utils.console import console
from blackcortex_cli.utils.metadata import read_version


def show_version(_: argparse.Namespace, context) -> None:
    """Print the current version of the CLI tool."""
    try:
        console.print(read_version())
    except FileNotFoundError:
        console.print("")


# Register the --version flag
flag_registry.register(
    Flag(
        name="version",
        short="v",
        long="version",
        help="Show version and exit",
        action="store_true",
        category="General",
        pre_handler=show_version,
        priority=100,
        exit_after=True,
    )
)
