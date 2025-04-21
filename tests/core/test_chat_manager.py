from unittest.mock import MagicMock, patch

import pytest
from openai import OpenAIError

from blackcortex_cli.core.chat_manager import ChatManager


# Fixture to mock the OpenAI client
@pytest.fixture
def mock_openai_client(monkeypatch):
    """Mock the OpenAI client used by ChatManager."""
    mock_client = MagicMock()
    monkeypatch.setattr("blackcortex_cli.core.chat_manager.OpenAI", lambda **kwargs: mock_client)
    return lambda: mock_client


# Fixture to create a ChatManager instance with a mocked config
@pytest.fixture
def chat_manager(mock_openai_client):
    """Provide a ChatManager instance with a mocked configuration."""
    config = MagicMock()
    config.api_key = "test_key"
    config.stream_enabled = False  # Default to non-streaming
    config.model = "gpt-4o"
    config.temperature = 0.5
    config.max_tokens = 4096
    config.memory_limit = 10
    config.memory_path = "/tmp/test_memory.json"
    config.default_prompt = ""
    return ChatManager(config)


# Test initialization
def test_initialization(chat_manager):
    """Ensure ChatManager initializes with the correct configuration."""
    assert chat_manager.client is not None
    assert chat_manager.config.api_key == "test_key"
    assert chat_manager.config.model == "gpt-4o"
    assert chat_manager.config.memory_limit == 10


