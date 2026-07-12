"""
core.py
-------
The core chatbot logic, kept independent of any web layer.

It can be used in two ways:
  1. Run directly in the terminal:   python core.py
  2. Imported by the backend API:    from core import get_reply

Keeping the logic here (free of HTTP code) means the same function powers both
the terminal chat and the web API. This is the single source of truth.

The bot is intentionally simple and rule-based so the project stays dependency
free. Swap out get_reply() with a call to a real model/service when needed.
"""

import random

# Rule table: each entry is (keywords, list of possible replies).
# The first rule whose keywords appear in the user's message wins.
_RULES = [
    (["hello", "hi", "hey"], ["Hello! How can I help you today?", "Hi there!"]),
    (["how are you"], ["I'm just a script, but I'm doing great. You?"]),
    (["your name", "who are you"], ["I'm a simple Python chatbot."]),
    (["bye", "goodbye", "exit", "quit"], ["Goodbye! Have a great day."]),
    (["thanks", "thank you"], ["You're welcome!"]),
    (["help"], ["Try saying hello, asking my name, or asking how I am."]),
    (["time", "date"], ["I can't read the clock, but your computer can!"]),
]

_FALLBACKS = [
    "Interesting — tell me more.",
    "I'm not sure I understand. Could you rephrase?",
    "Hmm, I don't have an answer for that yet.",
]


def get_reply(message):
    """Generate a bot reply for a user message.

    Args:
        message (str): The user's message.

    Returns:
        str: The bot's reply.

    Raises:
        ValueError: If the message is empty or not a string.
    """
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message must be a non-empty string.")

    text = message.lower()
    for keywords, replies in _RULES:
        if any(keyword in text for keyword in keywords):
            return random.choice(replies)

    return random.choice(_FALLBACKS)


def _run_terminal():
    """Interactive terminal chat loop."""
    print("=== Simple Chatbot (terminal) ===")
    print("Type a message and press Enter. Type 'quit' to exit.\n")

    while True:
        message = input("You: ").strip()
        if message.lower() in ("quit", "exit"):
            print("Bot: Goodbye! Have a great day.")
            break
        if not message:
            continue
        print(f"Bot: {get_reply(message)}\n")


if __name__ == "__main__":
    _run_terminal()
