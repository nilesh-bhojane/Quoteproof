import pytest
from app.services.masking_service import mask_pii, restore_pii


def test_mask_email():
    text = "Send quote to rajesh.kumar@example.com for 500 units."
    masked, mapping = mask_pii(text)
    assert "rajesh.kumar@example.com" not in masked
    assert "[EMAIL_1]" in masked
    assert mapping["[EMAIL_1]"] == "rajesh.kumar@example.com"
    assert restore_pii(masked, mapping) == text


def test_mask_phone_numbers():
    text = "Call me at +91 9876543210 or 9123456789 regarding 200 boxes."
    masked, mapping = mask_pii(text)
    assert "9876543210" not in masked
    assert "9123456789" not in masked
    assert "[PHONE_" in masked
    assert restore_pii(masked, mapping) == text


def test_mask_name_signoff():
    text = "Need rates for corrugated boxes. Regards, Amit Sharma"
    masked, mapping = mask_pii(text)
    assert "Amit Sharma" not in masked
    assert "[NAME_" in masked
    assert restore_pii(masked, mapping) == text


def test_no_leak_on_empty_or_clean_text():
    text = "Need 500 boxes 12x10x8, 3-ply, delivery to Pune next week."
    masked, mapping = mask_pii(text)
    assert masked == text
    assert mapping == {}
