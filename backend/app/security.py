import base64
import hashlib
import hmac
import re
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Request

from app import config

hasher = PasswordHasher()


def credentials_valid(username: str, password: str) -> bool:
    # The password is always checked, so a wrong username takes as long as a wrong password.
    try:
        password_ok = hasher.verify(config.APP_PASSWORD_HASH, password)
    except VerifyMismatchError:
        password_ok = False
    username_ok = hmac.compare_digest(username.encode(), config.APP_USERNAME.encode())
    return username_ok and password_ok


def client_ip(request: Request) -> str:
    # Render's proxy appends the address it received the request from to X-Forwarded-For,
    # after anything the client sent, so only the last entry can't be forged. Locally
    # there is no proxy, and the header is entirely up to the client.
    forwarded = request.headers.get("x-forwarded-for")
    if config.PRODUCTION and forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host


class RateLimiter:
    """At most `limit` hits per key in any `window` seconds. Kept in memory, so it
    resets on restart and assumes a single instance (as on Render's free tier)."""

    def __init__(self, limit: int, window: float):
        self.limit = limit
        self.window = window
        self.hits: defaultdict[object, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def is_limited(self, key: object) -> bool:
        with self.lock:
            hits = self.hits[key]
            while hits and hits[0] <= time.monotonic() - self.window:
                hits.popleft()
            return len(hits) >= self.limit

    def hit(self, key: object) -> None:
        with self.lock:
            # Drop keys with no recent hits, so many one-off clients can't grow this forever.
            if len(self.hits) > 10_000:
                cutoff = time.monotonic() - self.window
                self.hits = defaultdict(
                    deque, {k: v for k, v in self.hits.items() if v and v[-1] > cutoff}
                )
            self.hits[key].append(time.monotonic())


def content_security_policy(static_dir: Path) -> str:
    # The Next.js export inlines its bootstrap scripts in each page, so allow exactly
    # those by hash instead of allowing all inline scripts. Hashed as raw bytes, as the
    # browser does.
    script_hashes = sorted(
        {
            "'sha256-%s'" % base64.b64encode(hashlib.sha256(script).digest()).decode()
            for page in Path(static_dir).rglob("*.html")
            for script in re.findall(rb"<script>(.*?)</script>", page.read_bytes(), re.DOTALL)
        }
    )
    return "; ".join(
        [
            "default-src 'self'",
            f"script-src 'self' {' '.join(script_hashes)}",
            # React and Next.js set style attributes and the 404 page has a <style> tag.
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data:",
            "font-src 'self'",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
    )
