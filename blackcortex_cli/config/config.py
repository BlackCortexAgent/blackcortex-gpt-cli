# blackcortex_cli/config/config.py

"""
Configuration manager for GPT-CLI.

Loads environment variables from .env files, sets default values for model parameters,
logging, memory, and runtime settings. Provides a centralized Config object used throughout the CLI.
"""

import os

from blackcortex_cli.config.paths import get_cli_path, get_env_path


def load_env() -> bool:
    """
    Load environment variables from .env files and ensure CLI_PATH exists with proper permissions.

    Returns:
        bool: True if the dotenv module is available and loading succeeded, False otherwise.
    """
    try:
        from dotenv import load_dotenv

        cli_path = get_cli_path()
        try:
            os.makedirs(cli_path, exist_ok=True)
            os.chmod(cli_path, 0o770)
        except OSError as e:
            print(f"Warning: Failed to create or set permissions for {cli_path}: {e}")

        load_dotenv()
        load_dotenv(get_env_path())
        return True
    except ImportError:
        return False


class Config:
    """
    Configuration object for the GPT CLI.

    Loads environment variables and provides default values for OpenAI API settings,
    memory handling, logging, and runtime behavior.
    """

    def __init__(self):
        load_env()

        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("MODEL", "gpt-4o")
        self.summary_model = os.getenv("SUMMARY_MODEL", "gpt-3.5-turbo")
        self.default_prompt = os.getenv("DEFAULT_PROMPT", "")
        self.temperature = float(os.getenv("TEMPERATURE", "0.5"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4096"))

        cli_path = get_cli_path()
        self.memory_path = os.getenv("MEMORY_PATH", os.path.join(cli_path, "memory.json"))
        self.history_path = os.getenv("HISTORY_PATH", os.path.join(cli_path, "history"))
        self.memory_limit = int(os.getenv("MEMORY_LIMIT", "10"))
        self.max_summary_tokens = int(os.getenv("MAX_SUMMARY_TOKENS", "2048"))

        self.log_file = os.getenv("LOG_FILE", os.path.join(cli_path, "gpt.log"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_to_console = os.getenv("LOG_TO_CONSOLE", "false").lower() == "true"

        self.markdown_enabled = os.getenv("MARKDOWN_ENABLED", "true").lower() == "true"
        self.stream_enabled = os.getenv("STREAM_ENABLED", "false").lower() == "true"
