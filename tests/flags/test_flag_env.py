import os
import subprocess
from argparse import Namespace
from unittest.mock import Mock, mock_open, patch

import pytest

from blackcortex_cli.config.config import Config
from blackcortex_cli.core.context import Context
from blackcortex_cli.core.log_manager import LogManager
from blackcortex_cli.flags.flag_env import check_file_modified, handle_env, set_file_permissions


# Fixture to prevent .gpt-cli directory creation
@pytest.fixture(autouse=True)
def prevent_gpt_cli_dir(monkeypatch):
    """Mock file system operations to prevent .gpt-cli directory creation."""
    monkeypatch.setattr(os, "makedirs", Mock())
    monkeypatch.setattr(os, "chmod", Mock(side_effect=OSError("Mocked chmod")))
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
    config.api_key = "test_key"  # Required for some tests
    log_manager = LogManager(config.log_file)
    log_manager.logger = Mock(spec=["info", "error", "debug", "addHandler"])
    log_manager._init_file_handler = Mock()
    return Context(config, log_manager)


# Fixture for a temporary .env path
@pytest.fixture
def env_path(tmp_path):
    """Return a temporary .env path."""
    return str(tmp_path / ".gpt-cli" / ".env")


def test_set_file_permissions_success():
    """Test setting file permissions successfully."""
    log_manager = Mock()
    with patch("os.chmod") as mock_chmod:
        set_file_permissions("/fake/path", log_manager, 0o660)
        mock_chmod.assert_called_once_with("/fake/path", 0o660)
        log_manager.log_info.assert_called_once_with("Set permissions on /fake/path to 0o660")
        log_manager.log_error.assert_not_called()


def test_set_file_permissions_oserror(capsys):
    """Test handling OSError in set_file_permissions."""
    log_manager = Mock()
    with patch("os.chmod", side_effect=OSError("Permission denied")):
        set_file_permissions("/fake/path", log_manager, 0o660)
        log_manager.log_error.assert_called_once_with(
            "Failed to set permissions on /fake/path: Permission denied"
        )
        captured = capsys.readouterr()
        assert "Warning: Could not set permissions on /fake/path: Permission denied" in captured.out


def test_check_file_modified_success():
    """Test detecting file modification successfully."""
    log_manager = Mock()
    with patch("os.stat") as mock_stat:
        mock_stat.return_value.st_mtime = 12346
        result = check_file_modified("/fake/path", 12345, log_manager)
        assert result is True
        log_manager.log_info.assert_called_once_with("/fake/path was modified")
        log_manager.log_error.assert_not_called()


def test_check_file_modified_no_change():
    """Test detecting no file modification."""
    log_manager = Mock()
    with patch("os.stat") as mock_stat:
        mock_stat.return_value.st_mtime = 12345
        result = check_file_modified("/fake/path", 12345, log_manager)
        assert result is False
        log_manager.log_info.assert_called_once_with("/fake/path was not modified")
        log_manager.log_error.assert_not_called()


def test_check_file_modified_oserror():
    """Test handling OSError in check_file_modified."""
    log_manager = Mock()
    with patch("os.stat", side_effect=OSError("No such file")):
        result = check_file_modified("/fake/path", 12345, log_manager)
        assert result is False
        log_manager.log_error.assert_called_once_with(
            "Failed to check modification time of /fake/path: No such file"
        )
        log_manager.log_info.assert_not_called()


def test_handle_env_success_new_file(monkeypatch, context, env_path, capsys):
    """Test handle_env creating a new .env file and detecting modification."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_env.get_env_path", lambda: env_path)

    def stat_side_effect(*args, **kwargs):
        call_count = getattr(stat_side_effect, "call_count", 0) + 1
        stat_side_effect.call_count = call_count
        return Mock(st_mtime=12345 if call_count == 1 else 12346)

    with (
        patch("os.makedirs") as mock_makedirs,
        patch("os.path.exists", return_value=False),
        patch("os.path.isfile", return_value=True),
        patch("builtins.open", mock_open()),
        patch("os.chmod") as mock_chmod,
        patch("os.stat") as mock_stat,
        patch("subprocess.run") as mock_run,
        patch("os.getenv", return_value="nano"),
    ):
        mock_stat.side_effect = stat_side_effect
        mock_run.return_value = None
        with pytest.raises(SystemExit) as exc:
            handle_env(Namespace(), context)
        assert exc.value.code == 0
        mock_makedirs.assert_called_once_with(os.path.dirname(env_path), mode=0o770, exist_ok=True)
        mock_chmod.assert_called()
        context.log_manager.logger.info.assert_any_call(f"Created new .env file at {env_path}")
        context.log_manager.logger.info.assert_any_call(f"Opening {env_path} with editor 'nano'")
        context.log_manager.logger.info.assert_any_call(f"{env_path} was modified")
        captured = capsys.readouterr()
        assert "[+] .env file updated." in captured.out


def test_handle_env_success_existing_file_no_change(monkeypatch, context, env_path, capsys):
    """Test handle_env with existing file and no modification."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_env.get_env_path", lambda: env_path)

    def stat_side_effect(*args, **kwargs):
        return Mock(st_mtime=12345)

    with (
        patch("os.makedirs"),
        patch("os.path.exists", return_value=True),
        patch("os.path.isfile", return_value=True),
        patch("os.chmod"),
        patch("os.stat") as mock_stat,
        patch("subprocess.run") as mock_run,
        patch("os.getenv", return_value="nano"),
    ):
        mock_stat.side_effect = stat_side_effect
        mock_run.return_value = None
        with pytest.raises(SystemExit) as exc:
            handle_env(Namespace(), context)
        assert exc.value.code == 0
        context.log_manager.logger.info.assert_any_call(f"Opening {env_path} with editor 'nano'")
        context.log_manager.logger.info.assert_any_call(f"{env_path} was not modified")
        captured = capsys.readouterr()
        assert "[-] No changes made to .env file." in captured.out


