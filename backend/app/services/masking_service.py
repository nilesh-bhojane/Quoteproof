"""Masking service for PII (personally identifiable information).

Per CONTEXT.md Section 2 & 8:
- Phone numbers, email addresses, and person names must be masked BEFORE calling any external AI.
- Returns the masked text along with the entity-to-placeholder mapping.
- Raw customer identifiers are never logged or stored on the backend.
"""

import re
from typing import Tuple, Dict


# Common Indian and international phone number patterns
# Matches: +91 9876543210, +91-98765-43210, 9876543210, 09876543210, 98765 43210, etc.
PHONE_REGEX = re.compile(
    r"(?:\+?91[\s\-]?)?(?:\b[6-9]\d{4}[\s\-]?\d{5}\b|\b0?[6-9]\d{9}\b)"
)

# Standard RFC-compliant email pattern
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# Common name prefixes in business inquiries
NAME_PREFIX_REGEX = re.compile(
    r"(?:(?:kind\s+att(?:entio)?n|attn?|contact|regards|from|thanks\s*(?:&|and)\s*regards|cheers|sincerely)[\s,:]+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    re.IGNORECASE,
)


def mask_pii(text: str) -> Tuple[str, Dict[str, str]]:
    """Mask email addresses, phone numbers, and detected names in inquiry text.

    Returns:
        (masked_text, mapping): Where mapping holds {placeholder: original_value}.
    """
    mapping: Dict[str, str] = {}
    masked_text = text

    # 1. Mask Email Addresses
    email_idx = 1
    for match in EMAIL_REGEX.finditer(masked_text):
        original = match.group(0)
        placeholder = f"[EMAIL_{email_idx}]"
        mapping[placeholder] = original
        email_idx += 1

    for placeholder, original in mapping.items():
        if placeholder.startswith("[EMAIL_"):
            masked_text = masked_text.replace(original, placeholder)

    # 2. Mask Phone Numbers
    phone_idx = 1
    phone_matches = list(PHONE_REGEX.finditer(masked_text))
    # Replace from back to front to preserve string indices if any overlapping
    for match in reversed(phone_matches):
        original = match.group(0)
        # Avoid masking placeholders or item quantities (e.g. exactly 5-digit quantity)
        # PHONE_REGEX requires 10 digits starting with 6-9
        placeholder = f"[PHONE_{phone_idx}]"
        mapping[placeholder] = original
        masked_text = masked_text[:match.start()] + placeholder + masked_text[match.end():]
        phone_idx += 1

    # 3. Mask Names (context-based from greetings/sign-offs/attn)
    name_idx = 1
    name_matches = list(NAME_PREFIX_REGEX.finditer(masked_text))
    for match in reversed(name_matches):
        full_match = match.group(0)
        name_part = match.group(1)
        placeholder = f"[NAME_{name_idx}]"
        mapping[placeholder] = name_part
        # Replace only the name part
        start = match.start(1)
        end = match.end(1)
        masked_text = masked_text[:start] + placeholder + masked_text[end:]
        name_idx += 1

    return masked_text, mapping


def restore_pii(text: str, mapping: Dict[str, str]) -> str:
    """Restore placeholders with original PII values for client-side display."""
    restored = text
    for placeholder, original in mapping.items():
        restored = restored.replace(placeholder, original)
    return restored
