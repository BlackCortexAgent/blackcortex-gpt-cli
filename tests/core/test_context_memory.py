import pytest
from unittest.mock import patch, MagicMock
from blackcortex_cli.core.context_memory import ContextMemory
from openai import OpenAIError
import os
import json


# Fixture for a temporary memory file
@pytest.fixture
def temp_memory_file(tmp_path):
    """Provide a temporary file path for memory storage."""
    return str(tmp_path / "memory.json")


# Fixture to mock the OpenAI client
@pytest.fixture
def mock_openai_client(monkeypatch):
    """Mock the OpenAI client used for summarization."""
    mock_client = MagicMock()
    monkeypatch.setattr("blackcortex_cli.core.context_memory.OpenAI", lambda **kwargs: mock_client)
    return mock_client


# Fixture to mock the configuration
@pytest.fixture
def mock_config():
    """Provide a mocked configuration object."""
    config = MagicMock()
    config.memory_limit = 5
    config.summary_model = "gpt-4o-mini"
    config.max_summary_tokens = 100
    return config


# Test initialization
def test_initialization(temp_memory_file):
    """Test ContextMemory initializes with the correct file path."""
    memory = ContextMemory(temp_memory_file)
    assert memory.path == temp_memory_file
    assert memory.rolling_summary == ""
    assert memory.recent_messages == []


# Test loading a valid memory file
def test_load_valid_file(temp_memory_file, monkeypatch):
    """Test loading a valid JSON memory file."""
    memory_data = {"summary": "Test summary", "recent": [{"role": "user", "content": "Hello"}]}
    with open(temp_memory_file, "w", encoding="utf-8") as f:
        json.dump(memory_data, f)

    memory = ContextMemory(temp_memory_file)
    summary, messages = memory.load()
    assert summary == "Test summary"
    assert messages == [{"role": "user", "content": "Hello"}]
    assert memory.rolling_summary == "Test summary"
    assert memory.recent_messages == [{"role": "user", "content": "Hello"}]


# Test loading a corrupted memory file
def test_load_corrupted_file(temp_memory_file, monkeypatch, capsys):
    """Test loading a corrupted JSON memory file resets memory."""
    with open(temp_memory_file, "w", encoding="utf-8") as f:
        f.write("invalid json")

    memory = ContextMemory(temp_memory_file)
    summary, messages = memory.load()
    captured = capsys.readouterr()
    assert "Corrupted memory file. Resetting..." in captured.out
    assert summary == ""
    assert messages == []
    assert memory.rolling_summary == ""
    assert memory.recent_messages == []


# Test loading a non-existent file
def test_load_non_existent_file(temp_memory_file):
    """Test loading when the memory file does not exist."""
    memory = ContextMemory(temp_memory_file)
    summary, messages = memory.load()
    assert summary == ""
    assert messages == []
    assert memory.rolling_summary == ""
    assert memory.recent_messages == []


