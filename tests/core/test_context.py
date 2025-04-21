from unittest.mock import MagicMock, patch

import pytest

from blackcortex_cli.config.config import Config
from blackcortex_cli.core.chat_manager import ChatManager
from blackcortex_cli.core.context import Context
from blackcortex_cli.core.log_manager import LogManager


# Fixture for a mocked Config object
@pytest.fixture
def mock_config(tmp_path):
    """Provide a mocked Config object with a temporary log file path."""
    config = MagicMock(spec=Config)
    config.log_file = str(tmp_path / "test.log")
    config.log_level = "INFO"
    config.log_to_console = True
    return config


# Fixture for a mocked LogManager
@pytest.fixture
def mock_log_manager():
    """Provide a mocked LogManager instance."""
    return MagicMock(spec=LogManager)


# Fixture for a mocked ChatManager
@pytest.fixture
def mock_chat_manager():
    """Provide a mocked ChatManager instance."""
    return MagicMock(spec=ChatManager)


# Test initialization with default LogManager
def test_init_default_log_manager(mock_config):
    """Test Context initialization with default LogManager."""
    with patch("blackcortex_cli.core.context.LogManager") as mock_log_manager_class:
        mock_log_manager_instance = MagicMock(spec=LogManager)
        mock_log_manager_class.return_value = mock_log_manager_instance

        context = Context(mock_config)

        assert context.config == mock_config
        assert context.log_manager == mock_log_manager_instance
        assert context.chat_manager is None
        mock_log_manager_class.assert_called_once_with(
            mock_config.log_file, mock_config.log_level, mock_config.log_to_console
        )


# Test initialization with custom LogManager
def test_init_custom_log_manager(mock_config, mock_log_manager):
    """Test Context initialization with a custom LogManager."""
    context = Context(mock_config, log_manager=mock_log_manager)

    assert context.config == mock_config
    assert context.log_manager == mock_log_manager
    assert context.chat_manager is None
    # Ensure LogManager was not instantiated
    with patch("blackcortex_cli.core.context.LogManager") as mock_log_manager_class:
        mock_log_manager_class.assert_not_called()


# Test initialization with custom ChatManager
def test_init_custom_chat_manager(mock_config, mock_chat_manager):
    """Test Context initialization with a custom ChatManager."""
    context = Context(mock_config, chat_manager=mock_chat_manager)

    assert context.config == mock_config
    assert isinstance(context.log_manager, LogManager)  # Default LogManager created
    assert context.chat_manager == mock_chat_manager


# Test initialization with both custom LogManager and ChatManager
def test_init_custom_both_managers(mock_config, mock_log_manager, mock_chat_manager):
    """Test Context initialization with custom LogManager and ChatManager."""
    context = Context(mock_config, log_manager=mock_log_manager, chat_manager=mock_chat_manager)

    assert context.config == mock_config
    assert context.log_manager == mock_log_manager
    assert context.chat_manager == mock_chat_manager
    # Ensure LogManager was not instantiated
    with patch("blackcortex_cli.core.context.LogManager") as mock_log_manager_class:
        mock_log_manager_class.assert_not_called()


# Test initialization with None for log_manager and chat_manager
def test_init_none_managers(mock_config):
    """Test Context initialization with None for log_manager and chat_manager."""
    with patch("blackcortex_cli.core.context.LogManager") as mock_log_manager_class:
        mock_log_manager_instance = MagicMock(spec=LogManager)
        mock_log_manager_class.return_value = mock_log_manager_instance

        context = Context(mock_config, log_manager=None, chat_manager=None)

        assert context.config == mock_config
        assert context.log_manager == mock_log_manager_instance
        assert context.chat_manager is None
        mock_log_manager_class.assert_called_once_with(
            mock_config.log_file, mock_config.log_level, mock_config.log_to_console
        )
