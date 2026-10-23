import os

from openai import OpenAI

MODEL = os.environ.get("OPENROUTER_MODEL", "dots-studio/dots-3-note-preview:free")
# OpenRouter tries these in order when MODEL fails or is down.
FALLBACK_MODELS = ["nvidia/nemotron-3-super-120b-a12b:free"]
MAX_TOKENS = 2000


def client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        # Free providers occasionally hang; the SDK default would wait 10 minutes.
        timeout=60,
    )


def complete(messages: list[dict]) -> str:
    response = client().chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
        extra_body={"models": FALLBACK_MODELS},
    )
    return response.choices[0].message.content
