from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=64,
    )
    return f"{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(derived).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_part, hash_part = password_hash.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_part.encode())
        expected = base64.urlsafe_b64decode(hash_part.encode())
    except Exception:
        return False

    candidate = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=64,
    )
    return hmac.compare_digest(candidate, expected)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}".encode("ascii"))


def create_token(payload: dict[str, Any], secret_key: str, expires_in_seconds: int) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    body = {**payload, "iat": now, "exp": now + expires_in_seconds}
    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_segment}.{payload_segment}.{_b64url_encode(signature)}"


def decode_token(token: str, secret_key: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise ValueError("Invalid token format") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected_signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    received_signature = _b64url_decode(signature_segment)
    if not hmac.compare_digest(expected_signature, received_signature):
        raise ValueError("Invalid token signature")

    payload = json.loads(_b64url_decode(payload_segment).decode("utf-8"))
    exp = int(payload.get("exp", 0))
    if exp <= int(time.time()):
        raise ValueError("Token expired")
    return payload
