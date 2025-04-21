# blackcortex_cli/core/context_memory.py

"""
Contextual memory management for GPT-CLI (short-term memory).

Handles loading, saving, clearing, and summarizing recent user-assistant message pairs,
with optional summarization to preserve context within memory limits.
"""

import json
import os

from openai import OpenAI, OpenAIError

from blackcortex_cli.utils.console import console


class ContextMemory:
    def __init__(self, path: str):
        """Initialize the memory with the given file path."""
        self.path = path
        self.rolling_summary: str = ""
        self.recent_messages: list[dict] = []

    def load(self) -> tuple[str, list[dict]]:
        """
        Load memory from the file if it exists.

        Returns:
            A tuple containing the rolling summary and list of recent messages.
        """
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.rolling_summary = data.get("summary", "")
                    self.recent_messages = data.get("recent", [])
            except json.JSONDecodeError:
                console.print("[bold red][-] Corrupted memory file. Resetting...[/bold red]")
                self.rolling_summary, self.recent_messages = "", []
        return self.rolling_summary, self.recent_messages

    def save(self):
        """
        Persist the current memory state to disk.
        """
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                {"summary": self.rolling_summary, "recent": self.recent_messages}, f, indent=2
            )
        os.chmod(self.path, 0o660)

    def clear(self) -> tuple[str, list[dict]]:
        """
        Clear the memory file and in-memory contents.

        Returns:
            A tuple with empty summary and message list.
        """
        if os.path.exists(self.path):
            try:
                os.remove(self.path)
                console.print("[bold green][+] Memory file has been reset.[/bold green]")
            except PermissionError:
                console.print(
                    "[bold red][x] Permission denied when resetting memory file.[/bold red]"
                )
                return self.rolling_summary, self.recent_messages
        else:
            console.print("[yellow][-] No memory file to reset.[/yellow]")

        self.rolling_summary, self.recent_messages = "", []
        return self.rolling_summary, self.recent_messages

    def summarize(
        self,
        client: OpenAI,
        config,
    ) -> tuple[str, list[dict]]:
        """
        Summarize the recent messages and update the rolling summary.

        Args:
            client: OpenAI client used to generate the summary.
            config: Configuration object containing model, limits, and token settings.

        Returns:
            A tuple of updated summary and an empty message list.
        """
        if not self.recent_messages:
            self.save()
            return self.rolling_summary, []

        batch = self.recent_messages[-(config.memory_limit * 2) :]
        summary_prompt = (
            f"Here is the current summary of our conversation:\n{self.rolling_summary}\n\n"
            f"Please update it with the following messages:\n"
            + "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in batch])
        )

        try:
            response = client.chat.completions.create(
                model=config.summary_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a summarizer that maintains a concise summary",
                    },
                    {"role": "user", "content": summary_prompt},
                ],
                temperature=0,
                max_tokens=config.max_summary_tokens,
            )
            self.rolling_summary = response.choices[0].message.content.strip()
            self.recent_messages = []
            self.save()
        except (OpenAIError, Exception) as e:
            console.print(f"[bold red][x] Summary failed:[/bold red] {e}")

        return self.rolling_summary, self.recent_messages

    def check_memory_limit(self, client: OpenAI, config):
        """
        Trigger summarization if recent message count exceeds the configured memory limit.
        """
        if len(self.recent_messages) >= config.memory_limit * 2:
            self.summarize(client=client, config=config)
