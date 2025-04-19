# GPT CLI — Conversational Assistant for the Terminal

[![Publish to PyPI](https://github.com/BlackCortexAgent/blackcortex-gpt-cli/actions/workflows/publish.yml/badge.svg)](https://github.com/BlackCortexAgent/blackcortex-gpt-cli/actions/workflows/publish.yml)

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

### Interactive Mode

```bash
gpt
```

### One-Shot Command

```bash
gpt "Summarize the French Revolution"
```

### Pipe Input

```bash
echo "Explain quantum computing in simple terms" | gpt
```

### Reset Memory

```bash
gpt --reset
```

### Edit `.env` Configuration

```bash
gpt --env
```

### Uninstall

```bash
gpt --uninstall
```

This removes the installation, `.env`, memory, and global binary.

## Environment Variables Reference

| Variable                     | Description                                         | Default                |
|-----------------------------|-----------------------------------------------------|------------------------|
| `OPENAI_API_KEY`            | Required OpenAI API key                             | —                      |
| `OPENAI_MODEL`              | Model ID (e.g. `gpt-4o`)                            | `gpt-4o`               |
| `OPENAI_DEFAULT_PROMPT`     | System prompt at session start                      | (empty)                |
| `OPENAI_LOGFILE`            | Path to interaction log file                        | `~/.gpt.log`           |
| `OPENAI_TEMPERATURE`        | Response randomness                                 | `0.5`                  |
| `OPENAI_MAX_TOKENS`         | Max tokens per response                             | `4096`                 |
| `OPENAI_MAX_SUMMARY_TOKENS` | Max tokens for memory summarization                 | `2048`                 |
| `OPENAI_MEMORY_PATH`        | Path to memory JSON file                            | `~/.gpt_memory.json`   |
| `OPENAI_STREAM_ENABLED`     | Enable streaming token output                       | `false`                |

## Logging

If `OPENAI_LOGFILE` is set, each interaction is recorded:

```
[2025-04-15 15:51:51] Prompt:
What's the weather like in Tokyo?

Response:
I'm unable to provide live weather updates. Please check a weather site.
--------------------------------------------------------------------------------
```

## Memory System

Memory includes:

- Rolling conversation summary
- The 10 most recent messages

Older messages are summarized once the limit is reached. Use `--reset` to clear memory.

## Troubleshooting

- **Missing API key**: Check `.env` for `OPENAI_API_KEY`
- **Client init failed**: Verify internet and credentials
- **Token limit exceeded**: Reduce input size or use summarization

## Example Output

```bash
You:
Tell me a joke about databases

GPT:
Why did the database break up with the spreadsheet?

Because it couldn't handle the rows of emotions.
```

## License

MIT License

## Credits

Originally created by [Konijima](https://github.com/Konijima), now maintained by the [BlackCortex](https://github.com/BlackCortexAgent) team.
