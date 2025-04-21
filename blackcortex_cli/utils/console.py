# blackcortex_cli/utils/console.py

"""
Provides a shared Rich Console instance for consistent styled output across the CLI.
"""

from rich.console import Console

# Singleton Console instance
console = Console()
