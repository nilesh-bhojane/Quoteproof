"""Gemini AI Extraction Service with Pydantic Validation & Basic Mode Fallback.

Per CONTEXT.md Section 2, 4 & 8:
- AI only extracts: item description, quantity, unit, and specifications.
- AI NEVER produces prices, discounts, tax, or totals.
- Output is validated strictly against InquiryExtractionResult schema.
- Customer text is untrusted: prompt injection instructions are ignored and flagged.
- Failure handling: short timeout, up to 2 retries, then clear error and fallback to Basic mode.
"""

import json
import re
from decimal import Decimal
from typing import Optional
from app.core.config import settings
from app.schemas.inquiry import ExtractedItem, InquiryExtractionResult
from app.services.extraction import extract_inquiry as basic_extract_inquiry

# Prompt injection patterns commonly found in adversarial test inquiries
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous\s+)?instructions",
    r"ignore\s+(the\s+)?price\s+list",
    r"quote\s+(me\s+)?(rs\.?|inr|rupees?)\s*[01]\b",
    r"give\s+(\d+|all|100)%\s*discount",
    r"system\s+prompt",
    r"override\s+(all\s+)?prices?",
    r"you\s+are\s+now\s+in\s+admin\s+mode",
    r"disregard\s+(pricing|catalogue)",
]

SYSTEM_PROMPT = """You are an inquiry extraction co-pilot for a B2B packaging supplier in India.
Your sole job is to parse the customer's raw inquiry text into a structured JSON list of line items.

STRICT NON-NEGOTIABLE RULES:
1. NEVER output or invent prices, discounts, tax rates, or currency amounts.
2. NEVER invent SKUs.
3. Extract ONLY:
   - description: what product the customer wants
   - quantity: numerical amount as a number (or null if missing)
   - unit: e.g. "pcs", "roll", "box", "kg" (default "pcs")
   - specifications: key-value dictionary of specs like dimensions (e.g. "12x10x8"), ply rating (e.g. "3-ply"), color, GSM, etc.
4. Extract delivery_needs: delivery location, urgency, or required delivery date if mentioned.
5. Identify missing_fields: any essential details that the customer omitted (e.g., missing dimensions, missing quantity).
6. Return ONLY valid JSON matching this schema:
{
  "items": [
    {
      "description": "string",
      "quantity": 100,
      "unit": "pcs",
      "specifications": {}
    }
  ],
  "delivery_needs": "string or null",
  "missing_fields": ["string"],
  "warnings": ["string"]
}
"""


def detect_prompt_injection(text: str) -> bool:
    """Detect prompt injection attempts in customer inquiry text."""
    lowered = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            return True
    return False


def _clean_json_output(raw: str) -> str:
    """Strip markdown code fence blocks if returned by model."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def extract_inquiry_with_ai(
    text: str,
    force_basic_mode: bool = False,
    client: Optional[object] = None,
) -> InquiryExtractionResult:
    """Extract line items from inquiry text using Gemini or fallback to Basic mode.

    Args:
        text: Pre-masked customer inquiry text.
        force_basic_mode: If True, skips AI call and uses Basic mode immediately.
        client: Optional pre-configured genai.Client instance (useful for testing/mocking).

    Returns:
        Validated InquiryExtractionResult object.
    """
    injection_detected = detect_prompt_injection(text)
    extra_warnings = []
    if injection_detected:
        extra_warnings.append(
            "Adversarial prompt-injection instructions detected in customer text; instructions were ignored."
        )

    # Basic Mode bypass
    if force_basic_mode or not settings.GEMINI_API_KEY:
        basic_res = basic_extract_inquiry(text)
        items = [
            ExtractedItem(
                description=it["description"],
                quantity=Decimal(str(it["quantity"])) if it.get("quantity") is not None else None,
                unit=it.get("unit", "pcs"),
                specifications=it.get("specifications", {}),
            )
            for it in basic_res.get("items", [])
        ]
        return InquiryExtractionResult(
            items=items,
            missing_fields=basic_res.get("missing_fields", []),
            warnings=extra_warnings + basic_res.get("warnings", []) + [
                "Extracted using Basic rule-based mode."
            ],
            prompt_injection_detected=injection_detected,
            mode="basic",
            tokens_in=0,
            tokens_out=0,
            cost_inr=Decimal("0.00"),
        )

    # Call Gemini API with up to 2 retries
    max_retries = 2
    last_error: Optional[Exception] = None

    if client is None:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\nCustomer Inquiry:\n{text}"}]}
                ],
            )

            raw_text = getattr(response, "text", "") or ""
            json_text = _clean_json_output(raw_text)
            parsed = json.loads(json_text)

            # Extract token usage if provided
            usage = getattr(response, "usage_metadata", None)
            tokens_in = getattr(usage, "prompt_token_count", 0) or 0
            tokens_out = getattr(usage, "candidates_token_count", 0) or 0

            # Gemini Flash pricing estimate in INR (~₹0.008 per 1k input, ₹0.024 per 1k output)
            cost_inr = (Decimal(str(tokens_in)) * Decimal("0.000008")) + (
                Decimal(str(tokens_out)) * Decimal("0.000024")
            )
            cost_inr = cost_inr.quantize(Decimal("0.0001"))

            items = []
            for it in parsed.get("items", []):
                qty_val = it.get("quantity")
                items.append(
                    ExtractedItem(
                        description=str(it.get("description", "")).strip(),
                        quantity=Decimal(str(qty_val)) if qty_val is not None else None,
                        unit=str(it.get("unit", "pcs")),
                        specifications=it.get("specifications") or {},
                    )
                )

            return InquiryExtractionResult(
                items=items,
                delivery_needs=parsed.get("delivery_needs"),
                missing_fields=parsed.get("missing_fields", []),
                warnings=extra_warnings + parsed.get("warnings", []),
                prompt_injection_detected=injection_detected,
                mode="gemini",
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_inr=cost_inr,
            )

        except Exception as e:
            last_error = e

    # On failure after 2 retries: return clear recoverable error and fall back to Basic Mode
    basic_res = basic_extract_inquiry(text)
    items = [
        ExtractedItem(
            description=it["description"],
            quantity=Decimal(str(it["quantity"])) if it.get("quantity") is not None else None,
            unit=it.get("unit", "pcs"),
            specifications=it.get("specifications", {}),
        )
        for it in basic_res.get("items", [])
    ]
    return InquiryExtractionResult(
        items=items,
        missing_fields=basic_res.get("missing_fields", []),
        warnings=extra_warnings + [
            f"Gemini API unavailable after {max_retries} retries ({type(last_error).__name__}). Automatically fell back to Basic Mode."
        ],
        prompt_injection_detected=injection_detected,
        mode="basic_fallback",
        tokens_in=0,
        tokens_out=0,
        cost_inr=Decimal("0.00"),
    )
