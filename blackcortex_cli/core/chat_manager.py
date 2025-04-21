# blackcortex_cli/core/chat_manager.py

"""
Chat manager for GPT CLI.

Handles communication with the OpenAI API, including memory integration,
token estimation, and both streaming and blocking response modes.
"""

from datetime import datetime

import tiktoken
from openai import OpenAI, OpenAIError
from rich.live import Live
from rich.markdown import Markdown

from blackcortex_cli.config.config import Config
from blackcortex_cli.core.context_memory import ContextMemory
from blackcortex_cli.utils.console import console
from blackcortex_cli.utils.formatting import print_wrapped


class ChatManager:
    """Coordinates prompt handling, memory, and output streaming for GPT interactions."""

    def __init__(self, config: Config):
        """
        Initialize the ChatManager with configuration and context memory.
        """
        self.config = config
        self.client = OpenAI(api_key=config.api_key)
        self.stream_enabled = config.stream_enabled
        self.memory = ContextMemory(config.memory_path)
        self.memory.load()

        self.memory_intro = (
            f"This is a CLI environment with simulated memory.\n"
            f"You do not have full access to previous conversations, but you may receive a\n"
            f"rolling summary and the {config.memory_limit} most recent user-assistant message.\n"
            f"pairs. Once {config.memory_limit * 2} messages are reached, a summary is generated\n"
            f"to retain context while conserving memory."
        )

    def _estimate_tokens(self, messages: list[dict], response: str) -> int:
        """
        Estimate the total token count for input messages and response using tiktoken.

        Args:
            messages: List of message dictionaries with role and content.
            response: The assistant's response text.

        Returns:
            Estimated total token count.
        """
        try:
            encoding = tiktoken.encoding_for_model(self.config.model)
            token_count = 0

            for message in messages:
                content = message.get("content", "")
                token_count += len(encoding.encode(content)) + 4  # Message overhead

            if response:
                token_count += len(encoding.encode(response))

            return token_count
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to estimate tokens: {e}[/yellow]")
            return 0

    def get_answer(
        self, prompt_text: str, return_usage: bool = False
    ) -> tuple[str, int | None, str]:
        """
        Get the assistant's response, token usage, and timestamp for a given prompt.

        Args:
            prompt_text: The user's input prompt.
            return_usage: Whether to return token usage (ignored for streaming).

        Returns:
            Tuple of (response, token_usage, timestamp).
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.stream_enabled:
            response, estimated_tokens = self._get_answer_streaming(prompt_text, timestamp)
            return response, estimated_tokens, timestamp
        return self._get_answer_blocking(prompt_text, timestamp, return_usage)

    def _get_answer_blocking(
        self, prompt_text: str, timestamp: str, return_usage: bool
    ) -> tuple[str, int | None, str]:
        """
        Generate a blocking (non-streaming) assistant response to a prompt.

        Appends the prompt and response to memory and returns the reply.

        Returns:
            Tuple of (response, token_usage, timestamp).
        """
        self.memory.recent_messages.append({"role": "user", "content": prompt_text})
        messages = self._build_messages()
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        except OpenAIError as e:
            return f"[x] OpenAI API error: {e}", None, timestamp

        reply = response.choices[0].message.content.strip()
        self.memory.recent_messages.append({"role": "assistant", "content": reply})
        self.memory.check_memory_limit(client=self.client, config=self.config)
        self.memory.save()

        token_usage = (
            response.usage.total_tokens if return_usage and hasattr(response, "usage") else None
        )
        return reply, token_usage, timestamp

    def _get_answer_streaming(self, prompt_text: str, timestamp: str) -> str:
        """
        Stream the assistant's response token-by-token as it's generated.

        Returns:
            Tuple of (response text, estimated token count).
        """
        self.memory.recent_messages.append({"role": "user", "content": prompt_text})
        messages = self._build_messages()
        try:
            stream = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
            )
        except OpenAIError as e:
            return f"[x] OpenAI API error: {e}"

        full_reply = ""
        if self.config.markdown_enabled:
            with Live("", console=console, auto_refresh=False) as live:
                for chunk in stream:
                    content = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
                    if content:
                        full_reply += content
                        live.update(Markdown(full_reply))
                        live.refresh()
        else:
            for chunk in stream:
                content = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
                if content:
                    full_reply += content
                    print_wrapped(content, end="", markdown=False)
            console.print()

        self.memory.recent_messages.append({"role": "assistant", "content": full_reply})
        self.memory.check_memory_limit(client=self.client, config=self.config)
        self.memory.save()

        estimated_tokens = self._estimate_tokens(messages, full_reply)
        return full_reply, estimated_tokens

    def _build_messages(self) -> list[dict]:
        """
        Construct the full message history with intro, instructions, summary, and recent context.

        Returns:
            List of message dictionaries in the expected chat format.
        """
        messages = [{"role": "system", "content": f"INTRO: {self.memory_intro}"}]
        if self.config.default_prompt:
            messages.append(
                {"role": "system", "content": f"INSTRUCTIONS: {self.config.default_prompt}"}
            )
        if self.memory.rolling_summary:
            messages.append(
                {"role": "system", "content": f"SUMMARY: {self.memory.rolling_summary}"}
            )
        messages.extend(self.memory.recent_messages[-self.config.memory_limit :])
        return messages
