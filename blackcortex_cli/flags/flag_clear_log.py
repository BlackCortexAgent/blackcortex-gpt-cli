# blackcortex_cli/flags/flag_clear_log.py

"""
Flag handler for clearing the GPT CLI conversation log.
"""

import argparse

from blackcortex_cli.core.context import Context
from blackcortex_cli.core.flag_registry import Flag, flag_registry


def clear_log(_: argparse.Namespace, context: Context):
    """
    Clear the conversation log using the LogManager from the CLI context.
    """
    context.log_manager.clear()


flag_registry.register(
    Flag(
        name="clear-log",
        short="cl",
        long="clear-log",
        help="Clear the conversation log",
        action="store_true",
        category="Session",
        pre_handler=clear_log,
        exit_after=True,
    )
)
