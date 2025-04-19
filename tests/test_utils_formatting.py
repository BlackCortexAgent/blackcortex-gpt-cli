"""
Unit tests for formatting utilities in blackcortex_cli.utils.formatting.

Tests include rendering headers and printing wrapped content.
"""

from unittest.mock import patch

from rich.markdown import Markdown
from rich.text import Text

from blackcortex_cli.utils.formatting import MAX_WIDTH, print_wrapped, render_header


def test_render_header_alignment_and_styles():
    """
    Test render_header creates properly aligned text with correct styles.
    """
    left = "GPT CLI"
    right = "v1.2.3"
    result = render_header(left, right)

    assert isinstance(result, Text)
    assert left in result.plain
    assert right in result.plain
    # Check left and right appear only once
    assert result.plain.count(left) == 1
    assert result.plain.count(right) == 1
    # Check total width doesn't exceed MAX_WIDTH
    assert len(result.plain) <= MAX_WIDTH


@patch("blackcortex_cli.utils.formatting.console.print")
def test_print_wrapped_plain_text(mock_print):
    """
    Test print_wrapped prints plain text properly wrapped without markdown.
    """
    text = (
        "This is a test line that should be printed with wrapping but without markdown formatting."
    )
    print_wrapped(text, markdown=False)

    # Ensure console.print was called with lines of rich.Text
    assert mock_print.call_count >= 1
    for call in mock_print.call_args_list:
        (arg,), _ = call
        assert isinstance(arg, Text)


@patch("blackcortex_cli.utils.formatting.console.print")
def test_print_wrapped_markdown(mock_print):
    """
    Test print_wrapped interprets markdown if enabled.
    """
    text = "# Title\n\nSome *markdown* content."
    print_wrapped(text, markdown=True)

    # The fallback call if wrapping fails or for single-line markdown
    assert mock_print.call_count >= 1
    # It could be Markdown or Text depending on rendering; ensure at least not raw string
    for call in mock_print.call_args_list:
        (arg,), _ = call
        assert not isinstance(arg, str)


@patch("blackcortex_cli.utils.formatting.console.print")
def test_print_wrapped_renders_markdown_block(mock_print):
    """Ensure print_wrapped handles a Markdown object directly (non-str)"""
    md = Markdown("**Bold** and _italic_")
    print_wrapped(md)
    assert mock_print.called
