from __future__ import annotations

import re

from .errors import ValidationError

# Business limits (keep conservative; stored as INTEGER in SQLite and proto uses int64)
MAX_AMOUNT = 10**12 - 1  # up to 12 digits


# Name: letters + space and a few common punctuation marks, no digits.
# Minimum length 2.
_NAME_RE = re.compile(r"^[A-Za-z](?:[A-Za-z .'-]{0,48}[A-Za-z.])$")
# allow letters, digits, space and common address punctuation
# Address: allow common address punctuation; minimum length 3.
_ADDRESS_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9 ,./#\-]{1,98}[A-Za-z0-9.])$")


def normalize_digits(value: str) -> str:
    return value.strip().replace(" ", "").replace("-", "")


def validate_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValidationError("name", "cannot be empty")
    if any(ch.isdigit() for ch in name):
        raise ValidationError("name", "must not contain digits")
    if not _NAME_RE.match(name):
        raise ValidationError("name", "contains invalid characters")
    return name


def validate_address(address: str) -> str:
    address = address.strip()
    if not address:
        raise ValidationError("address", "cannot be empty")
    if not _ADDRESS_RE.match(address):
        raise ValidationError(
            "address",
            "contains invalid characters (allowed: letters, digits, space, , . / - #)",
        )
    return address


def validate_aadhaar(aadhaar: str) -> str:
    aadhaar_norm = normalize_digits(aadhaar)
    if not (aadhaar_norm.isdigit() and len(aadhaar_norm) == 12):
        raise ValidationError("aadhaar", "must be exactly 12 digits")
    return aadhaar_norm


def validate_contact(contact: str) -> str:
    contact_norm = normalize_digits(contact)
    if not (contact_norm.isdigit() and len(contact_norm) == 10):
        raise ValidationError("contact", "must be exactly 10 digits")
    return contact_norm


def _validate_positive_int(value: int, *, field: str, max_digits: int) -> int:
    if not isinstance(value, int):
        raise ValidationError(field, "must be an integer")
    if value <= 0:
        raise ValidationError(field, "must be a positive integer")
    if len(str(value)) > max_digits:
        raise ValidationError(field, f"must be at most {max_digits} digits")
    return value


def validate_customer_id(customer_id: int) -> int:
    return _validate_positive_int(customer_id, field="customer_id", max_digits=12)


def validate_account_id(account_id: int) -> int:
    return _validate_positive_int(account_id, field="account_id", max_digits=12)


def validate_account_type(account_type: str) -> str:
    value = account_type.strip().lower()
    if value not in {"savings", "current"}:
        raise ValidationError("account_type", "must be one of: savings, current")
    return value


def validate_pin(pin: str) -> str:
    pin = pin.strip()
    if not pin:
        raise ValidationError("pin", "cannot be empty")
    if not (pin.isdigit() and len(pin) == 4):
        raise ValidationError("pin", "must be exactly 4 digits")
    return pin


def validate_initial_deposit(amount: int) -> int:
    if not isinstance(amount, int):
        raise ValidationError("initial_deposit", "must be an integer")
    if amount < 0:
        raise ValidationError("initial_deposit", "must be >= 0")
    if amount > MAX_AMOUNT:
        raise ValidationError("initial_deposit", f"must be <= {MAX_AMOUNT}")
    return amount


def validate_amount(amount: int, *, field: str = "amount") -> int:
    if not isinstance(amount, int):
        raise ValidationError(field, "must be an integer")
    if amount <= 0:
        raise ValidationError(field, "must be > 0")
    if amount > MAX_AMOUNT:
        raise ValidationError(field, f"must be <= {MAX_AMOUNT}")
    return amount
