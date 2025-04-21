from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from blackcortex_cli.config.config import Config
from blackcortex_cli.core.context import Context
from blackcortex_cli.core.log_manager import LogManager
from blackcortex_cli.flags.flag_version import show_version


@pytest.fixture
def context(tmp_path):
    """Create a test context with a mocked LogManager."""
    config = Config()
    config.log_file = str(tmp_path / "gpt.log")
    log_manager = LogManager(config.log_file)
    log_manager.logger = Mock(spec=["info", "error", "debug", "addHandler"])
    log_manager._init_file_handler = Mock()
    return Context(config, log_manager)


def test_show_version_success(context):
    """Test show_version with a valid version string."""
    with (
        patch("blackcortex_cli.flags.flag_version.read_version", return_value="1.2.2"),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        show_version(Namespace(), context)
        mock_print.assert_called_once_with("1.2.2")


def test_show_version_empty(context):
    """Test show_version with an empty version string."""
    with (
        patch("blackcortex_cli.flags.flag_version.read_version", return_value=""),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        show_version(Namespace(), context)
        mock_print.assert_called_once_with("")


def test_show_version_metadata_error(context):
    """Test show_version when read_version raises an exception."""
    with (
        patch(
            "blackcortex_cli.flags.flag_version.read_version",
            side_effect=FileNotFoundError("Metadata file not found"),
        ),
        patch("blackcortex_cli.utils.console.console.print") as mock_print,
    ):
        show_version(Namespace(), context)
        mock_print.assert_called_once_with("")
