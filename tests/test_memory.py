import json
import os
from unittest.mock import MagicMock, patch

import pytest

from blackcortex_cli.memory import (
    load_memory,
    reset_memory,
    save_memory,
    summarize_recent,
)


@pytest.fixture
def temp_memory_file(tmp_path):
    """Fixture to create a temporary memory file."""
    temp_file = tmp_path / "memory.json"
    yield temp_file
    if temp_file.exists():
        temp_file.unlink()


def test_load_memory_nonexistent_path():
    """Test loading memory from a nonexistent path."""
    summary, recent = load_memory("/nonexistent/path/memory.json")
    assert summary == ""
    assert recent == []


def test_load_memory_corrupted_json(tmp_path):
    """Test behavior when attempting to load a malformed JSON memory file."""
    path = tmp_path / "corrupt.json"
    path.write_text("{ invalid json")
    with patch("blackcortex_cli.memory.console.print") as mock_print:
        summary, recent = load_memory(str(path))
        mock_print.assert_called_once()
        assert summary == ""
        assert recent == []


def test_save_memory_empty_data(temp_memory_file):
    """Test saving empty summary and recent messages to file."""
    save_memory(str(temp_memory_file), "", [])
    with open(temp_memory_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["summary"] == ""
    assert data["recent"] == []


def test_save_memory_sets_permissions(temp_memory_file):
    """Ensure saved memory file is set to permissions 600 (user read/write only)."""
    save_memory(str(temp_memory_file), "sum", ["msg"])
    assert oct(os.stat(temp_memory_file).st_mode & 0o777) == "0o600"


def test_reset_memory_permission_error(temp_memory_file):
    """Simulate permission error when trying to delete a memory file."""
    temp_memory_file.touch()

    with (
        patch("os.remove", side_effect=PermissionError),
        patch("blackcortex_cli.memory.console.print") as mock_print,
    ):
        summary, recent = reset_memory(str(temp_memory_file))
        mock_print.assert_called_once_with(
            "[bold red]⚠️ Failed to reset memory file due to permission error.[/bold red]"
        )
        assert summary == ""
        assert recent == []


def test_summarize_recent_empty_messages(temp_memory_file):
    """Test that summarization is skipped and memory is saved when no recent messages exist."""
    client = MagicMock()
    rolling_summary = "Initial summary"
    recent_messages = []
    memory_limit = 2
    max_summary_tokens = 50

    with patch("blackcortex_cli.memory.save_memory") as mock_save:
        new_summary, new_recent = summarize_recent(
            client,
            "test-model",
            str(temp_memory_file),
            rolling_summary,
            recent_messages,
            memory_limit,
            max_summary_tokens,
        )
        assert new_summary == rolling_summary
        assert new_recent == []
        mock_save.assert_called_once_with(str(temp_memory_file), rolling_summary, [])


def test_summarize_recent_failure(temp_memory_file):
    """Test fallback behavior when summarization API call fails."""
    client = MagicMock()
    client.chat.completions.create.side_effect = Exception("API error")

    rolling_summary = "Initial summary"
    recent_messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
    memory_limit = 2
    max_summary_tokens = 50

    with patch("blackcortex_cli.memory.console.print") as mock_print:
        new_summary, new_recent = summarize_recent(
            client,
            "test-model",
            str(temp_memory_file),
            rolling_summary,
            recent_messages,
            memory_limit,
            max_summary_tokens,
        )

        assert new_summary == rolling_summary
        assert new_recent == recent_messages
        mock_print.assert_called_once_with("[bold red]Summary failed:[/bold red] API error")


def test_summarize_recent_success(temp_memory_file):
    """Test successful summarization updates the memory file with the new summary."""
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content.strip.return_value = "Updated summary"
    client.chat.completions.create.return_value = mock_response

    new_summary, new_recent = summarize_recent(
        client,
        "gpt-4",
        str(temp_memory_file),
        "Old summary",
        [{"role": "user", "content": "How are you?"}],
        memory_limit=2,
        max_summary_tokens=100,
    )

    assert new_summary == "Updated summary"
    assert new_recent == []
