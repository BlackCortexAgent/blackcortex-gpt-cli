"""
Unit tests for ChatManager in blackcortex_cli.core.chat.

Covers initialization, blocking and streaming answer retrieval,
prompt building, memory checks, and OpenAI API error handling.
"""

from unittest.mock import MagicMock, patch

import pytest
from openai import OpenAIError

from blackcortex_cli.core.chat import ChatManager


class DummyConfig:
    """Dummy configuration class for ChatManager tests."""

    api_key = "test"
    model = "gpt-3.5-turbo"
    temperature = 0.5
    max_tokens = 50
    max_summary_tokens = 25
    memory_path = "/tmp/memory.json"
    memory_limit = 2
    default_prompt = "Be concise."


@pytest.fixture
def dummy_config():
    """Fixture providing a dummy config object."""
    return DummyConfig()


@pytest.fixture
def chat_manager(dummy_config):
    """Fixture creating a ChatManager with patched OpenAI and ContextMemory."""
    with (
        patch("blackcortex_cli.core.chat.OpenAI") as mock_openai,
        patch("blackcortex_cli.core.chat.ContextMemory") as mock_memory,
    ):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        memory_instance = MagicMock()
        memory_instance.recent_messages = []
        memory_instance.rolling_summary = ""
        mock_memory.return_value = memory_instance
        manager = ChatManager(dummy_config)
        manager.client = mock_client
        manager.memory = memory_instance
        yield manager


def test_init_loads_memory(dummy_config):
    """
    Test ChatManager.__init__ loads memory and sets properties.
    """
    with (
        patch("blackcortex_cli.core.chat.OpenAI"),
        patch("blackcortex_cli.core.chat.ContextMemory") as mock_memory,
    ):
        instance = MagicMock()
        mock_memory.return_value = instance
        ChatManager(dummy_config)
        instance.load.assert_called_once()


def test_get_answer_blocking_success(chat_manager):
    """
    Test get_answer (blocking) appends user message, calls OpenAI,
    handles response, and updates memory correctly.
    """
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content="Reply!"))]
    response.usage = MagicMock(total_tokens=42)
    chat_manager.client.chat.completions.create.return_value = response

    result, usage = chat_manager.get_answer("Hello!", return_usage=True)
    assert result == "Reply!"
    assert usage == 42
    assert chat_manager.memory.recent_messages[-2] == {"role": "user", "content": "Hello!"}
    assert chat_manager.memory.recent_messages[-1] == {"role": "assistant", "content": "Reply!"}


def test_get_answer_blocking_api_error(chat_manager):
    """
    Test get_answer returns error string when OpenAIError is raised during blocking call.
    """
    chat_manager.client.chat.completions.create.side_effect = OpenAIError("Bad")
    result = chat_manager.get_answer("fail")
    assert "OpenAI API error" in result


@patch("blackcortex_cli.core.chat.console.print")
def test_get_answer_streaming_prints_and_appends(mock_print, chat_manager):
    """
    Test _get_answer_streaming streams response, prints it, and updates memory.
    """
    chunk = MagicMock()
    chunk.choices = [MagicMock(delta=MagicMock(content="Hi"))]
    chat_manager.client.chat.completions.create.return_value = iter([chunk])
    chat_manager.stream_enabled = True

    result = chat_manager.get_answer("Stream?", return_usage=False)

    assert "Hi" in result
    assert {"role": "user", "content": "Stream?"} in chat_manager.memory.recent_messages
    assert {"role": "assistant", "content": "Hi"} in chat_manager.memory.recent_messages
    mock_print.assert_any_call("Hi", end="", soft_wrap=True)
    mock_print.assert_any_call()  # Final line break


@patch("blackcortex_cli.core.chat.console.print")
def test_get_answer_streaming_api_error(mock_console_print, chat_manager):
    """
    Test that streaming errors from OpenAI are caught and return an error string.
    """
    chat_manager.client.chat.completions.create.side_effect = OpenAIError("fail")
    chat_manager.stream_enabled = True

    result = chat_manager.get_answer("fail")
    assert "OpenAI API error" in result


def test_build_messages_includes_all(chat_manager):
    """
    Test _build_messages includes system intro, default prompt, summary, and recent memory messages.
    """
    chat_manager.memory.rolling_summary = "summary text"
    chat_manager.memory.recent_messages = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "Q2"},
    ]
    messages = chat_manager._build_messages()
    assert messages[0]["role"] == "system"
    assert "INTRO" in messages[0]["content"]
    assert messages[1]["content"].startswith("INSTRUCTIONS")
    assert messages[2]["content"].startswith("SUMMARY")
    assert messages[-2:] == [
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "Q2"},
    ]


def test_check_memory_limit_triggers_summary(chat_manager):
    """
    Test _check_memory_limit triggers summarization when memory exceeds limit.
    """
    chat_manager.memory.recent_messages = [{}] * (chat_manager.config.memory_limit * 2)
    chat_manager.memory.summarize = MagicMock()
    chat_manager._check_memory_limit()
    chat_manager.memory.summarize.assert_called_once()


def test_check_memory_limit_no_trigger(chat_manager):
    """
    Test _check_memory_limit does not summarize if under memory limit.
    """
    chat_manager.memory.recent_messages = [{}] * (chat_manager.config.memory_limit * 2 - 1)
    chat_manager.memory.summarize = MagicMock()
    chat_manager._check_memory_limit()
    chat_manager.memory.summarize.assert_not_called()


def test_get_answer_blocking_without_usage(chat_manager):
    """
    Test get_answer handles missing usage attribute gracefully (returns None).
    """
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content="Test response"))]
    del response.usage  # Simulate attribute not present

    chat_manager.client.chat.completions.create.return_value = response
    result = chat_manager.get_answer("no usage", return_usage=True)
    assert result == ("Test response", None)


@patch("blackcortex_cli.core.chat.console.print")
def test_get_answer_streaming_skips_empty_chunks(mock_print, chat_manager):
    """
    Test that empty or null chunks are skipped during streaming and nothing is printed.
    """
    chunk_none = MagicMock()
    chunk_none.choices = [MagicMock(delta=None)]

    chunk_empty = MagicMock()
    chunk_empty.choices = [MagicMock(delta=MagicMock(content=""))]

    chat_manager.client.chat.completions.create.return_value = iter([chunk_none, chunk_empty])
    chat_manager.stream_enabled = True

    result = chat_manager.get_answer("Empty stream test")

    assert result == ""
    mock_print.assert_any_call()