def test_handle_env_file_creation_oserror(monkeypatch, context, env_path, capsys):
    """Test handle_env with OSError during file creation."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_env.get_env_path", lambda: env_path)
    with (
        patch("os.makedirs", side_effect=OSError("Permission denied")),
    ):
        with pytest.raises(SystemExit) as exc:
            handle_env(Namespace(), context)
        assert exc.value.code == 1
        context.log_manager.logger.error.assert_called_once_with(
            f"Failed to prepare .env file at {env_path}: Permission denied"
        )
        captured = capsys.readouterr()
        assert " Failed to prepare .env file: Permission denied" in captured.out


def test_handle_env_editor_failure(monkeypatch, context, env_path, capsys):
    """Test handle_env with editor failure (subprocess error)."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_env.get_env_path", lambda: env_path)
    with (
        patch("os.makedirs"),
        patch("os.path.exists", return_value=True),
        patch("os.path.isfile", return_value=True),
        patch("os.chmod"),
        patch("os.stat", return_value=Mock(st_mtime=12345)),
        patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["nano", env_path])),
        patch("os.getenv", return_value="nano"),
    ):
        with pytest.raises(SystemExit) as exc:
            handle_env(Namespace(), context)
        assert exc.value.code == 1
        context.log_manager.logger.error.assert_called_once_with(
            f"Editor failed for {env_path}: exited with code 1"
        )
        captured = capsys.readouterr()
        assert " Editor failed: Exited with code 1" in captured.out


def test_handle_env_editor_oserror(monkeypatch, context, env_path, capsys):
    """Test handle_env with OSError during editor invocation."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_env.get_env_path", lambda: env_path)
    with (
        patch("os.makedirs"),
        patch("os.path.exists", return_value=True),
        patch("os.path.isfile", return_value=True),
        patch("os.chmod"),
        patch("os.stat", return_value=Mock(st_mtime=12345)),
        patch("subprocess.run", side_effect=OSError("No such file or directory")),
        patch("os.getenv", return_value="invalid_editor"),
    ):
        with pytest.raises(SystemExit) as exc:
            handle_env(Namespace(), context)
        assert exc.value.code == 1
        context.log_manager.logger.error.assert_called_once_with(
            f"Failed to open editor for {env_path}: No such file or directory"
        )
        captured = capsys.readouterr()
        assert " Failed to open editor: No such file or directory" in captured.out
        assert "Try setting the EDITOR environment variable or installing 'nano'." in captured.out


def test_handle_env_permission_warning(monkeypatch, context, env_path, capsys):
    """Test handle_env with permission warning during chmod."""
    monkeypatch.setattr("blackcortex_cli.flags.flag_env.get_env_path", lambda: env_path)

    def stat_side_effect(*args, **kwargs):
        call_count = getattr(stat_side_effect, "call_count", 0) + 1
        stat_side_effect.call_count = call_count
        return Mock(st_mtime=12345 if call_count == 1 else 12346)

    with (
        patch("os.makedirs"),
        patch("os.path.exists", return_value=True),
        patch("os.path.isfile", return_value=True),
        patch("os.chmod", side_effect=OSError("Permission denied")),
        patch("os.stat") as mock_stat,
        patch("subprocess.run"),
        patch("os.getenv", return_value="nano"),
    ):
        mock_stat.side_effect = stat_side_effect
        with pytest.raises(SystemExit) as exc:
            handle_env(Namespace(), context)
        assert exc.value.code == 0
        context.log_manager.logger.error.assert_called_with(
            f"Failed to set permissions on {env_path}: Permission denied"
        )
        captured = capsys.readouterr()
        assert "Warning: Could not set permissions on" in captured.out
        assert "[+] .env file updated." in captured.out
