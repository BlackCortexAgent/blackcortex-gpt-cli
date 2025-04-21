# blackcortex_cli/flags/flag_clear_memory.py

"""
Flag handler to clear context memory in the BlackCortex GPT CLI.

This module registers the --clear-memory flag, allowing users to reset the short-term memory
used by the chat manager, which includes recent messages and summaries.
"""

import argparse

from blackcortex_cli.core.context import Context
from blackcortex_cli.core.flag_registry import Flag, flag_registry


def clear_memory(_: argparse.Namespace, context: Context):
    """
    Clear the current context memory managed by the chat system.
    """
    context.chat_manager.memory.clear()


flag_registry.register(
    Flag(
        name="clear-memory",
        short="cm",
        long="clear-memory",
        help="Clear context memory",
        action="store_true",
        category="Session",
        post_handler=clear_memory,
        exit_after=True,
    )
)
