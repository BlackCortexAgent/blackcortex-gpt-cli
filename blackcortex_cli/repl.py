# blackcortex_cli/repl.py

"""
REPL interface for BLACKCORTEX GPT CLI.
Provides an interactive prompt for users to communicate with the assistant.
Handles input history, context-based responses, streaming, and logging.
"""

import os

from openai import OpenAIError
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.patch_stdout import patch_stdout

from blackcortex_cli.core.context import Context
from blackcortex_cli.utils.console import console
from blackcortex_cli.utils.formatting import print_wrapped


class FilteredFileHistory(FileHistory):
    """
    Custom history class that filters out 'exit' and 'quit' commands from being saved
    and ensures the history file has secure permissions.
    """

    def __init__(self, filename: str):
        """Initialize history file and set permissions to 0o660."""
        super().__init__(filename)
        self._set_permissions()

    def append_string(self, string: str) -> None:
        """
        Append a command to the history file unless it's 'exit' or 'quit'.
        Also reapply secure permissions.
        """
        if string.lower() not in {"exit", "quit"}:
            super().append_string(string)
            self._set_permissions()

    def _set_permissions(self) -> None:
        """
        Set file permissions to 0o660 if the file exists.
        Logs an error if permission cannot be changed.
        """
        if os.path.exists(self.filename):
            try:
                os.chmod(self.filename, 0o660)
            except PermissionError:
                console.print(
                    f"[bold red]Permission denied when setting {self.filename} to 0o660[/bold red]"
                )
            except Exception as e:
                console.print(
                    f"[bold red]Failed to set permissions for {self.filename}: {e}[/bold red]"
                )


class ReplRunner:
    """
    Main runner for the REPL interface.
    Manages user input, assistant responses, logging, and error handling.
    """

    def __init__(self, context: Context):
        """
        Initialize the REPL session with provided context.

        Args:
            context: Application context containing configuration and managers.
        """
        self.context = context
        self.session = PromptSession(
            history=FilteredFileHistory(os.path.expanduser(self.context.config.history_path)),
            auto_suggest=AutoSuggestFromHistory(),
        )

    def run(self):
        """
        Start the REPL loop, handling user input and displaying assistant responses.
        Supports markdown output, streaming, and token usage reporting.
        """
        console.print(
            "[bold green]BlackCortex GPT CLI is ready. Type 'exit' to quit.[/bold green]\n"
        )

        while True:
            try:
                with patch_stdout():
                    user_input = self.session.prompt(
                        HTML("<ansibrightblue><b>You:</b> </ansibrightblue>"),
                        color_depth=ColorDepth.TRUE_COLOR,
                    ).strip()

                if not user_input:
                    continue
                if user_input.lower() in {"exit", "quit"}:
                    console.print("[bold yellow]Goodbye![/bold yellow]")
                    break

                console.print()
                console.print("[bold green]Assistant[/bold green]")

                # Get response with loading animation in non-streaming mode
                if not self.context.config.stream_enabled:
                    with console.status("Processing...", spinner="dots"):
                        response, token_usage, timestamp = self.context.chat_manager.get_answer(
                            user_input, return_usage=True
                        )
                    print_wrapped(response, markdown=self.context.config.markdown_enabled)
                else:
                    response, token_usage, timestamp = self.context.chat_manager.get_answer(
                        user_input, return_usage=True
                    )

                self.context.log_manager.write(user_input, response, token_usage)

                token_info = str(token_usage) if token_usage is not None else "N/A"
                footer = f"{self.context.config.model}  •  {token_info} tokens  •  {timestamp}"
                console.print(f"[dim]{footer}[/dim]")

                console.print()
                console.rule(style="grey50")
                console.print()

            except KeyboardInterrupt:
                self.context.log_manager.log_info("User interrupted the session")
                console.print("\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
            except (OpenAIError, RuntimeError) as e:
                self.context.log_manager.log_error(f"Error occurred: {e}")
                console.print(f"\n[bold red]Error:[/bold red] {e}\n")
