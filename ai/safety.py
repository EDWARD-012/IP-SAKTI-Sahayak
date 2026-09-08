"""
ai/safety.py — Deterministic input safety checks (no LLM).

Public API
----------
SafetyResult  — frozen dataclass; truthy when ok=True
check(text)   — main entry point; returns SafetyResult
check_input(text) — compatibility wrapper; returns (ok: bool, reason: str)

MIN_LENGTH / MAX_LENGTH — exported so tests can use them parametrically.

Reason codes (SafetyResult.reason)
-----------------------------------
""             — passed all checks
"too_short"    — stripped length < MIN_LENGTH (includes whitespace-only)
"too_long"     — length > MAX_LENGTH
"pii_email"    — email address detected
"pii_aadhaar"  — Aadhaar-like 12-digit number detected (plain, spaced, or hyphenated)
"pii_phone"    — Indian phone number detected
"prompt_injection" — known adversarial injection pattern
"""
from __future__ import annotations

import dataclasses
import logging
import re

logger = logging.getLogger("ai")

# ── Constants ─────────────────────────────────────────────────────────────────
MIN_LENGTH: int = 5
MAX_LENGTH: int = 1000


# ── Result type ───────────────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class SafetyResult:
    """
    Immutable result from check().

    ``bool(result)`` returns ``result.ok`` so callers can write::

        if not check(question):
            return out_of_scope_response
    """
    ok: bool
    reason: str = ""

    def __bool__(self) -> bool:
        return self.ok


# ── PII patterns ──────────────────────────────────────────────────────────────

_RE_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# Aadhaar: 12 consecutive digits (no separator)
_RE_AADHAAR_PLAIN = re.compile(r"(?<!\d)\d{12}(?!\d)")
# Aadhaar: 4-4-4 groups with space or hyphen separator
_RE_AADHAAR_SEP = re.compile(r"(?<!\d)\d{4}[\s\-]\d{4}[\s\-]\d{4}(?!\d)")

# Indian mobile: 10 digits starting with 6-9 (optional +91 / 0 prefix)
_RE_PHONE = re.compile(r"(?<!\d)(?:\+91[\s\-]?|0)?[6-9]\d{9}(?!\d)")


# ── Prompt injection patterns ─────────────────────────────────────────────────

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bignore\s+(previous|above|all|prior)\b", re.I),
    re.compile(r"\bforget\s+(your|all|the)\s+(instructions|rules|constraints|above)\b", re.I),
    re.compile(r"\bdisregard\s+(all|any|your|prior|previous)\b", re.I),
    re.compile(r"\bbypass\s+(all|any|your|the)\b", re.I),
    re.compile(r"\boverride\s+(your|all|the)\b", re.I),
    re.compile(r"\bsystem\s*:", re.I),
    re.compile(r"\bjailbreak\b", re.I),
    re.compile(r"\bact\s+as\b", re.I),
    re.compile(r"\bpretend\s+(you\s+are|to\s+be)\b", re.I),
    re.compile(r"\byou\s+are\s+now\b", re.I),                 # "you are now X"
    re.compile(r"\bDAN\b"),                                     # Do Anything Now
    re.compile(r"\breveal\s+your\s+(prompt|system|instructions)\b", re.I),
    re.compile(r"\bprint\s+your\s+(prompt|system|instructions)\b", re.I),
    re.compile(r"<\s*/?system\s*>", re.I),
    re.compile(r"\bINSTRUCTIONS?\s*:", re.I),
]


# ── Core check ────────────────────────────────────────────────────────────────

def check(text: str) -> SafetyResult:
    """
    Run all safety checks on *text* and return a SafetyResult.

    Checks run in order: length → PII → prompt injection.
    Returns on the first failure (no partial reasons).
    """
    # ── 1. Length ─────────────────────────────────────────────────
    stripped = text.strip()
    if len(stripped) < MIN_LENGTH:
        return SafetyResult(ok=False, reason="too_short")
    if len(text) > MAX_LENGTH:
        return SafetyResult(ok=False, reason="too_long")

    # ── 2. PII ────────────────────────────────────────────────────
    if _RE_EMAIL.search(text):
        return SafetyResult(ok=False, reason="pii_email")

    if _RE_AADHAAR_PLAIN.search(text) or _RE_AADHAAR_SEP.search(text):
        return SafetyResult(ok=False, reason="pii_aadhaar")

    if _RE_PHONE.search(text):
        return SafetyResult(ok=False, reason="pii_phone")

    # ── 3. Prompt injection ───────────────────────────────────────
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(
                "safety.check: prompt injection pattern=%r matched in question",
                pattern.pattern,
            )
            return SafetyResult(ok=False, reason="prompt_injection")

    return SafetyResult(ok=True, reason="")


# ── Backward-compatible wrapper ───────────────────────────────────────────────

def check_input(question: str) -> tuple[bool, str]:
    """
    Compatibility shim for callers that expect (bool, str).

    Wraps check() so ai.pipeline can call::

        is_safe, reason = check_input(question)
    """
    result = check(question)
    return result.ok, result.reason
