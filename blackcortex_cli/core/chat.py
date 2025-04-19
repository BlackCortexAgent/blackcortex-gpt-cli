"""
Chat manager for GPT CLI.

Handles OpenAI interactions, prompt construction, memory summarization,
and response streaming or blocking based on runtime config.
"""

from openai import OpenAI, OpenAIError
from rich.console import Console

from blackcortex_cli.config.loader import Config
from blackcortex_cli.memory.context_memory import ContextMemory

console = Console()


class ChatManager:
    """
    Central coordinator for GPT CLI chat logic.

    Manages the OpenAI client, memory, prompt construction, and response handling.
    """

    def __init__(self, config: Config, stream: bool = False):
        self.config = config
        self.client = OpenAI(api_key=config.api_key)
        self.stream_enabled = stream
        self.memory = ContextMemory(config.memory_path)
        self.memory.load()

        self.memory_intro = (
            f"This is a CLI environment with simulated memory.\n"
            f"You do not have full access to previous conversations, but you may receive a\n"
            f"rolling summary and the {config.memory_limit} most recent user-assistant message.\n"
            f"pairs. Once {config.memory_limit * 2} messages are reached, a summary is generated\n"
            f"to retain context while conserving memory."
        )

    def get_answer(
        self, prompt_text: str, return_usage: bool = False
    ) -> str | tuple[str, int | None]:
        if self.stream_enabled:
            response = self._get_answer_streaming(prompt_text)
            return (response, None) if return_usage else response
        return self._get_answer_blocking(prompt_text)

    def _get_answer_blocking(self, prompt_text: str) -> str:
        """
        Get a complete response in one request.
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
            return f"❌ OpenAI API error: {e}"

        reply = response.choices[0].message.content.strip()
        self.memory.recent_messages.append({"role": "assistant", "content": reply})
        self._check_memory_limit()
        return reply, response.usage.total_tokens if hasattr(response, "usage") else None

    def _get_answer_streaming(self, prompt_text: str) -> str:
        """
        Get a response streamed in chunks and print it progressively.
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
            return f"❌ OpenAI API error: {e}"

        full_reply = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
            if content:
                full_reply += content
                console.print(content, end="", soft_wrap=True)
        console.print()
        self.memory.recent_messages.append({"role": "assistant", "content": full_reply})
        self._check_memory_limit()
        return full_reply

    def _build_messages(self) -> list[dict]:
        """
        Build the message payload including system, summary, and recent turns.
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

    def _check_memory_limit(self):
        """
        If too many messages, summarize and truncate for next session turn.
        """
        if len(self.memory.recent_messages) >= self.config.memory_limit * 2:
            self.memory.summarize(
                client=self.client,
                model=self.config.model,
                memory_limit=self.config.memory_limit,
                max_summary_tokens=self.config.max_summary_tokens,
            )
