from unittest.mock import MagicMock

import pytest

from blackcortex_cli.core.context import Context
from blackcortex_cli.flags.flag_clear_memory import clear_memory


@pytest.fixture
def mock_context():
    """Fixture for a mocked Context object with a ChatManager."""
    config = MagicMock()
    chat_manager = MagicMock()
    context = MagicMock(spec=Context)
    context.config = config
    context.chat_manager = chat_manager
    return context


def test_clear_memory(mock_context):
    """Test clear_memory calls ChatManager.memory.clear."""
    clear_memory(MagicMock(), mock_context)
    mock_context.chat_manager.memory.clear.assert_called_once()
