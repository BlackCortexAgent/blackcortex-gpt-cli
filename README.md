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
make install
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

### 🧾 CLI Usage

After installation, use the `gpt` command globally.

#### **Positional Arguments**

| Argument     | Description                |
| ------------ | -------------------------- |
| `input_data` | Send one-shot prompt input |

#### **Options**

| Flag                                  | Description                                            |
| ------------------------------------- | ------------------------------------------------------ |
| `-h`, `--help`                        | Show this help message and exit                        |
| `-m`, `--no-markdown`                 | Disable Markdown formatting in responses               |
| `-s`, `--stream`                      | Stream assistant responses token-by-token              |
| `-r`, `--reset`                       | Reset context memory                                   |
| `-e`, `--env`                         | Open configuration file                                |
| `-u`, `--update`                      | Update the CLI tool                                    |
| `-x`, `--uninstall`                   | Uninstall the CLI tool                                 |
| `-k [API_KEY]`, `--set-key [API_KEY]` | Set or update OpenAI API key (prompt if value omitted) |
| `-p`, `--ping`                        | Test OpenAI API connectivity                           |
| `-l`, `--log`                         | Display conversation log                               |
| `-c`, `--clear-log`                   | Clear the conversation log                             |
| `-v`, `--version`                     | Display current version                                |

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
OPENAI_MAX_SUMMARY_TOKENS=2048              # Max tokens for memory summarization
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

## Contributing

We welcome all contributions!

### 🚀 Quickstart for Development

```bash
git clone https://github.com/BlackCortexAgent/blackcortex-gpt-cli.git
cd blackcortex-gpt-cli
make dev
```

Run tests:

```bash
make test       # uses virtualenv (.venv)
# or use 'make ci-release' if running outside .venv
```

Lint and format:

```bash
make lint
make format
```

Use `make check` to lint, test, build, and validate in `.venv`.  
Use `make ci-release` for system Python (e.g., CI/CD pipelines).

### 📄 See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

## License

This project is licensed under the **MIT License**, an OSI-approved open source license that permits the following:

- ✅ Free use for personal, academic, or commercial purposes
- ✅ Permission to modify, merge, publish, and distribute the software
- ✅ Usage with or without attribution (attribution encouraged but not required)
- ✅ No warranty is provided — use at your own risk

## Credits

Originally created by [Konijima](https://github.com/Konijima), now maintained by the [BlackCortex](https://blackcortex.net/) team.
