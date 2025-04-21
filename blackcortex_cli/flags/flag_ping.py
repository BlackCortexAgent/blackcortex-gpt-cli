# blackcortex_cli/flags/flag_ping.py

"""
Flag definition for testing OpenAI API connectivity in the BlackCortex GPT CLI.
"""

import argparse

from openai import OpenAI, OpenAIError

from blackcortex_cli.core.context import Context
from blackcortex_cli.core.flag_registry import Flag, flag_registry
from blackcortex_cli.utils.console import console


def handle_ping(_: argparse.Namespace, context: Context):
    """
    Test OpenAI API connectivity with the provided API key.

    Sends a request to list available models to verify if the API is reachable.
    Displays a success or error message in the terminal.
    """
    console.print("[bold cyan]Pinging OpenAI API...[/bold cyan]")
    try:
        temp_client = OpenAI(api_key=context.config.api_key)
        temp_client.models.list()
        console.print("[bold green][+] OpenAI API is reachable.[/bold green]")
    except OpenAIError as e:
        console.print(f"[bold red][x] Failed to reach OpenAI API:[/bold red] {e}")


# Register the --ping flag
flag_registry.register(
    Flag(
        name="ping",
        short="p",
        long="ping",
        help="Test OpenAI API connectivity",
        action="store_true",
        category="System",
        pre_handler=handle_ping,
        exit_after=True,
    )
)
