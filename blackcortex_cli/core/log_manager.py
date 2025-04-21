# blackcortex_cli/core/log_manager.py

"""
LogManager for GPT CLI.

Handles persistent storage of prompt-response pairs, token usage, and other logs with timestamped
entries using Python's logging module with RotatingFileHandler for file output and optional
RichHandler for console output. Provides utilities to view and clear the log file.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from rich.logging import RichHandler

from blackcortex_cli.utils.console import console


class LogManager:
    """
    Manages interaction logs for the GPT CLI tool using logging handlers.
    """

    def __init__(
        self,
        path: str,
        log_level: str = "INFO",
        log_to_console: bool = False,
        permissions: int = 0o600,
        group: str | None = None,
    ):
        """
        Initialize the LogManager.

        Args:
            path: Path to the log file.
            log_level: Logging level (default: "INFO").
            log_to_console: Whether to also log to the console.
            permissions: File permissions for the log file.
            group: Optional group name for group ownership.
        """
        self.path = os.path.expanduser(path)
        self.permissions = permissions
        self.group = group
        self.logger = logging.getLogger("gpt_cli")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self._file_handler_initialized = False

        self.logger.handlers.clear()

        if log_to_console:
            console_handler = RichHandler(
                show_time=True, show_level=True, show_path=False, console=console
            )
            console_handler.setFormatter(logging.Formatter("%(message)s"))
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)

    def _init_file_handler(self):
        """
        Initialize the file-based log handler with rotation and formatting.
        """
        if self._file_handler_initialized:
            return

        file_handler = RotatingFileHandler(
            self.path, maxBytes=1024 * 1024 * 10, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(file_handler)
        self._file_handler_initialized = True

        self._set_permissions()

    def _set_permissions(self):
        """
        Set file permissions and group ownership for the log file.
        """
        if os.path.exists(self.path):
            try:
                os.chmod(self.path, 0o660)
            except PermissionError:
                console.print(
                    f"[bold red][x] Permission denied when setting {self.path} to {oct(self.permissions)}[/bold red]"
                )
            except (KeyError, Exception) as e:
                console.print(
                    f"[bold red][x] Failed to set permissions or group for {self.path}: {e}[/bold red]"
                )

    def write(self, prompt_text: str, response: str, token_usage: int | None = None):
        """
        Log a prompt-response pair with optional token usage.

        Args:
            prompt_text: The user's input prompt.
            response: The assistant's response.
            token_usage: Number of tokens used (optional).
        """
        self._init_file_handler()
        self.logger.info(f"Prompt: {prompt_text}")
        self.logger.info(f"Response: {response}")
        if token_usage is not None:
            self.logger.info(f"[Token Usage: {token_usage}]")
        self.logger.info("-" * 80)
        self._set_permissions()

    def log_info(self, message: str):
        """Log an informational message."""
        self._init_file_handler()
        self.logger.info(message)

    def log_error(self, message: str):
        """Log an error message."""
        self._init_file_handler()
        self.logger.error(message)

    def log_debug(self, message: str):
        """Log a debug message."""
        self._init_file_handler()
        self.logger.debug(message)

    def show(self) -> None:
        """
        Display the contents of the log file, if it exists.
        """
        if not os.path.exists(self.path):
            console.print("[yellow][-] No log file found.[/yellow]")
        else:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    console.print(content)
                else:
                    console.print("[yellow][-] Log file is empty.[/yellow]")

    def clear(self):
        """Delete the log file if it exists."""
        if os.path.exists(self.path):
            os.remove(self.path)
            console.print("[bold green][+] Log file has been deleted.[/bold green]")
        else:
            console.print("[yellow][-] No log file to delete.[/yellow]")
