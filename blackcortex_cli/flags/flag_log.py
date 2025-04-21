# blackcortex_cli/flags/flag_log.py

"""
Flag definition for displaying the conversation log in the BlackCortex GPT CLI.
"""

import argparse

from blackcortex_cli.core.context import Context
from blackcortex_cli.core.flag_registry import Flag, flag_registry


def show_log(_: argparse.Namespace, context: Context):
    """Display the conversation log using the LogManager."""
    context.log_manager.show()


flag_registry.register(
    Flag(
        name="log",
        short="l",
        long="log",
        help="Display conversation log",
        action="store_true",
        category="Session",
        pre_handler=show_log,
        exit_after=True,
    )
)
