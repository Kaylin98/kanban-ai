import os

from openai import OpenAI
from pydantic import BaseModel

MODEL = os.environ.get("OPENROUTER_MODEL", "dots-studio/dots-3-note-preview:free")
# OpenRouter tries these in order when MODEL fails or is down.
FALLBACK_MODELS = ["nvidia/nemotron-3-super-120b-a12b:free"]
# Reasoning tokens count towards MAX_TOKENS, so ask both models (which support it) for little.
REASONING = {"effort": "low"}
MAX_TOKENS = 4000


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
        extra_body={"models": FALLBACK_MODELS, "reasoning": REASONING},
    )
    return response.choices[0].message.content


def parse[T: BaseModel](messages: list[dict], schema: type[T]) -> T:
    """Returns the reply as `schema`, using Structured Outputs."""
    response = client().chat.completions.parse(
        model=MODEL,
        messages=messages,
        response_format=schema,
        max_tokens=MAX_TOKENS,
        extra_body={
            "models": FALLBACK_MODELS,
            "reasoning": REASONING,
            # Only route to providers that support Structured Outputs.
            "provider": {"require_parameters": True},
        },
    )
    return response.choices[0].message.parsed
