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

### 1. Clone the Repository

```bash
git clone https://github.com/Konijima/gpt-cli.git
cd gpt-cli
```

### 2. Run the Installer

This will:

- Copy `gpt.py` to `~/.gpt-cli/`
- Set up a Python virtual environment
- Install dependencies (if `requirements.txt` exists)
- Create an empty `.env` file (if not already present)
- Install a global `gpt` launcher in `~/.local/bin/gpt`

```bash
./install.sh
```

If `~/.local/bin` is not in your `PATH`, the installer will offer to add it to your shell configuration (`.bashrc` or `.zshrc`).

---

## 🧼 Uninstallation

To completely remove the CLI:

```bash
./uninstall.sh
```

This will:

- Remove the `gpt` command from `~/.local/bin/`
- Delete the CLI install at `~/.gpt-cli/`

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