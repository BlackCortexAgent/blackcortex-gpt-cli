import argparse
from unittest.mock import MagicMock

import pytest

from blackcortex_cli.core.flag_registry import Flag, FlagRegistry


# Fixture for a mock Context
@pytest.fixture
def mock_context():
    """Provide a mocked Context instance."""
    return MagicMock()


# Fixture for a mock handler function
@pytest.fixture
def mock_handler():
    """Provide a mocked handler function."""
    return MagicMock()


# Fixture for a sample Flag
@pytest.fixture
def sample_flag(mock_handler):
    """Provide a sample Flag instance."""
    return Flag(
        name="stream",
        short="s",
        long="stream",
        help="Enable streaming mode",
        action="store_true",
        category="General",
        pre_handler=mock_handler,
        post_handler=mock_handler,
        priority=10,
        exit_after=False,
    )


# Fixture for a sample Flag with store action
@pytest.fixture
def sample_store_flag(mock_handler):
    """Provide a sample Flag instance with store action."""
    return Flag(
        name="model",
        short="m",
        long="model",
        help="Specify the model",
        action="store",
        value_type=str,
        default="gpt-4o",
        choices=["gpt-4o", "gpt-3.5-turbo"],
        category="Model",
        pre_handler=mock_handler,
        post_handler=mock_handler,
        priority=5,
    )


# Fixture for a sample Flag with custom dest
@pytest.fixture
def sample_custom_dest_flag(mock_handler):
    """Provide a sample Flag instance with a custom dest."""
    return Flag(
        name="custom",
        short="c",
        long="custom-flag",
        help="Custom flag with dest",
        action="store",
        value_type=str,
        dest="custom_dest",
        category="Custom",
        pre_handler=mock_handler,
        post_handler=mock_handler,
        priority=7,
    )


# Fixture for a sample Flag with no choices
@pytest.fixture
def sample_no_choices_flag(mock_handler):
    """Provide a sample Flag instance with choices=None."""
    return Flag(
        name="value",
        short="v",
        long="value",
        help="Specify a value",
        action="store",
        value_type=str,
        choices=None,  # Explicitly None
        category="Options",
        pre_handler=mock_handler,
        post_handler=mock_handler,
        priority=3,
    )


# Fixture for a sample Flag with append action
@pytest.fixture
def sample_append_flag(mock_handler):
    """Provide a sample Flag instance with append action."""
    return Flag(
        name="append",
        short="a",
        long="append",
        help="Append values",
        action="append",
        value_type=str,
        category="Options",
        pre_handler=mock_handler,
        post_handler=mock_handler,
        priority=2,
    )


# Test FlagRegistry initialization
def test_flag_registry_init():
    """Test FlagRegistry initializes with an empty flag list."""
    registry = FlagRegistry()
    assert registry._flags == []


# Test registering a valid flag
def test_register_valid_flag(sample_flag):
    """Test registering a valid flag."""
    registry = FlagRegistry()
    registry.register(sample_flag)
    assert len(registry._flags) == 1
    assert registry._flags[0] == sample_flag


# Test registering duplicate long flag
def test_register_duplicate_long_flag(sample_flag):
    """Test registering a flag with a duplicate long name raises ValueError."""
    registry = FlagRegistry()
    registry.register(sample_flag)
    duplicate_flag = Flag(
        name="stream2", short="t", long="stream", help="Another stream flag", action="store_true"
    )
    with pytest.raises(ValueError, match="Flag with long=stream already registered"):
        registry.register(duplicate_flag)


# Test registering duplicate short flag
def test_register_duplicate_short_flag(sample_flag):
    """Test registering a flag with a duplicate short name raises ValueError."""
    registry = FlagRegistry()
    registry.register(sample_flag)
    duplicate_flag = Flag(
        name="stream2", short="s", long="stream2", help="Another stream flag", action="store_true"
    )
    with pytest.raises(ValueError, match="Flag with short=s already registered"):
        registry.register(duplicate_flag)


