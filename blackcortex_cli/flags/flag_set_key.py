# blackcortex_cli/flags/flag_set_key.py

"""
Flag definition for setting the OpenAI API key in the BlackCortex GPT CLI.

Prompts the user or accepts a value via CLI, validates the key using OpenAI API,
and securely saves it to the .env file.
"""

import argparse
import os

from openai import OpenAI, OpenAIError
from prompt_toolkit import prompt

from blackcortex_cli.config.paths import get_env_path
from blackcortex_cli.core.flag_registry import Flag, flag_registry
from blackcortex_cli.utils.console import console


def handle_set_key(args: argparse.Namespace, context=None):
    Set and validate the OpenAI API key, saving it to the .env file with secure permissions.

    If the key is not provided via CLI, prompts the user interactively.
    Validates the key by attempting to list models via the OpenAI API.
    """
    api_key = None if args.set_key == "__PROMPT__" else args.set_key

    if api_key is None:
        console.print(
            "[bold yellow][-] No API key provided. Please enter your OpenAI API key:[/bold yellow]"
        )
        try:
            api_key = prompt("API Key: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("[bold red][x] API key prompt cancelled.[/bold red]")
            return

    console.print("[bold cyan]Validating API key...[/bold cyan]")
    try:
        temp_client = OpenAI(api_key=api_key)
        temp_client.models.list()
    except OpenAIError:
        console.print("[bold red][x] Invalid API key[/bold red]")
        return

    try:
        ENV_PATH = get_env_path()
        os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
        lines = []
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

        with open(ENV_PATH, "w", encoding="utf-8") as f:
            found = False
            for line in lines:
                if "OPENAI_API_KEY=" in line:
                    f.write(f"OPENAI_API_KEY={api_key}\n")
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f"OPENAI_API_KEY={api_key}\n")

        os.chmod(ENV_PATH, 0o660)
    except OSError as e:
        console.print(f"[bold red][x] Failed to write .env file:[/bold red] {e}")
        return

    console.print("[bold green][+] API key saved and validated.[/bold green]")


# Register the --set-key flag
flag_registry.register(
    Flag(
        name="set-key",
        short="k",
        long="set-key",
        help="Set or update OpenAI API key (prompt if value omitted)",
        action="store",
        nargs="?",
        const="__PROMPT__",
        metavar="API_KEY",
        dest="set_key",
        category="Configuration",
        pre_handler=handle_set_key,
        exit_after=True,
    )
)
