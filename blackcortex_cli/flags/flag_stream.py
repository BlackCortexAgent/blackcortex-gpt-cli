# blackcortex_cli/flags/flag_stream.py

"""
Flag definition for controlling streaming responses in the BlackCortex GPT CLI.
"""

import argparse

from blackcortex_cli.core.context import Context
from blackcortex_cli.core.flag_registry import Flag, flag_registry


def set_stream(args: argparse.Namespace, context: Context) -> None:
    """
    Handler for the --stream flag to enable or disable streaming output.

    Updates the context configuration based on the user-supplied 'true' or 'false' value.
    """
    context.config.stream_enabled = args.stream.lower() == "true"


# Register the --stream flag for controlling streaming output
flag_registry.register(
    Flag(
        name="stream",
        short="s",
        long="stream",
        help="Control streaming of assistant responses ('true' to enable, 'false' to disable)",
        action="store",
        value_type=str,
        choices=["true", "false"],
        dest="stream",
        category="Output",
        pre_handler=set_stream,
    )
)
