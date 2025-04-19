"""
REPL interface for BLACKCORTEX GPT CLI.

This module defines a `ReplRunner` class that launches an interactive
Read-Eval-Print Loop (REPL) for interacting with OpenAI models via the GPT CLI.
It supports Markdown rendering, streaming and non-streaming responses,
conversation logging, and formatted output display using `rich`.
"""

import os
from datetime import datetime

from openai import OpenAIError
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console

from blackcortex_cli.core.chat import ChatManager
from blackcortex_cli.logging.manager import LogManager
from blackcortex_cli.utils.formatting import print_wrapped, render_header

console = Console()


class ReplRunner:
    """
    Interactive REPL interface for the GPT CLI.

    Captures user input, passes to the chat manager,
    renders output, and logs the conversation.
    """

    def __init__(self, chat: ChatManager, log: LogManager, markdown: bool = True):
        self.chat = chat
        self.log = log
        self.markdown = markdown

        self.session = PromptSession(
            history=FileHistory(os.path.expanduser("~/.gpt_history")),
            auto_suggest=AutoSuggestFromHistory(),
        )

    def run(self):
        console.print("[bold green]🧠 GPT CLI is ready. Type 'exit' to quit.[/bold green]\n")

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
                    console.print("\n[bold yellow]Goodbye![/bold yellow]")
                    break

                console.print()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if self.chat.stream_enabled:
                    meta = f"{self.chat.config.model}  •  {timestamp}"
                    console.print(render_header("Assistant", meta, style_left="bold green"))
                    response = self.chat.get_answer(user_input)
                    self.log.write(user_input, response)
                else:
                    response, usage = self.chat.get_answer(user_input, return_usage=True)
                    meta = (
                        f"{self.chat.config.model} ({usage} tokens)  •  {timestamp}"
                        if usage
                        else f"{self.chat.config.model}  •  {timestamp}"
                    )
                    console.print(render_header("Assistant", meta, style_left="bold green"))
                    print_wrapped(response, markdown=self.markdown)
                    self.log.write(user_input, response)

                console.print()
                console.rule(style="grey50")
                console.print()

            except KeyboardInterrupt:
                console.print("\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
            except (OpenAIError, RuntimeError) as e:
                console.print(f"\n[bold red]Error:[/bold red] {e}\n")
