# blackcortex_cli/flags/flag_markdown.py

"""
Flag definition for controlling Markdown formatting in the BlackCortex GPT CLI.
"""

import argparse

from blackcortex_cli.core.context import Context
from blackcortex_cli.core.flag_registry import Flag, flag_registry


def set_markdown(args: argparse.Namespace, context: Context) -> None:
    """
    Set Markdown formatting preference based on user input.

    Updates the context configuration to enable or disable Markdown output
    depending on whether the '--markdown' argument is 'true' or 'false'.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        context (Context): The application context containing configuration.
    """
    context.config.markdown_enabled = args.markdown.lower() == "true"


# Register the --markdown flag
flag_registry.register(
    Flag(
        name="markdown",
        short="md",
        long="markdown",
        help="Control Markdown formatting in responses ('true' to enable, 'false' to disable)",
        action="store",
        value_type=str,
        choices=["true", "false"],
        dest="markdown",
        category="Output",
        pre_handler=set_markdown,
    )
)
