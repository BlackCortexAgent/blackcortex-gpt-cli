import os

# === Load .env if available ===
try:
    from dotenv import load_dotenv
    # Load .env from current directory if present
    load_dotenv()
    # Load .env from installation directory (~/.gpt-cli/.env)
    load_dotenv(os.path.expanduser("~/.gpt-cli/.env"))
except ImportError:
    pass

# === Configuration Defaults ===
DEFAULT_MODEL = "gpt-4o"
DEFAULT_PROMPT = ""
DEFAULT_LOG_PATH = "~/.gpt.log"
DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_TOKENS = 4096
DEFAULT_MAX_SUMMARY_TOKENS = 2048
DEFAULT_MEMORY_PATH = "~/.gpt_memory.json"
DEFAULT_STREAM = "false"
DEFAULT_MEMORY_LIMIT = 10

# === Environment Setup ===
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL', DEFAULT_MODEL)
default_prompt = os.getenv('OPENAI_DEFAULT_PROMPT', DEFAULT_PROMPT)
log_file = os.path.expanduser(os.getenv('OPENAI_LOGFILE', DEFAULT_LOG_PATH))
temperature = float(os.getenv('OPENAI_TEMPERATURE', DEFAULT_TEMPERATURE))
max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', DEFAULT_MAX_TOKENS))
max_summary_tokens = int(os.getenv('OPENAI_MAX_SUMMARY_TOKENS', DEFAULT_MAX_SUMMARY_TOKENS))
memory_path = os.path.expanduser(os.getenv('OPENAI_MEMORY_PATH', DEFAULT_MEMORY_PATH))
memory_limit = int(os.getenv('OPENAI_MEMORY_LIMIT', DEFAULT_MEMORY_LIMIT))
stream_enabled = os.getenv('OPENAI_STREAM_ENABLED', DEFAULT_STREAM).lower() == 'true'
