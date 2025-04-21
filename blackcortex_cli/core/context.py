# blackcortex_cli/core/context.py

"""
Context initializer for GPT CLI core components.

This module encapsulates the construction and management of core components,
such as the chat manager and log manager, tied to a specific configuration instance.
"""

from blackcortex_cli.config.config import Config
from blackcortex_cli.core.chat_manager import ChatManager
from blackcortex_cli.core.log_manager import LogManager


class Context:
    def __init__(
        self, config: Config, log_manager: LogManager = None, chat_manager: ChatManager = None
    ):
        """
        Initialize the application context with config, log manager, and chat manager.

        Args:
            config: The CLI configuration instance.
            log_manager: Optional custom LogManager. If not provided, one is created.
            chat_manager: Optional custom ChatManager. If not provided, can be set later.
        """
        self.config = config
        self.log_manager = log_manager or LogManager(
            config.log_file, config.log_level, config.log_to_console
        )
        self.chat_manager = chat_manager
