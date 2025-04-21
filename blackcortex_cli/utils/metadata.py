# blackcortex_cli/utils/metadata.py

"""
Utilities for reading project metadata, primarily from installed package metadata,
with a fallback to pyproject.toml during development.
"""

import tomllib
from importlib.metadata import PackageNotFoundError, metadata
from pathlib import Path

toml_load = tomllib.load


def read_metadata() -> dict:
    """
    Load the project metadata, preferring installed package metadata over pyproject.toml.

    Returns:
        A dictionary containing the project's metadata.
    """
    try:
        # Try to get metadata from the installed package
        package_metadata = metadata("blackcortex-gpt-cli")
        return {
            "name": package_metadata["Name"],
            "version": package_metadata["Version"],
            # Add other metadata fields as needed
        }
    except PackageNotFoundError:
        # Fallback to reading pyproject.toml during development
        if toml_load is None:
            return {}
        try:
            pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
            with pyproject_path.open("rb") as f:
                data = toml_load(f)
            return data.get("project", {})
        except (FileNotFoundError, ValueError):
            return {}


def read_version() -> str:
    """
    Return the project's version string, preferring installed package metadata.

    Returns:
        The version as a string, or "0.0.0" if not found.
    """
    return read_metadata().get("version", "0.0.0")


def read_name() -> str:
    """
    Return the project's name, preferring installed package metadata.

    Returns:
        The name as a string, or "unknown" if not found.
    """
    return read_metadata().get("name", "unknown")
