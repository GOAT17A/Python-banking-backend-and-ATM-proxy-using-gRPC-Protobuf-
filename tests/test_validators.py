from __future__ import annotations

import pytest

from banking_app.validation import (
    MAX_AMOUNT,
    ValidationError,
    validate_aadhaar,
    validate_account_id,
    validate_account_type,
    validate_address,
    validate_amount,
    validate_contact,
    validate_customer_id,
    validate_initial_deposit,
    validate_name,
    validate_pin,
)


def test_validate_name_rejects_digits():
    with pytest.raises(ValidationError, match=r"name: must not contain digits"):
        validate_name("John1")


def test_validate_name_accepts_basic():
    assert validate_name("John Doe") == "John Doe"


def test_validate_address_rejects_bad_chars():
    with pytest.raises(ValidationError, match=r"address: contains invalid characters"):
        validate_address("Apt@12")


def test_validate_aadhaar_normalizes_and_validates():
    assert validate_aadhaar("1234-5678-9012") == "123456789012"
    with pytest.raises(ValidationError, match=r"aadhaar: must be exactly 12 digits"):
        validate_aadhaar("123")


def test_validate_contact_normalizes_and_validates():
    assert validate_contact("99999-99999") == "9999999999"
    with pytest.raises(ValidationError, match=r"contact: must be exactly 10 digits"):
        validate_contact("123")


def test_validate_ids():
    assert validate_customer_id(1) == 1
    assert validate_account_id(12) == 12
    with pytest.raises(ValidationError, match=r"customer_id: must be a positive integer"):
        validate_customer_id(0)


def test_validate_account_type():
    assert validate_account_type("SAVINGS") == "savings"
    assert validate_account_type("current") == "current"
    with pytest.raises(ValidationError, match=r"account_type: must be one of"):
        validate_account_type("fd")


def test_validate_pin():
    assert validate_pin("1234") == "1234"
    with pytest.raises(ValidationError, match=r"pin: must be exactly 4 digits"):
        validate_pin("12345")
    with pytest.raises(ValidationError, match=r"pin: must be exactly 4 digits"):
        validate_pin("12ab")


def test_validate_amount_limits():
    assert validate_initial_deposit(0) == 0
    assert validate_amount(1) == 1
    with pytest.raises(ValidationError, match=r"initial_deposit: must be >= 0"):
        validate_initial_deposit(-1)
    with pytest.raises(ValidationError, match=r"amount: must be > 0"):
        validate_amount(0)
    with pytest.raises(ValidationError):
        validate_amount(MAX_AMOUNT + 1)
