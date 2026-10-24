"""Custom domain exceptions for QuoteProof AI."""


class QuoteProofException(Exception):
    """Base exception for all domain errors."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class ProductNotFoundException(QuoteProofException):
    def __init__(self, identifier: str):
        super().__init__(
            code="PRODUCT_NOT_FOUND",
            message=f"Product '{identifier}' could not be matched in the price list.",
        )


class StockShortageException(QuoteProofException):
    def __init__(self, product_name: str, available: int, requested: int):
        super().__init__(
            code="STOCK_SHORTAGE",
            message=f"Insufficient stock for '{product_name}'. Requested {requested}, but only {available} available.",
        )


class PricingException(QuoteProofException):
    def __init__(self, message: str):
        super().__init__(code="PRICING_ERROR", message=message)


class ApprovalBlockedException(QuoteProofException):
    def __init__(self, unresolved_flags: list):
        super().__init__(
            code="APPROVAL_BLOCKED",
            message=f"Cannot approve quotation with blocking flags: {unresolved_flags}",
        )


class GeminiExtractionException(QuoteProofException):
    def __init__(self, message: str):
        super().__init__(code="GEMINI_EXTRACTION_ERROR", message=message)


class PromptInjectionException(QuoteProofException):
    def __init__(self, message: str = "Suspicious instructions detected in inquiry text."):
        super().__init__(code="PROMPT_INJECTION_DETECTED", message=message)