# Test applying flags to parser
def test_apply_to_parser(sample_flag, sample_store_flag):
    """Test applying flags to an ArgumentParser with correct grouping."""
    registry = FlagRegistry()
    registry.register(sample_flag)
    registry.register(sample_store_flag)

    parser = MagicMock(spec=argparse.ArgumentParser)
    mock_group_general = MagicMock()
    mock_group_model = MagicMock()
    parser.add_argument_group.side_effect = [mock_group_general, mock_group_model]

    registry.apply_to_parser(parser)

    parser.add_argument_group.assert_any_call("General")
    parser.add_argument_group.assert_any_call("Model")
    mock_group_general.add_argument.assert_called_with(
        "-s", "--stream", help="Enable streaming mode", action="store_true", dest="stream"
    )
    mock_group_model.add_argument.assert_called_with(
        "-m",
        "--model",
        help="Specify the model",
        action="store",
        type=str,
        default="gpt-4o",
        choices=["gpt-4o", "gpt-3.5-turbo"],
        dest="model",
    )


# Test applying flag with no choices
def test_apply_to_parser_no_choices(sample_no_choices_flag):
    """Test applying a flag with choices=None to the parser."""
    registry = FlagRegistry()
    registry.register(sample_no_choices_flag)

    parser = MagicMock(spec=argparse.ArgumentParser)
    mock_group = MagicMock()
    parser.add_argument_group.return_value = mock_group

    registry.apply_to_parser(parser)

    mock_group.add_argument.assert_called_with(
        "-v", "--value", help="Specify a value", action="store", type=str, dest="value"
    )
    # Verify choices is not included in kwargs
    assert "choices" not in mock_group.add_argument.call_args[1]


# Test applying flag with custom dest
def test_apply_to_parser_custom_dest(sample_custom_dest_flag):
    """Test applying a flag with a custom dest to the parser."""
    registry = FlagRegistry()
    registry.register(sample_custom_dest_flag)

    parser = MagicMock(spec=argparse.ArgumentParser)
    mock_group = MagicMock()
    parser.add_argument_group.return_value = mock_group

    registry.apply_to_parser(parser)

    mock_group.add_argument.assert_called_with(
        "-c",
        "--custom-flag",
        help="Custom flag with dest",
        action="store",
        type=str,
        dest="custom_dest",
    )
    # Verify dest is custom_dest, not derived from long
    assert mock_group.add_argument.call_args[1]["dest"] == "custom_dest"


# Test get_pre_handlers with provided flags
def test_get_pre_handlers_provided_flags(sample_flag, sample_store_flag, mock_context):
    """Test retrieving pre-handlers for provided flags, sorted by priority."""
    registry = FlagRegistry()
    registry.register(sample_flag)  # priority=10
    registry.register(sample_store_flag)  # priority=5

    args = argparse.Namespace(stream=True, model="gpt-4o")

    handlers = registry.get_pre_handlers(args)
    assert len(handlers) == 2
    assert handlers[0][0] == sample_flag.pre_handler  # Higher priority (10) first
    assert handlers[0][1] == False  # exit_after
    assert handlers[1][0] == sample_store_flag.pre_handler  # Lower priority (5)
    assert handlers[1][1] == False  # exit_after


# Test get_pre_handlers with unprovided flags
def test_get_pre_handlers_unprovided_flags(sample_flag, sample_store_flag, mock_context):
    """Test retrieving pre-handlers when flags are not provided."""
    registry = FlagRegistry()
    registry.register(sample_flag)
    registry.register(sample_store_flag)

    args = argparse.Namespace(stream=False, model=None)

    handlers = registry.get_pre_handlers(args)
    assert handlers == []


# Test get_pre_handlers with custom dest
def test_get_pre_handlers_custom_dest(sample_custom_dest_flag, mock_context):
    """Test retrieving pre-handlers with a custom dest."""
    registry = FlagRegistry()
    registry.register(sample_custom_dest_flag)

    args = argparse.Namespace(custom_dest="test_value")

    handlers = registry.get_pre_handlers(args)
    assert len(handlers) == 1
    assert handlers[0][0] == sample_custom_dest_flag.pre_handler
    assert handlers[0][1] == False


