"""
Configuration manager for GPT-CLI.

Loads environment variables, applies defaults,
and expands user paths for runtime configuration.
"""

import os

try:  # pragma: no cover
    from dotenv import load_dotenv

    load_dotenv()  # pragma: no cover
    load_dotenv(os.path.expanduser("~/.gpt-cli/.env"))  # pragma: no cover
except ImportError:  # pragma: no cover
    pass  # pragma: no cover


class Config:
    """
    Central configuration loader for GPT CLI.
    Pulls from environment variables with defaults.
    """

    def __init__(self):
        self.api_key: str | None = os.getenv("OPENAI_API_KEY")

        self.model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.default_prompt: str = os.getenv("OPENAI_DEFAULT_PROMPT", "")

        self.log_file: str = os.path.expanduser(os.getenv("OPENAI_LOGFILE", "~/.gpt.log"))
        self.memory_path: str = os.path.expanduser(
            os.getenv("OPENAI_MEMORY_PATH", "~/.gpt_memory.json")
        )

        self.temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.5"))
        self.max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))
        self.max_summary_tokens: int = int(os.getenv("OPENAI_MAX_SUMMARY_TOKENS", "2048"))
        self.memory_limit: int = int(os.getenv("OPENAI_MEMORY_LIMIT", "10"))

        self.stream_enabled: bool = os.getenv("OPENAI_STREAM_ENABLED", "false").lower() == "true"
