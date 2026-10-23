import os

from openai import OpenAI

MODEL = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")


def client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )


def complete(messages: list[dict]) -> str:
    response = client().chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content
