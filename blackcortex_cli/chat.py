# chat.py

from openai import OpenAIError
from rich.console import Console

from blackcortex_cli.config import (
    default_prompt,
    max_summary_tokens,
    max_tokens,
    memory_limit,
    memory_path,
    model,
    temperature,
)
from blackcortex_cli.memory import save_memory, summarize_recent

console = Console()


class State:
    """
    Shared runtime state for the GPT CLI session.

    Holds the OpenAI client instance, streaming flag, rolling summary,
    and the list of recent messages for context tracking.
    """

    client = None
    stream_enabled = False
    rolling_summary = ""
    recent_messages = []


MEMORY_INTRO = f"""This is a CLI environment with simulated memory.
You do not have full access to previous conversations, but you may receive a rolling summary
and the {memory_limit} most recent user-assistant message pairs.
Once {memory_limit * 2} messages are reached, a summary is generated to retain context while
conserving memory.
"""


def get_answer(prompt_text: str) -> str:
    """
    Retrieve a response from the OpenAI API, using either streaming or blocking mode.

    Delegates to the appropriate handler based on the current stream_enabled flag.
    """
    return (
        get_answer_streaming(prompt_text)
        if State.stream_enabled
        else get_answer_blocking(prompt_text)
    )


def get_answer_blocking(prompt_text: str) -> str:
    """
    Generate a non-streaming response from the OpenAI API.

    Sends the prompt along with recent memory and optional context, then records
    the assistant’s reply in memory. Handles API errors gracefully.
    """
    State.recent_messages.append({"role": "user", "content": prompt_text})
    messages = build_messages()
    try:
        response = State.client.chat.completions.create(
            model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
        )
    except OpenAIError as e:
        return f"❌ OpenAI API error: {e}"
    reply = response.choices[0].message.content.strip()
    State.recent_messages.append({"role": "assistant", "content": reply})
    check_memory_limit()
    return reply


def get_answer_streaming(prompt_text: str) -> str:
    """
    Generate a streaming response from the OpenAI API and print it progressively.

    Useful for real-time feedback in interactive REPL mode. Stores the final
    assistant reply in memory and summarizes if needed.
    """
    State.recent_messages.append({"role": "user", "content": prompt_text})
    messages = build_messages()
    try:
        stream = State.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
    except OpenAIError as e:
        return f"❌ OpenAI API error: {e}"
    full_reply = ""
    for chunk in stream:
        content = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
        if content:
            full_reply += content
            console.print(content, end="", soft_wrap=True)
    console.print()
    State.recent_messages.append({"role": "assistant", "content": full_reply})
    check_memory_limit()
    return full_reply


def build_messages():
    """
    Construct the message list for the OpenAI API call.

    Includes static memory intro, optional user-defined prompt, rolling summary,
    and the most recent messages up to the memory limit.
    """
    messages = [{"role": "system", "content": f"INTRO: {MEMORY_INTRO}"}]
    if default_prompt:
        messages.append({"role": "system", "content": f"INSTRUCTIONS: {default_prompt}"})
    if State.rolling_summary:
        messages.append({"role": "system", "content": f"SUMMARY: {State.rolling_summary}"})
    messages.extend(State.recent_messages[-memory_limit:])
    return messages


def check_memory_limit():
    """
    Trigger memory summarization if recent message count exceeds the threshold.

    This maintains context efficiency by summarizing earlier messages and
    retaining only the most relevant interactions.
    """
    if len(State.recent_messages) >= memory_limit * 2:
        State.rolling_summary, State.recent_messages = summarize_recent(
            State.client,
            model,
            memory_path,
            State.rolling_summary,
            State.recent_messages,
            memory_limit,
            max_summary_tokens,
        )
    save_memory(memory_path, State.rolling_summary, State.recent_messages)
