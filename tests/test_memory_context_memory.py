"""
Unit tests for ContextMemory in blackcortex_cli.memory.context_memory.

Covers loading, saving, resetting, and summarization behavior with and without errors.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from openai import OpenAIError

from blackcortex_cli.memory.context_memory import ContextMemory


@pytest.fixture
def temp_memory_path():
    """Provide a temporary file path for memory storage."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    if os.path.exists(f.name):
        os.remove(f.name)


@pytest.fixture
def memory(temp_memory_path):
    """Return a fresh ContextMemory instance."""
    return ContextMemory(temp_memory_path)


def test_load_valid_file(memory):
    """
    Test load() correctly loads summary and recent messages from a valid JSON file.
    """
    content = {"summary": "Summary here", "recent": [{"role": "user", "content": "Hi"}]}
    with open(memory.path, "w", encoding="utf-8") as f:
        json.dump(content, f)

    summary, recent = memory.load()

    assert summary == "Summary here"
    assert recent == [{"role": "user", "content": "Hi"}]


@patch("blackcortex_cli.memory.context_memory.console.print")
def test_load_corrupted_file(mock_print, memory):
    """
    Test load() handles corrupted file gracefully and resets memory.
    """
    with open(memory.path, "w", encoding="utf-8") as f:
        f.write("not-json")

    summary, recent = memory.load()

    assert summary == ""
    assert recent == []
    mock_print.assert_called_once()


def test_save_persists_to_disk(memory):
    """
    Test save() writes the correct JSON structure to disk.
    """
    memory.rolling_summary = "Updated summary"
    memory.recent_messages = [{"role": "assistant", "content": "Sure!"}]
    memory.save()

    with open(memory.path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["summary"] == "Updated summary"
    assert data["recent"] == [{"role": "assistant", "content": "Sure!"}]
    assert os.stat(memory.path).st_mode & 0o777 == 0o600


@patch("blackcortex_cli.memory.context_memory.console.print")
def test_reset_deletes_existing_file(mock_print, memory):
    """
    Test reset() deletes existing file and clears in-memory data.
    """
    memory.rolling_summary = "Old"
    memory.recent_messages = [{"role": "user", "content": "Before reset"}]
    memory.save()

    summary, recent = memory.reset()

    assert summary == ""
    assert recent == []
    assert not os.path.exists(memory.path)
    mock_print.assert_called_once()


@patch("blackcortex_cli.memory.context_memory.console.print")
def test_reset_handles_missing_file(mock_print, memory):
    """
    Test reset() handles non-existent file gracefully.
    """
    os.remove(memory.path)
    summary, recent = memory.reset()

    assert summary == ""
    assert recent == []
    mock_print.assert_called_once_with("[blue]ℹ️ No memory file to reset.[/blue]\n")


@patch("blackcortex_cli.memory.context_memory.console.print")
def test_summarize_with_recent_messages(mock_print, memory):
    """
    Test summarize() sends prompt and clears recent_messages on success.
    """
    memory.rolling_summary = "Initial summary."
    memory.recent_messages = [
        {"role": "user", "content": "What is AI?"},
        {"role": "assistant", "content": "AI is Artificial Intelligence."},
    ]
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Updated summary."))]
    mock_client.chat.completions.create.return_value = mock_response

    summary, recent = memory.summarize(
        client=mock_client,
        model="gpt-3.5-turbo",
        memory_limit=2,
        max_summary_tokens=64,
    )

    assert summary == "Updated summary."
    assert recent == []
    assert memory.rolling_summary == "Updated summary."


@patch("blackcortex_cli.memory.context_memory.console.print")
def test_summarize_handles_exception(mock_print, memory):
    """
    Test summarize() logs error and retains messages if summarization fails.
    """
    memory.rolling_summary = "Initial summary."
    memory.recent_messages = [{"role": "user", "content": "Hi"}]
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Boom")

    summary, recent = memory.summarize(
        client=mock_client,
        model="gpt-3.5-turbo",
        memory_limit=2,
        max_summary_tokens=64,
    )

    assert summary == "Initial summary."
    assert recent == [{"role": "user", "content": "Hi"}]
    mock_print.assert_called_once()


@patch("blackcortex_cli.memory.context_memory.console.print")
def test_summarize_openaierror(mock_print, memory):
    """
    Test summarize handles OpenAIError gracefully.
    """
    memory.recent_messages = [{"role": "user", "content": "fail"}]
    memory.rolling_summary = "previous summary"

    client = MagicMock()
    client.chat.completions.create.side_effect = OpenAIError("failed")

    summary, recent = memory.summarize(
        client=client,
        model="gpt-3.5-turbo",
        memory_limit=2,
        max_summary_tokens=64,
    )

    assert summary == "previous summary"
    assert recent == [{"role": "user", "content": "fail"}]
    mock_print.assert_called_once()


def test_summarize_with_no_recent_messages(memory):
    """
    Test summarize does nothing and saves when recent_messages is empty.
    """
    memory.rolling_summary = "Existing summary"
    memory.recent_messages = []

    memory.save = MagicMock()

    client = MagicMock()

    summary, recent = memory.summarize(
        client=client,
        model="gpt-3.5-turbo",
        memory_limit=2,
        max_summary_tokens=64,
    )

    assert summary == "Existing summary"
    assert recent == []
    memory.save.assert_called_once()


@patch("blackcortex_cli.memory.context_memory.console.print")
def test_summarize_handles_openaierror_specific(mock_print, memory):
    """
    Test summarize handles OpenAIError and logs correctly.
    """
    memory.rolling_summary = "Existing summary"
    memory.recent_messages = [{"role": "user", "content": "test"}]

    client = MagicMock()
    client.chat.completions.create.side_effect = OpenAIError("fail")

    summary, recent = memory.summarize(
        client=client,
        model="gpt-4",
        memory_limit=2,
        max_summary_tokens=64,
    )

    assert summary == "Existing summary"
    assert recent == [{"role": "user", "content": "test"}]
    mock_print.assert_called_once()
