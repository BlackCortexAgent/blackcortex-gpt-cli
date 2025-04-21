import io
from unittest.mock import patch
import pytest
from blackcortex_cli.utils.metadata import read_metadata, read_version, read_name


# Tests for read_metadata
def test_read_metadata_normal():
    """Test read_metadata with a normal [project] section."""
    toml_content = b'[project]\nname = "myproject"\nversion = "1.0.0"'
    with patch("pathlib.Path.open", return_value=io.BytesIO(toml_content)):
        metadata = read_metadata()
        assert metadata == {"name": "myproject", "version": "1.0.0"}


def test_read_metadata_missing_keys():
    """Test read_metadata when some keys are missing in [project]."""
    toml_content = b'[project]\nname = "myproject"'
    with patch("pathlib.Path.open", return_value=io.BytesIO(toml_content)):
        metadata = read_metadata()
        assert metadata == {"name": "myproject"}


def test_read_metadata_no_project():
    """Test read_metadata when [project] section is missing."""
    toml_content = b'[tool]\nsomething = "else"'
    with patch("pathlib.Path.open", return_value=io.BytesIO(toml_content)):
        metadata = read_metadata()
        assert metadata == {}


def test_read_metadata_file_not_found():
    """Test read_metadata when pyproject.toml does not exist."""
    with patch("pathlib.Path.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            read_metadata()


# Tests for read_version
def test_read_version_normal():
    """Test read_version when version is present."""
    with patch("blackcortex_cli.utils.metadata.read_metadata", return_value={"version": "1.0.0"}):
        assert read_version() == "1.0.0"


def test_read_version_missing():
    """Test read_version when version is missing."""
    with patch("blackcortex_cli.utils.metadata.read_metadata", return_value={"name": "myproject"}):
        assert read_version() == "0.0.0"


def test_read_version_no_project():
    """Test read_version when [project] section is missing."""
    with patch("blackcortex_cli.utils.metadata.read_metadata", return_value={}):
        assert read_version() == "0.0.0"


# Tests for read_name
def test_read_name_normal():
    """Test read_name when name is present."""
    with patch("blackcortex_cli.utils.metadata.read_metadata", return_value={"name": "myproject"}):
        assert read_name() == "myproject"


def test_read_name_missing():
    """Test read_name when name is missing."""
    with patch("blackcortex_cli.utils.metadata.read_metadata", return_value={"version": "1.0.0"}):
        assert read_name() == "unknown"


def test_read_name_no_project():
    """Test read_name when [project] section is missing."""
    with patch("blackcortex_cli.utils.metadata.read_metadata", return_value={}):
        assert read_name() == "unknown"
