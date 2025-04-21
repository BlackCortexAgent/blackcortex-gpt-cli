from unittest.mock import MagicMock

import pytest

from blackcortex_cli.core.context import Context
from blackcortex_cli.flags.flag_clear_log import clear_log


@pytest.fixture
def mock_context():
    """Fixture for a mocked Context object with a LogManager."""
    config = MagicMock()
    log_manager = MagicMock()
    context = MagicMock(spec=Context)
    context.config = config
    context.log_manager = log_manager
    return context


def test_clear_log(mock_context):
    """Test clear_log calls LogManager.clear."""
    clear_log(MagicMock(), mock_context)
    mock_context.log_manager.clear.assert_called_once()