# Test saving memory
def test_save(temp_memory_file, monkeypatch):
    """Test saving memory state to disk with correct permissions."""
    mock_chmod = MagicMock()
    monkeypatch.setattr(os, "chmod", mock_chmod)

    memory = ContextMemory(temp_memory_file)
    memory.rolling_summary = "Test summary"
    memory.recent_messages = [{"role": "user", "content": "Hello"}]
    memory.save()

    with open(temp_memory_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["summary"] == "Test summary"
    assert data["recent"] == [{"role": "user", "content": "Hello"}]
    mock_chmod.assert_called_once_with(temp_memory_file, 0o660)


# Test clearing memory with existing file
def test_clear_existing_file(temp_memory_file, capsys):
    """Test clearing memory when the file exists."""
    with open(temp_memory_file, "w", encoding="utf-8") as f:
        f.write("{}")

    memory = ContextMemory(temp_memory_file)
    summary, messages = memory.clear()
    captured = capsys.readouterr()
    assert "Memory file has been reset" in captured.out
    assert summary == ""
    assert messages == []
    assert not os.path.exists(temp_memory_file)


# Test clearing memory with permission error
def test_clear_permission_error(temp_memory_file, monkeypatch, capsys):
    """Test clearing memory with a PermissionError."""
    with open(temp_memory_file, "w", encoding="utf-8") as f:
        f.write("{}")

    monkeypatch.setattr(os, "remove", MagicMock(side_effect=PermissionError("Access denied")))

    memory = ContextMemory(temp_memory_file)
    memory.rolling_summary = "Test summary"
    memory.recent_messages = [{"role": "user", "content": "Hello"}]
    summary, messages = memory.clear()
    captured = capsys.readouterr()
    assert "Permission denied when resetting memory file" in captured.out
    assert summary == "Test summary"
    assert messages == [{"role": "user", "content": "Hello"}]
    assert os.path.exists(temp_memory_file)


# Test clearing non-existent file
def test_clear_non_existent_file(temp_memory_file, capsys):
    """Test clearing memory when the file does not exist."""
    memory = ContextMemory(temp_memory_file)
    summary, messages = memory.clear()
    captured = capsys.readouterr()
    assert "No memory file to reset" in captured.out
    assert summary == ""
    assert messages == []
    assert not os.path.exists(temp_memory_file)


# Test summarization with messages
def test_summarize_with_messages(temp_memory_file, mock_openai_client, mock_config):
    """Test summarization with recent messages."""
    memory = ContextMemory(temp_memory_file)
    memory.recent_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Updated summary"))]
    mock_openai_client.chat.completions.create.return_value = mock_response

    summary, messages = memory.summarize(mock_openai_client, mock_config)
    assert summary == "Updated summary"
    assert messages == []
    assert memory.rolling_summary == "Updated summary"
    assert memory.recent_messages == []


# Test summarization with empty messages
def test_summarize_empty_messages(temp_memory_file, mock_openai_client, mock_config):
    """Test summarization with no messages."""
    memory = ContextMemory(temp_memory_file)
    summary, messages = memory.summarize(mock_openai_client, mock_config)
    assert summary == ""
    assert messages == []
    assert memory.rolling_summary == ""
    assert memory.recent_messages == []
    mock_openai_client.chat.completions.create.assert_not_called()


# Test summarization with OpenAI error
def test_summarize_openai_error(temp_memory_file, mock_openai_client, mock_config, capsys):
    """Test summarization handling OpenAIError."""
    memory = ContextMemory(temp_memory_file)
    memory.recent_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]

    mock_openai_client.chat.completions.create.side_effect = OpenAIError("API failure")

    summary, messages = memory.summarize(mock_openai_client, mock_config)
    captured = capsys.readouterr()
    assert "Summary failed: API failure" in captured.out
    assert summary == ""
    assert messages == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]


# Test check_memory_limit triggering summarization
def test_check_memory_limit_triggers_summarize(temp_memory_file, mock_openai_client, mock_config):
    """Test check_memory_limit triggers summarization when limit is exceeded."""
    memory = ContextMemory(temp_memory_file)
    # Exceed limit (memory_limit * 2 = 10)
    memory.recent_messages = [{"role": "user", "content": f"Msg {i}"} for i in range(11)]

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Summary"))]
    mock_openai_client.chat.completions.create.return_value = mock_response

    memory.check_memory_limit(mock_openai_client, mock_config)
    assert memory.rolling_summary == "Summary"
    assert memory.recent_messages == []


# Test check_memory_limit below limit
def test_check_memory_limit_below_limit(temp_memory_file, mock_openai_client, mock_config):
    """Test check_memory_limit does not trigger summarization when below limit."""
    memory = ContextMemory(temp_memory_file)
    memory.recent_messages = [{"role": "user", "content": "Msg"}]  # Below limit (10)

    memory.check_memory_limit(mock_openai_client, mock_config)
    assert memory.rolling_summary == ""
    assert len(memory.recent_messages) == 1
    mock_openai_client.chat.completions.create.assert_not_called()
