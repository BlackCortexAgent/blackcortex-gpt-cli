# blackcortex_cli/flags/flag_env.py

"""
Flag definition for opening the .env configuration file in the BlackCortex GPT CLI.

This module defines the --env flag, which opens the .env file in the user's editor for configuration,
creating it if necessary and checking for any modifications made during the session.
"""

import argparse
import os
import subprocess
import sys

from blackcortex_cli.config.paths import get_env_path
from blackcortex_cli.core.context import Context
from blackcortex_cli.core.flag_registry import Flag, flag_registry
from blackcortex_cli.utils.console import console


def set_file_permissions(path: str, log_manager, permissions: int = 0o660) -> None:
    """
    Set permissions on a file and log the outcome.

    Args:
        path: Path to the file.
        log_manager: LogManager instance for logging.
        permissions: Desired permissions (default: 0o660).
    """
    try:
        os.chmod(path, permissions)
        log_manager.log_info(f"Set permissions on {path} to {oct(permissions)}")
    except OSError as e:
        log_manager.log_error(f"Failed to set permissions on {path}: {e}")
        console.print(f"[yellow][-] Warning: Could not set permissions on {path}: {e}[/yellow]")


def check_file_modified(path: str, before: float, log_manager) -> bool:
    """
    Check if a file was modified and log the result.

    Args:
        path: Path to the file.
        before: Modification time before editing.
        log_manager: LogManager instance for logging.

    Returns:
        bool: True if the file was modified, False otherwise.
    """
    try:
        after = os.stat(path).st_mtime
        modified = after != before
        log_manager.log_info(f"{path} {'was' if modified else 'was not'} modified")
        return modified
    except OSError as e:
        log_manager.log_error(f"Failed to check modification time of {path}: {e}")
        return False


def handle_env(args: argparse.Namespace, context: Context) -> None:
    """
    Open the .env configuration file in the user's default editor.

    Ensures the file and its directory exist, launches the editor, logs actions,
    and reports whether the file was modified.

    Args:
        args: Parsed command-line arguments (unused).
        context: Application context with configuration and log manager.

    Exits:
        Status 0 on success, 1 on error.
    """
    env_path = get_env_path()
    log_manager = context.log_manager

    # Ensure the .env file and its directory exist
    try:
        os.makedirs(os.path.dirname(env_path), mode=0o770, exist_ok=True)
        if not os.path.exists(env_path):
            with open(env_path, "a", encoding="utf-8") as f:
                f.write("# BlackCortex GPT CLI configuration\n")
            log_manager.log_info(f"Created new .env file at {env_path}")
        set_file_permissions(env_path, log_manager)
    except OSError as e:
        log_manager.log_error(f"Failed to prepare .env file at {env_path}: {e}")
        console.print(f"[bold red][x] Failed to prepare .env file:[/bold red] {e}")
        sys.exit(1)

    # Open the editor
    try:
        before = os.stat(env_path).st_mtime
        editor = os.getenv("EDITOR", "nano")
        log_manager.log_info(f"Opening {env_path} with editor '{editor}'")
        subprocess.run([editor, env_path], check=True)
        set_file_permissions(env_path, log_manager)
        if check_file_modified(env_path, before, log_manager):
            console.print("[bold green][+] .env file updated.[/bold green]")
        else:
            console.print("[bold yellow][-] No changes made to .env file.[/bold yellow]")
    except subprocess.CalledProcessError as e:
        log_manager.log_error(f"Editor failed for {env_path}: exited with code {e.returncode}")
        console.print(f"[bold red][x] Editor failed:[/bold red] Exited with code {e.returncode}")
        sys.exit(1)
    except OSError as e:
        log_manager.log_error(f"Failed to open editor for {env_path}: {e}")
        console.print(f"[bold red][x] Failed to open editor:[/bold red] {e}")
        console.print(
            "[yellow]Try setting the EDITOR environment variable or installing 'nano'.[/yellow]"
        )
        sys.exit(1)

    sys.exit(0)


# Register the --env flag
flag_registry.register(
    Flag(
        name="env",
        short="e",
        long="env",
        help="Open configuration file",
        action="store_true",
        category="Configuration",
        pre_handler=handle_env,
        exit_after=True,
    )
)
