# blackcortex_cli/utils/formatting.py

from rich.console import Console
from rich.text import Text

console = Console()

MAX_WIDTH = 100


def render_header(left: str, right: str, style_left="bold", style_right="dim") -> Text:
    """
    Renders a left-right aligned header with consistent width for CLI output.
    """
    space = MAX_WIDTH - len(left) - len(right) - 2
    spacer = " " * max(space, 1)
    return Text.assemble((left, style_left), spacer, (right, style_right))


def print_wrapped(text, markdown=True):
    """
    Prints text wrapped to MAX_WIDTH. Handles rich.Text and Markdown input.
    """
    from rich.markdown import Markdown
    from rich.text import Text

    if isinstance(text, str):
        text = Markdown(text) if markdown else Text(text)

    if isinstance(text, Text):
        for line in text.wrap(console, width=MAX_WIDTH):
            console.print(line)
    else:
        console.print(text)
