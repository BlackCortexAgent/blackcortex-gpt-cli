import os


def get_cli_path():
    return os.path.expanduser("~/.gpt-cli")


def get_env_path():
    return os.path.expanduser("~/.gpt-cli/.env")
