"""
Contextual memory management for GPT-CLI (short-term memory).

This module defines `ContextMemory`, a class for managing session-local memory.
It tracks recent conversation turns and maintains a rolling summary, optimizing
prompt construction while staying within token limits.
"""

import json
import os

from openai import OpenAI, OpenAIError
from rich.console import Console

console = Console()


class ContextMemory:
    """
    Manages short-term conversational memory for a CLI session.
    Stores and summarizes recent messages using OpenAI and local disk.
    """

    def __init__(self, path: str):
        self.path = path
        self.rolling_summary: str = ""
        self.recent_messages: list[dict] = []

    def load(self) -> tuple[str, list[dict]]:
        """
        Load memory from disk. Initializes rolling summary and message list.
        """
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.rolling_summary = data.get("summary", "")
                    self.recent_messages = data.get("recent", [])
            except json.JSONDecodeError:
                console.print("[bold red]⚠️ Corrupted memory file. Resetting...[/bold red]")
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
        os.chmod(self.path, 0o600)

    def reset(self) -> tuple[str, list[dict]]:
        """
        Delete memory file and clear memory in-memory.
        """
        if os.path.exists(self.path):
            try:
                os.remove(self.path)
                console.print("[bold yellow]🧹 Memory file has been reset.[/bold yellow]\n")
            except PermissionError:
                console.print(
                    "[bold red]⚠️ Permission denied when resetting memory file.[/bold red]"
                )
                return self.rolling_summary, self.recent_messages
        else:
            console.print("[blue]ℹ️ No memory file to reset.[/blue]\n")

        self.rolling_summary, self.recent_messages = "", []
        return self.rolling_summary, self.recent_messages

    def summarize(
        self,
        client: OpenAI,
        model: str,
        memory_limit: int,
        max_summary_tokens: int,
    ) -> tuple[str, list[dict]]:
        """
        Summarize recent messages into a rolling summary using OpenAI.

        Resets the recent_messages buffer after successful summarization.
        """
        if not self.recent_messages:
            self.save()
            return self.rolling_summary, []

        batch = self.recent_messages[-(memory_limit * 2) :]
        summary_prompt = (
            f"Here is the current summary of our conversation:\n{self.rolling_summary}\n\n"
            f"Please update it with the following messages:\n"
            + "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in batch])
        )

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a summarizer that maintains a concise summary",
                    },
                    {"role": "user", "content": summary_prompt},
                ],
                temperature=0,
                max_tokens=max_summary_tokens,
            )
            self.rolling_summary = response.choices[0].message.content.strip()
            self.recent_messages = []
            self.save()
        except (OpenAIError, Exception) as e:
            console.print(f"[bold red]Summary failed:[/bold red] {e}")

        return self.rolling_summary, self.recent_messages
