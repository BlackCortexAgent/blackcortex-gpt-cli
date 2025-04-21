import io
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

import pytest

from blackcortex_cli.utils.metadata import read_metadata, read_name, read_version


# Tests for read_metadata
def test_read_metadata_from_package_metadata():
    """Test read_metadata using importlib.metadata."""
    mock_metadata = {"Name": "blackcortex-gpt-cli", "Version": "1.2.2"}
    with patch("blackcortex_cli.utils.metadata.metadata", return_value=mock_metadata):
        result = read_metadata()
        assert result == {"name": "blackcortex-gpt-cli", "version": "1.2.2"}


def test_read_metadata_from_pyproject_toml():
    """Test read_metadata fallback to pyproject.toml."""
    toml_content = b'[project]\nname = "blackcortex-gpt-cli"\nversion = "1.2.2"'
    with (
        patch("pathlib.Path.open", return_value=io.BytesIO(toml_content)),
        patch("blackcortex_cli.utils.metadata.metadata", side_effect=PackageNotFoundError),
    ):
        result = read_metadata()
        assert result == {"name": "blackcortex-gpt-cli", "version": "1.2.2"}


def test_read_metadata_missing_project_section():
    """Test read_metadata when pyproject.toml has no [project] section."""
    toml_content = b'[tool]\nsomething = "else"'
    with (
        patch("pathlib.Path.open", return_value=io.BytesIO(toml_content)),
        patch("blackcortex_cli.utils.metadata.metadata", side_effect=PackageNotFoundError),
    ):
        result = read_metadata()
        assert result == {}


def test_read_metadata_file_not_found():
    """Test read_metadata when pyproject.toml is missing."""
    with (
        patch("pathlib.Path.open", side_effect=FileNotFoundError),
        patch("blackcortex_cli.utils.metadata.metadata", side_effect=PackageNotFoundError),
    ):
        result = read_metadata()
        assert result == {}


def test_read_metadata_invalid_toml():
    """Test read_metadata when pyproject.toml is invalid."""
    toml_content = b"invalid = toml\nsyntax"
    with (
        patch("pathlib.Path.open", return_value=io.BytesIO(toml_content)),
        patch("blackcortex_cli.utils.metadata.metadata", side_effect=PackageNotFoundError),
    ):
        result = read_metadata()
        assert result == {}


# Tests for read_version
def test_read_version_from_metadata():
    """Test read_version using package metadata."""
    with patch(
        "blackcortex_cli.utils.metadata.read_metadata",
        return_value={"name": "blackcortex-gpt-cli", "version": "1.2.2"},
    ):
        result = read_version()
        assert result == "1.2.2"


def test_read_version_missing_version():
    """Test read_version when version is missing."""
    with patch("blackcortex_cli.utils.metadata.read_metadata", return_value={"name": "myproject"}):
        result = read_version()
        assert result == "0.0.0"


def test_read_version_empty_metadata():
    """Test read_version when metadata is empty."""
    with patch("blackcortex_cli.utils.metadata.read_metadata", return_value={}):
        result = read_version()
        assert result == "0.0.0"


# Tests for read_name
def test_read_name_from_metadata():
    """Test read_name using package metadata."""
    with patch(
        "blackcortex_cli.utils.metadata.read_metadata",
        return_value={"name": "blackcortex-gpt-cli", "version": "1.2.2"},
    ):
        result = read_name()
        assert result == "blackcortex-gpt-cli"


def test_read_name_missing_name():
    """Test read_name when name is missing."""
    with patch("blackcortex_cli.utils.metadata.read_metadata", return_value={"version": "1.2.2"}):
        result = read_name()
        assert result == "unknown"


def test_read_name_empty_metadata():
    """Test read_name when metadata is empty."""
    with patch("blackcortex_cli.utils.metadata.read_metadata", return_value={}):
        result = read_name()
        assert result == "unknown"
