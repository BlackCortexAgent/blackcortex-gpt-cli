"""
Utility functions for formatted terminal output using Rich.
Provides Markdown rendering, wrapped printing, and styled headers.
"""

from rich.markdown import Markdown

from blackcortex_cli.utils.console import console


def print_wrapped(text: str, markdown: bool = False, end: str = "\n") -> None:
    """
    Print text with wrapping, optionally rendering as Markdown.

    Args:
        text: The text to print.
        markdown: Whether to render the text as Markdown.
        end: String to append after printing (default: newline).
    """
    if markdown:
        console.print(Markdown(text), end=end)
    else:
        console.print(text, end=end)


def render_header(left: str, right: str, style_left: str = "bold") -> str:
    """
    Render a styled header with left and right-aligned text.

    Args:
        left: The primary label text.
        right: The secondary dimmed text.
        style_left: Rich style to apply to the left text (default: bold).

    Returns:
        A Rich-formatted string combining both styled parts.
    """
    return f"[{style_left}]{left}[/{style_left}] [dim]{right}[/dim]"
