# 🧠 GPT CLI Tool with Persistent Memory and Streaming

A terminal-based GPT assistant powered by the OpenAI API, featuring:

- 🔁 **Persistent memory** across sessions with summarization
- 🌊 **Streaming output** (optional)
- 🧾 **Command history and logging**
- 🧠 **Customizable prompt and model**
- 🔐 **Secure `.env` configuration**

---

## 📦 Features

- Conversational memory with summarization after 20 messages
- Markdown-formatted input/output in terminal
- Command history with autocompletion
- Optional streaming mode (prints as it's generated)
- Command-line and one-shot mode
- Log file support for auditing

---

## 🚀 Installation

Install the GPT CLI via pip or pipx. Requires Python 3.8+.

### Using PyPI

```bash
pip install konijima-gpt-cli
```

### Using pipx (recommended)

```bash
pipx install konijima-gpt-cli
```

### From GitHub (install directly from source)

```bash
# Install directly from the GitHub repo to avoid PyPI conflicts
pip install git+https://github.com/Konijima/gpt-cli.git#egg=konijima-gpt-cli
# or with pipx
pipx install git+https://github.com/Konijima/gpt-cli.git#egg=konijima-gpt-cli
```

### Development Installation

```bash
git clone https://github.com/Konijima/gpt-cli.git
cd gpt-cli
pip install .
```

### Update

```bash
pip install --upgrade konijima-gpt-cli
# or
pipx upgrade konijima-gpt-cli
```

### Uninstallation

```bash
pip uninstall konijima-gpt-cli
# or
pipx uninstall konijima-gpt-cli
```

---

## 🛠️ Environment Setup

A `.env` file is required to store your API key and configuration.

```bash
touch ~/.gpt-cli/.env
```

### Sample `.env` File

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

---

## 🔧 Usage

After installation, you can use the `gpt` command globally.

### Interactive Mode

```bash
gpt
```

You’ll enter a REPL-like interface:

```bash
🧠 GPT CLI is ready. Type your question or 'exit' to quit.
```

### One-Shot Mode

```bash
gpt "Translate 'hello' to French"
```

### From Pipe Input

```bash
echo "Write a haiku about the ocean" | gpt
```

### Reset Memory

```bash
gpt --reset
```

> This clears all saved memory and summaries, then exits.

### Edit Environment Configuration

```bash
gpt --env
```

> Opens your `.env` file in your default terminal editor (e.g., `nano`, `vim`, or set via `$EDITOR`).

### Uninstall

```bash
gpt --uninstall
```

> This command will completely remove the GPT CLI, including the .env file and virtual environment under ~/.gpt-cli, as well as the global gpt command from ~/.local/bin.

---

## 🔐 Environment Variables (Full Reference)

| Variable                     | Description                                         | Default                |
|-----------------------------|-----------------------------------------------------|------------------------|
| `OPENAI_API_KEY`            | **Required.** Your OpenAI API key                  | —                      |
| `OPENAI_MODEL`              | Model to use (`gpt-4o`, `gpt-3.5-turbo`, etc.)     | `gpt-4o`               |
| `OPENAI_DEFAULT_PROMPT`     | System prompt used at the start of each session    | (empty)                |
| `OPENAI_LOGFILE`            | File path to log all interactions                  | `~/.gpt.log`           |
| `OPENAI_TEMPERATURE`        | Sampling temperature (creativity vs determinism)   | `0.5`                  |
| `OPENAI_MAX_TOKENS`         | Maximum tokens per response                        | `4096`                 |
| `OPENAI_MAX_SUMMARY_TOKENS` | Max tokens when summarizing recent interactions    | `2048`                 |
| `OPENAI_MEMORY_PATH`        | Path to memory file for summary + recent messages  | `~/.gpt_memory.json`   |
| `OPENAI_STREAM_ENABLED`     | Enable streaming output (live typing)              | `false`                |

---

## 📝 Log Format

If `OPENAI_LOGFILE` is set, all prompts and responses are saved:

```
[2025-04-15 15:51:51] Prompt:
Hello there

Response:
Hello there again! What would you like to explore or discuss today?
--------------------------------------------------------------------------------
```

---

## 🧹 Memory

Memory consists of:

- A **rolling summary** of conversation
- The **10 most recent messages**

When 20 messages accumulate, the tool summarizes them into the context summary.

To reset memory:

```bash
gpt --reset
```

---

## ❓ Troubleshooting

- ❌ *Missing API key*: Ensure `OPENAI_API_KEY` is set in `.env`
- ❌ *Client failed to initialize*: Check internet and API credentials
- 💭 *Too many tokens*: Try a smaller input or enable summarization

---

## 🧪 Example Output

```bash
You:
Write a joke about servers

GPT:
Why did the server go to therapy?

Because it had too many unresolved requests.
```

---

## 📄 License

MIT License

---

## ✨ Credits

Built with ❤️ by [Konijima](https://github.com/Konijima) and OpenAI’s GPT models.