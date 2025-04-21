from unittest.mock import patch, ANY
from rich.markdown import Markdown
from blackcortex_cli.utils.formatting import print_wrapped, render_header


# Tests for print_wrapped
def test_print_wrapped_plain():
    """Test print_wrapped with plain text and default end parameter."""
    with patch("blackcortex_cli.utils.console.console.print") as mock_print:
        print_wrapped("Hello", markdown=False, end="\n")
        mock_print.assert_called_once_with("Hello", end="\n")


def test_print_wrapped_markdown():
    """Test print_wrapped with Markdown text and custom end parameter."""
    with patch("blackcortex_cli.utils.console.console.print") as mock_print:
        print_wrapped("**Bold**", markdown=True, end="")
        assert mock_print.call_count == 1
        call_args = mock_print.call_args
        assert call_args is not None
        args, kwargs = call_args
        assert len(args) == 1
        assert isinstance(args[0], Markdown)
        assert kwargs == {"end": ""}


def test_print_wrapped_custom_end():
    """Test print_wrapped with plain text and a custom end parameter."""
    with patch("blackcortex_cli.utils.console.console.print") as mock_print:
        print_wrapped("No newline", markdown=False, end=" ")
        mock_print.assert_called_once_with("No newline", end=" ")


def test_print_wrapped_empty_text():
    """Test print_wrapped with empty text."""
    with patch("blackcortex_cli.utils.console.console.print") as mock_print:
        print_wrapped("", markdown=True, end="\n")
        mock_print.assert_called_once_with(ANY, end="\n")
        assert isinstance(mock_print.call_args[0][0], Markdown)


# Tests for render_header
def test_render_header_default():
    """Test render_header with default styling."""
    result = render_header("Left", "Right")
    assert result == "[bold]Left[/bold] [dim]Right[/dim]"


def test_render_header_custom_style():
    """Test render_header with a custom style for the left text."""
    result = render_header("Left", "Right", style_left="red")
    assert result == "[red]Left[/red] [dim]Right[/dim]"


def test_render_header_empty_left():
    """Test render_header with an empty left string."""
    result = render_header("", "Right")
    assert result == "[bold][/bold] [dim]Right[/dim]"


def test_render_header_empty_right():
    """Test render_header with an empty right string."""
    result = render_header("Left", "")
    assert result == "[bold]Left[/bold] [dim][/dim]"


def test_render_header_special_characters():
    """Test render_header with special characters in inputs."""
    result = render_header("[Special]", "Chars]")
    assert result == "[bold][Special][/bold] [dim]Chars][/dim]"
