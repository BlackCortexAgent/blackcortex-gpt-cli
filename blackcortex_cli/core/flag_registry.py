# blackcortex_cli/core/flag_registry.py

"""
Flag registry for managing command-line flags in the BlackCortex GPT CLI.

This module provides the `Flag` dataclass for defining CLI flags and the
`FlagRegistry` class for registering, categorizing, and applying flags to
an argparse parser. It also supports execution of optional pre- and post-
handlers based on flag presence and priority.
"""

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from blackcortex_cli.core.context import Context


@dataclass
class Flag:
    """
    Dataclass representing a command-line flag.

    Attributes:
        name (str): The name of the flag (used internally).
        short (str | None): Short flag name (e.g., "-s").
        long (str): Long flag name (e.g., "--stream").
        help (str): Help text for the flag.
        action (str): Argparse action (e.g., "store_true", "store").
        value_type (type | None): Type of the flag value (e.g., str, int).
        default (Any): Default value for the flag.
        nargs (str | None): Number of arguments (e.g., "+", "*").
        const (str | None): Constant value for certain actions.
        metavar (str | None): Placeholder name for the argument in help text.
        category (str): Category for grouping in help output.
        pre_handler (Callable | None): Handler to run before main processing.
        post_handler (Callable | None): Handler to run after main processing.
        dest (str | None): Namespace attribute name for the flag value.
        priority (int): Priority for handler execution order.
        exit_after (bool): Whether to exit after the pre-handler.
        choices (list[str] | None): Allowed values for the flag (for action="store").
    """

    name: str
    short: str | None
    long: str
    help: str
    action: str = "store_true"
    value_type: type | None = None
    default: Any = argparse.SUPPRESS
    nargs: str | None = None
    const: str | None = None
    metavar: str | None = None
    category: str = "General"
    pre_handler: Callable[[argparse.Namespace, Context], None] | None = None
    post_handler: Callable[[argparse.Namespace, Context], None] | None = None
    dest: str | None = None
    priority: int = 0
    exit_after: bool = False
    choices: list[str] | None = None


class FlagRegistry:
    """Manages registration and application of command-line flags."""

    def __init__(self):
        """Initialize an empty flag registry."""
        self._flags: list[Flag] = []

    def register(self, flag: Flag) -> None:
        """
        Register a flag in the registry.

        Args:
            flag (Flag): The flag to register.

        Raises:
            ValueError: If the long or short flag name is already registered.
        """
        if any(f.long == flag.long for f in self._flags):
            raise ValueError(f"Flag with long={flag.long} already registered")
        if flag.short and any(f.short == flag.short for f in self._flags if f.short):
            raise ValueError(f"Flag with short={flag.short} already registered")
        self._flags.append(flag)

    def apply_to_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        Apply registered flags to an ArgumentParser.

        Groups flags by category and adds them with the appropriate argparse settings.

        Args:
            parser (argparse.ArgumentParser): The parser to configure.
        """
        categories: dict[str, argparse._ArgumentGroup] = {}
        for flag in self._flags:
            group = categories.setdefault(flag.category, parser.add_argument_group(flag.category))
            kwargs = {
                "help": flag.help,
                "action": flag.action,
            }
            if flag.value_type is not None:
                kwargs["type"] = flag.value_type
            if flag.default is not argparse.SUPPRESS:
                kwargs["default"] = flag.default
            if flag.nargs is not None:
                kwargs["nargs"] = flag.nargs
            if flag.const is not None:
                kwargs["const"] = flag.const
            if flag.metavar is not None:
                kwargs["metavar"] = flag.metavar
            if flag.choices is not None:
                kwargs["choices"] = flag.choices
            kwargs["dest"] = flag.dest or flag.long.replace("-", "_")
            args = [f"--{flag.long}"]
            if flag.short:
                args.insert(0, f"-{flag.short}")
            group.add_argument(*args, **kwargs)

    def get_pre_handlers(
        self, args: argparse.Namespace
    ) -> list[tuple[Callable[[argparse.Namespace, Context], None], bool]]:
        """
        Get pre-handlers for flags that were provided.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.

        Returns:
            List of tuples containing the handler and exit_after flag, sorted by priority.
        """
        items = []
        for flag in self._flags:
            if not flag.pre_handler:
                continue
            dest = flag.dest or flag.long.replace("-", "_")
            value = getattr(args, dest, None)
            if (flag.action == "store_true" and value is True) or (
                flag.action != "store_true" and value is not None
            ):
                items.append((flag.priority, flag.pre_handler, flag.exit_after))
        return [
            (handler, exit_after)
            for _, handler, exit_after in sorted(items, key=lambda i: i[0], reverse=True)
        ]

    def get_post_handlers(
        self, args: argparse.Namespace
    ) -> list[Callable[[argparse.Namespace, Context], None]]:
        """
        Get post-handlers for flags that were provided.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.

        Returns:
            List of post-handlers to execute.
        """
        handlers = []
        for flag in self._flags:
            if not flag.post_handler:
                continue
            dest = flag.dest or flag.long.replace("-", "_")
            value = getattr(args, dest, None)
            if (flag.action == "store_true" and value is True) or (
                flag.action != "store_true" and value is not None
            ):
                handlers.append(flag.post_handler)
        return handlers


# Global instance of FlagRegistry
flag_registry = FlagRegistry()
