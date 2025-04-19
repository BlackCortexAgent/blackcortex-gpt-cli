# BLACKCORTEX GPT CLI
[![Check (Lint + Test)](https://github.com/BlackCortexAgent/blackcortex-gpt-cli/actions/workflows/check.yml/badge.svg)](https://github.com/BlackCortexAgent/blackcortex-gpt-cli/actions/workflows/check.yml)
[![Publish to PyPI](https://github.com/BlackCortexAgent/blackcortex-gpt-cli/actions/workflows/publish.yml/badge.svg)](https://github.com/BlackCortexAgent/blackcortex-gpt-cli/actions/workflows/publish.yml)

### A Conversational Assistant for the Terminal

A terminal-based GPT assistant powered by the OpenAI API, developed by [Konijima](https://github.com/Konijima) and now maintained under the [BlackCortex](https://github.com/BlackCortexAgent/) organization.

## Features

- Persistent memory across sessions with summarization
- Streaming output support
- Command history and logging
- Configurable prompt, model, and temperature
- `.env`-based secure configuration

## Installation

Requires **Python 3.8+**.

### Using PyPI

```bash
pip install blackcortex-gpt-cli
```

### Using pipx (recommended)

```bash
pipx install blackcortex-gpt-cli
```

### From GitHub

```bash
pip install git+https://github.com/BlackCortexAgent/blackcortex-gpt-cli.git
# or with pipx
pipx install git+https://github.com/BlackCortexAgent/blackcortex-gpt-cli.git
```

### Development Installation

```bash
git clone https://github.com/BlackCortexAgent/blackcortex-gpt-cli.git
cd blackcortex-gpt-cli
pip install .
```

### Updating

```bash
pip install --upgrade blackcortex-gpt-cli
# or
pipx upgrade blackcortex-gpt-cli
```

## Environment Setup

Create a `.env` file to configure your API and options:

```bash
touch ~/.gpt-cli/.env
```

### Sample `.env`

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_DEFAULT_PROMPT=You are a helpful CLI assistant.
OPENAI_LOGFILE=~/.gpt.log
OPENAI_TEMPERATURE=0.5
OPENAI_MAX_TOKENS=4096
OPENAI_MAX_SUMMARY_TOKENS=2048
OPENAI_MEMORY_PATH=~/.gpt_memory.json
OPENAI_STREAM_ENABLED=false
```

## Usage

After installation, use the `gpt` command globally.

```bash
gpt [-h] [--no-markdown] [--stream] [--reset] [--summary] [--env]
    [--set-key [API_KEY]] [--ping] [--log] [--clear-log]
    [--update] [--uninstall] [--version] [input_data ...]
```

### Positional Arguments

- `input_data` – One-shot prompt input. Example:
  ```bash
  gpt "Summarize the history of aviation"
  ```

### Options

- `-h, --help` — Show help message and exit
- `--no-markdown` — Disable Markdown formatting in output
- `--stream` — Enable live token streaming during response
- `--reset` — Reset memory and exit
- `--summary` — Display current conversation summary
- `--env` — Edit the `.env` file
- `--set-key [API_KEY]` — Update your OpenAI API key
- `--ping` — Test connection with OpenAI API
- `--log` — Show the full conversation log
- `--clear-log` — Clear the conversation log file
- `--update` — Update GPT CLI to the latest version
- `--uninstall` — Uninstall GPT CLI completely
- `--version` — Display the current version

## Environment Configuration

The GPT CLI loads settings from two locations:

1. `.env` file in the current working directory (if present)
2. `~/.gpt-cli/.env` (default persistent configuration)

You can configure model behavior, memory, logging, and streaming options.

### Sample `.env` File

```env
OPENAI_API_KEY=your-api-key-here             # Required
OPENAI_MODEL=gpt-4o                          # Model ID (default: gpt-4o)
OPENAI_DEFAULT_PROMPT=You are a helpful assistant.
OPENAI_LOGFILE=~/.gpt.log                    # Log file location
OPENAI_TEMPERATURE=0.5                       # Response randomness (default: 0.5)
OPENAI_MAX_TOKENS=4096                       # Max response tokens
OPENAI_MAX_SUMMARY_TOKENS=2048               # Max tokens for memory summarization
OPENAI_MEMORY_PATH=~/.gpt_memory.json        # Path to memory file
OPENAI_MEMORY_LIMIT=10                       # Number of recent messages stored (default: 10)
OPENAI_STREAM_ENABLED=false                  # Enable token-by-token streaming (true/false)
```

> Use `gpt --env` to open and edit the `.env` file in your terminal editor.

## Memory System

Memory includes:

- Rolling conversation summary
- The 10 most recent messages

Older messages are summarized once the limit is reached. Use `--reset` to clear memory.

## Troubleshooting

- **Missing API key**: Check `.env` for `OPENAI_API_KEY`
- **Client init failed**: Verify internet and credentials
- **Token limit exceeded**: Reduce input size or use summarization

## Interactive Example Output

```bash
You: Tell me a joke about databases

GPT: Why did the database break up with the spreadsheet?

Because it couldn't handle the rows of emotions.
────────────────────────────────────────────────────────
```

## License

This project is licensed under the **MIT License**, an OSI-approved open source license that permits the following:

- ✅ Free use for personal, academic, or commercial purposes
- ✅ Permission to modify, merge, publish, and distribute the software
- ✅ Usage with or without attribution (attribution encouraged but not required)
- ✅ No warranty is provided — use at your own risk

## Credits

Originally created by [Konijima](https://github.com/Konijima), now maintained by the [BlackCortex](https://blackcortex.net/) team.
