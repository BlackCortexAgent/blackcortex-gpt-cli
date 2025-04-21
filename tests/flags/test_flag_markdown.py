from argparse import Namespace
from unittest.mock import Mock

import pytest

from blackcortex_cli.config.config import Config
from blackcortex_cli.core.context import Context
from blackcortex_cli.core.log_manager import LogManager
from blackcortex_cli.flags.flag_markdown import set_markdown


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
    config.markdown_enabled = False  # Default value for tests
    log_manager = LogManager(config.log_file)
    log_manager.logger = Mock(spec=["info", "error", "debug", "addHandler"])
    log_manager._init_file_handler = Mock()
    return Context(config, log_manager)


def test_set_markdown_enable(context):
    """Test set_markdown enables Markdown when args.markdown is 'true'."""
    args = Namespace(markdown="true")
    set_markdown(args, context)
    assert context.config.markdown_enabled is True


def test_set_markdown_disable(context):
    """Test set_markdown disables Markdown when args.markdown is 'false'."""
    args = Namespace(markdown="false")
    set_markdown(args, context)
    assert context.config.markdown_enabled is False


def test_set_markdown_case_insensitive_true(context):
    """Test set_markdown handles case-insensitive 'TRUE' input."""
    args = Namespace(markdown="TRUE")
    set_markdown(args, context)
    assert context.config.markdown_enabled is True


def test_set_markdown_case_insensitive_false(context):
    """Test set_markdown handles case-insensitive 'False' input."""
    args = Namespace(markdown="False")
    set_markdown(args, context)
    assert context.config.markdown_enabled is False
