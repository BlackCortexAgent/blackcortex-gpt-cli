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

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🛠️ Environment Setup

Create a `.env` file in the root directory to configure your API and runtime settings:

```bash
touch .env
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

### Interactive Mode

```bash
python3 gpt.py
```

You’ll enter a REPL-like interface:

```bash
🧠 GPT CLI is ready. Type your question or 'exit' to quit.

You: What is the capital of France?
```

### One-Shot Mode

```bash
python3 gpt.py "Translate 'hello' to French"
```

### From Pipe Input

```bash
echo "Write a haiku about the ocean" | python3 gpt.py
```

### Reset Memory

```bash
python3 gpt.py --reset
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

All conversations are appended to the log file if `OPENAI_LOGFILE` is set:

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

When 20 messages are accumulated, the script calls the API to **summarize** and compact them into the summary for future context.

You can reset memory with:

```bash
python3 gpt.py --reset
```

---

## ❓ Troubleshooting

- ❌ *Missing API key*: Ensure `OPENAI_API_KEY` is set in `.env`
- ❌ *Client failed to initialize*: Verify API key and network connection
- 💭 *Too many tokens*: Reduce prompt or increase summarization frequency

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
