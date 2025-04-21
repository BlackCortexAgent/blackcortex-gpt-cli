from argparse import Namespace
from unittest.mock import Mock, mock_open, patch

import pytest

from blackcortex_cli.config.config import Config
from blackcortex_cli.core.context import Context
from blackcortex_cli.core.log_manager import LogManager
from blackcortex_cli.flags.flag_log import show_log


# Fixture to prevent .gpt-cli directory creation
@pytest.fixture(autouse=True)
def prevent_gpt_cli_dir(monkeypatch):
    """Mock file system operations to prevent .gpt-cli directory creation."""
    monkeypatch.setattr("os.makedirs", Mock())
    monkeypatch.setattr("os.chmod", Mock(side_effect=OSError("Mocked chmod")))
    # Mock load_env to prevent .env loading and directory creation
    monkeypatch.setattr("blackcortex_cli.config.config.load_env", lambda: False)
    yield


# Fixture for a test context with a mocked Config and LogManager
@pytest.fixture
def context(tmp_path, monkeypatch):
    """Create a test context with a mocked Config and LogManager."""
    # Mock Config to avoid real initialization
    config = Mock(spec=Config)
    config.log_file = str(tmp_path / "gpt.log")
    log_manager = LogManager(config.log_file)
    log_manager.logger = Mock(spec=["info", "error", "debug", "addHandler"])
    log_manager._init_file_handler = Mock()
    return Context(config, log_manager)


def test_show_log_success(context):
    """Test show_log displays log content successfully."""
    context.log_manager.show = Mock()
    with patch("builtins.open", mock_open(read_data="Log content\n")):
        show_log(Namespace(), context)
    context.log_manager.show.assert_called_once()


def test_show_log_empty_file(context):
    """Test show_log with an empty log file."""
    context.log_manager.show = Mock()
    with patch("builtins.open", mock_open(read_data="")):
        show_log(Namespace(), context)
    context.log_manager.show.assert_called_once()


def test_show_log_non_existent_file(context):
    """Test show_log when the log file does not exist."""
    context.log_manager.show = Mock(side_effect=FileNotFoundError("No such file"))
    with pytest.raises(FileNotFoundError, match="No such file"):
        show_log(Namespace(), context)
    context.log_manager.show.assert_called_once()


def test_show_log_permission_error(context):
    """Test show_log with a permission error."""
    context.log_manager.show = Mock(side_effect=PermissionError("Permission denied"))
    with pytest.raises(PermissionError, match="Permission denied"):
        show_log(Namespace(), context)
    context.log_manager.show.assert_called_once()