# Test get_answer in non-streaming mode
def test_get_answer_non_streaming(chat_manager, mock_openai_client):
    """Verify get_answer returns the correct response and token usage in non-streaming mode."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
    mock_response.usage = MagicMock(total_tokens=10)
    mock_openai_client().chat.completions.create.return_value = mock_response

    response, tokens, timestamp = chat_manager.get_answer("Test input", return_usage=True)
    assert response == "Test response"
    assert tokens == 10
    assert timestamp is not None


# Test get_answer in streaming mode with markdown
def test_get_answer_streaming(chat_manager, mock_openai_client):
    """Check that get_answer handles streaming responses correctly with markdown."""
    chat_manager.config.stream_enabled = True
    chat_manager.stream_enabled = True
    chat_manager.config.markdown_enabled = True
    # Mock a streaming response
    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock(delta=MagicMock(content="chunk1 "))]
    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock(delta=MagicMock(content="chunk2"))]
    mock_chunk3 = MagicMock()
    mock_chunk3.choices = [MagicMock(delta=MagicMock(content=None))]
    mock_openai_client().chat.completions.create.return_value = iter(
        [mock_chunk1, mock_chunk2, mock_chunk3]
    )

    with (
        patch("blackcortex_cli.core.chat_manager.Live") as mock_live,
        patch("blackcortex_cli.core.chat_manager.print_wrapped"),
    ):
        mock_live_instance = MagicMock()
        mock_live.return_value.__enter__.return_value = mock_live_instance
        response, tokens, timestamp = chat_manager.get_answer("Test input", return_usage=True)
        assert response == "chunk1 chunk2"
        assert tokens >= 0
        assert timestamp is not None
        mock_live_instance.update.assert_called()
        mock_live_instance.refresh.assert_called()


# Test get_answer in streaming mode without markdown
def test_get_answer_streaming_no_markdown(chat_manager, mock_openai_client):
    """Check that get_answer handles streaming responses correctly without markdown."""
    chat_manager.config.stream_enabled = True
    chat_manager.stream_enabled = True
    chat_manager.config.markdown_enabled = False
    # Mock a streaming response
    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock(delta=MagicMock(content="chunk1 "))]
    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock(delta=MagicMock(content="chunk2"))]
    mock_chunk3 = MagicMock()
    mock_chunk3.choices = [MagicMock(delta=MagicMock(content=None))]
    mock_openai_client().chat.completions.create.return_value = iter(
        [mock_chunk1, mock_chunk2, mock_chunk3]
    )

    with (
        patch("blackcortex_cli.core.chat_manager.Live", return_value=MagicMock()),
        patch("blackcortex_cli.core.chat_manager.print_wrapped") as mock_print_wrapped,
    ):
        response, tokens, timestamp = chat_manager.get_answer("Test input", return_usage=True)
        assert response == "chunk1 chunk2"
        assert tokens >= 0
        assert timestamp is not None
        mock_print_wrapped.assert_called()


# Test error handling with parameterized scenarios
@pytest.mark.parametrize(
    "exception, expected_error, should_raise",
    [
        (OpenAIError("API error"), "API error", False),
        (TimeoutError("Timeout"), "Timeout", True),
    ],
)
def test_get_answer_error_handling(
    chat_manager, mock_openai_client, exception, expected_error, should_raise
):
    """Ensure get_answer handles API errors appropriately."""
    mock_openai_client().chat.completions.create.side_effect = exception
    if should_raise:
        with pytest.raises(type(exception), match=expected_error):
            chat_manager.get_answer("Test input", return_usage=True)
    else:
        response, tokens, timestamp = chat_manager.get_answer("Test input", return_usage=True)
        assert "[x] OpenAI API error" in response
        assert tokens is None
        assert timestamp is not None


# Test context management across multiple turns
def test_get_answer_multi_turn(chat_manager, mock_openai_client):
    """Validate that conversation context is maintained across multiple calls."""
    mock_response1 = MagicMock()
    mock_response1.choices = [MagicMock(message=MagicMock(content="Response 1"))]
    mock_response1.usage = MagicMock(total_tokens=5)
    mock_response2 = MagicMock()
    mock_response2.choices = [MagicMock(message=MagicMock(content="Response 2"))]
    mock_response2.usage = MagicMock(total_tokens=10)
    mock_openai_client().chat.completions.create.side_effect = [mock_response1, mock_response2]

    with patch("blackcortex_cli.core.context_memory.ContextMemory.check_memory_limit"):
        response, tokens, timestamp = chat_manager.get_answer("Hello", return_usage=True)
        response, tokens, timestamp = chat_manager.get_answer("How are you?", return_usage=True)

    call_args = mock_openai_client().chat.completions.create.call_args_list[1]
    messages = call_args[1]["messages"]
    assert len(messages) >= 2
    assert any(msg["content"] == "Hello" for msg in messages)
    assert any(msg["content"] == "How are you?" for msg in messages)


# Test _estimate_tokens exception handling
def test_estimate_tokens_exception(chat_manager, monkeypatch):
    """Test _estimate_tokens handles exceptions gracefully."""

    def mock_encode(*args, **kwargs):
        raise ValueError("Encoding error")

    monkeypatch.setattr("tiktoken.encoding_for_model", lambda x: MagicMock(encode=mock_encode))
    tokens = chat_manager._estimate_tokens([{"role": "user", "content": "Test"}], "Response")
    assert tokens == 0


# Test get_answer in blocking mode with return_usage=False
def test_get_answer_blocking_no_usage(chat_manager, mock_openai_client):
    """Verify get_answer in blocking mode with return_usage=False."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
    mock_response.usage = None  # Simulate no usage data
    mock_openai_client().chat.completions.create.return_value = mock_response

    response, tokens, timestamp = chat_manager.get_answer("Test input", return_usage=False)
    assert response == "Test response"
    assert tokens is None
    assert timestamp is not None


# Test get_answer in blocking mode with missing usage
def test_get_answer_blocking_missing_usage(chat_manager, mock_openai_client):
    """Verify get_answer in blocking mode when response lacks usage data."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
    del mock_response.usage  # Simulate missing usage attribute
    mock_openai_client().chat.completions.create.return_value = mock_response

    response, tokens, timestamp = chat_manager.get_answer("Test input", return_usage=True)
    assert response == "Test response"
    assert tokens is None
    assert timestamp is not None
