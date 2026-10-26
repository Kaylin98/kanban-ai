# /// script
# requires-python = ">=3.14"
# dependencies = ["argon2-cffi>=25.1.0"]
# ///
"""Prompts for a password and prints its argon2 hash, the value for APP_PASSWORD_HASH.

Run with: uv run scripts/hash_password.py
"""

from getpass import getpass

from argon2 import PasswordHasher

password = getpass("Password: ")
if password != getpass("Repeat password: "):
    raise SystemExit("The passwords don't match.")
print(PasswordHasher().hash(password))
