# logging.py
import os
from datetime import datetime

from blackcortex_cli.config import log_file


def write_to_log(prompt_text: str, response: str):
    """
    Append a prompt and its corresponding response to the log file with a timestamp.

    Ensures the log file exists and is only accessible by the user (chmod 600).
    This helps preserve a history of interactions for later review or debugging.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Prompt:\n{prompt_text}\n\nResponse:\n{response}\n{'-' * 80}\n")
        os.chmod(log_file, 0o600)
