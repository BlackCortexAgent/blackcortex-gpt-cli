# blackcortex_cli/utils/metadata.py

"""
Utilities for reading project metadata from pyproject.toml.
"""

import tomllib
from pathlib import Path


def read_metadata() -> dict:
    """
    Load the [project] metadata section from pyproject.toml.

    Returns:
        A dictionary containing the project's metadata.
    """
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    return data.get("project", {})


def read_version() -> str:
    """
    Return the project's version string from pyproject.toml.

    Returns:
        The version as a string, or "0.0.0" if not found.
    """
    return read_metadata().get("version", "0.0.0")


def read_name() -> str:
    """
    Return the project's name from pyproject.toml.

    Returns:
        The name as a string, or "unknown" if not found.
    """
    return read_metadata().get("name", "unknown")
