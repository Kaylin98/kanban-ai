import os

import pytest

from app import ai


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set"
)
def test_live_two_plus_two():
    reply = ai.complete([{"role": "user", "content": "What is 2+2?"}])
    assert "4" in reply