# Test get_pre_handlers edge cases
def test_get_pre_handlers_edge_cases(
    sample_flag, sample_store_flag, sample_append_flag, mock_context
):
    """Test get_pre_handlers with edge cases for store_true, store, and append actions."""
    registry = FlagRegistry()
    registry.register(sample_flag)  # store_true
    registry.register(sample_store_flag)  # store
    registry.register(sample_append_flag)  # append

    # Case 1: store_true=False, store=None, append=None
    args = argparse.Namespace(stream=False, model=None, append=None)
    handlers = registry.get_pre_handlers(args)
    assert handlers == []

    # Case 2: store_true=False, store=value, append=None
    args = argparse.Namespace(stream=False, model="gpt-4o", append=None)
    handlers = registry.get_pre_handlers(args)
    assert len(handlers) == 1
    assert handlers[0][0] == sample_store_flag.pre_handler

    # Case 3: store_true=True, store=None, append=None
    args = argparse.Namespace(stream=True, model=None, append=None)
    handlers = registry.get_pre_handlers(args)
    assert len(handlers) == 1
    assert handlers[0][0] == sample_flag.pre_handler

    # Case 4: store_true=False, store=None, append=value
    args = argparse.Namespace(stream=False, model=None, append=["value"])
    handlers = registry.get_pre_handlers(args)
    assert len(handlers) == 1
    assert handlers[0][0] == sample_append_flag.pre_handler


# Test get_post_handlers with provided flags
def test_get_post_handlers_provided_flags(sample_flag, sample_store_flag, mock_context):
    """Test retrieving post-handlers for provided flags."""
    registry = FlagRegistry()
    registry.register(sample_flag)
    registry.register(sample_store_flag)

    args = argparse.Namespace(stream=True, model="gpt-4o")

    handlers = registry.get_post_handlers(args)
    assert len(handlers) == 2
    assert sample_flag.post_handler in handlers
    assert sample_store_flag.post_handler in handlers


# Test get_post_handlers with unprovided flags
def test_get_post_handlers_unprovided_flags(sample_flag, sample_store_flag, mock_context):
    """Test retrieving post-handlers when flags are not provided."""
    registry = FlagRegistry()
    registry.register(sample_flag)
    registry.register(sample_store_flag)

    args = argparse.Namespace(stream=False, model=None)

    handlers = registry.get_post_handlers(args)
    assert handlers == []


# Test flag with None handlers
def test_flag_none_handlers():
    """Test registering a flag with no handlers."""
    flag = Flag(
        name="nohandler",
        short="n",
        long="nohandler",
        help="Flag with no handlers",
        action="store_true",
    )
    registry = FlagRegistry()
    registry.register(flag)

    args = argparse.Namespace(nohandler=True)
    pre_handlers = registry.get_pre_handlers(args)
    post_handlers = registry.get_post_handlers(args)
    assert pre_handlers == []
    assert post_handlers == []


# Test flag with choices and nargs
def test_flag_with_choices_and_nargs():
    """Test applying a flag with choices and nargs to the parser."""
    flag = Flag(
        name="values",
        short="v",
        long="values",
        help="Specify multiple values",
        action="store",
        value_type=str,
        nargs="+",
        choices=["a", "b", "c"],
        category="Options",
    )
    registry = FlagRegistry()
    registry.register(flag)

    parser = MagicMock(spec=argparse.ArgumentParser)
    mock_group = MagicMock()
    parser.add_argument_group.return_value = mock_group

    registry.apply_to_parser(parser)

    mock_group.add_argument.assert_called_with(
        "-v",
        "--values",
        help="Specify multiple values",
        action="store",
        type=str,
        nargs="+",
        choices=["a", "b", "c"],
        dest="values",
    )
