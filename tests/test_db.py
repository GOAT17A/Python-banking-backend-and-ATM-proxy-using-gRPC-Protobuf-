from __future__ import annotations

import pytest

from banking_app.db import BankDB


def test_create_customer_and_account_and_balance(tmp_path):
    db_path = tmp_path / "bank.db"
    db = BankDB(str(db_path))
    db.init_schema()

    customer = db.create_customer(
        name="Alice",
        address="1 Main St",
        aadhaar="123456789012",
        contact="9999999999",
    )
    account = db.create_account(
        customer_id=customer.customer_id,
        account_type="savings",
        initial_deposit=1000,
        pin="1234",
    )

    assert account.balance == 1000
    assert db.get_balance(account_id=account.account_id, pin="1234") == 1000


def test_invalid_pin_rejected(tmp_path):
    db_path = tmp_path / "bank.db"
    db = BankDB(str(db_path))
    db.init_schema()

    customer = db.create_customer(
        name="Bob",
        address="2 High St",
        aadhaar="222233334444",
        contact="8888888888",
    )
    account = db.create_account(
        customer_id=customer.customer_id,
        account_type="savings",
        initial_deposit=100,
        pin="4321",
    )

    with pytest.raises(ValueError, match="invalid PIN"):
        db.get_balance(account_id=account.account_id, pin="0000")


def test_withdraw_insufficient_balance(tmp_path):
    db_path = tmp_path / "bank.db"
    db = BankDB(str(db_path))
    db.init_schema()

    customer = db.create_customer(
        name="Cara",
        address="3 Park Ave",
        aadhaar="333344445555",
        contact="7777777777",
    )
    account = db.create_account(
        customer_id=customer.customer_id,
        account_type="savings",
        initial_deposit=50,
        pin="1111",
    )

    with pytest.raises(ValueError, match="insufficient balance"):
        db.withdraw(account_id=account.account_id, pin="1111", amount=100)


def test_close_requires_zero_balance(tmp_path):
    db_path = tmp_path / "bank.db"
    db = BankDB(str(db_path))
    db.init_schema()

    customer = db.create_customer(
        name="Dan",
        address="4 Lake Rd",
        aadhaar="444455556666",
        contact="6666666666",
    )
    account = db.create_account(
        customer_id=customer.customer_id,
        account_type="savings",
        initial_deposit=10,
        pin="2222",
    )

    with pytest.raises(ValueError, match="balance must be 0"):
        db.close_account(account_id=account.account_id, pin="2222")

    new_balance = db.withdraw(account_id=account.account_id, pin="2222", amount=10)
    assert new_balance == 0

    db.close_account(account_id=account.account_id, pin="2222")

    with pytest.raises(ValueError, match="account is closed"):
        db.get_balance(account_id=account.account_id, pin="2222")


def test_aadhaar_must_be_12_digits(tmp_path):
    db_path = tmp_path / "bank.db"
    db = BankDB(str(db_path))
    db.init_schema()

    with pytest.raises(ValueError, match=r"aadhaar: must be exactly 12 digits"):
        db.create_customer(
            name="John",
            address="1 Main St",
            aadhaar="12345",
            contact="9999999999",
        )

    with pytest.raises(ValueError, match=r"aadhaar: must be exactly 12 digits"):
        db.create_customer(
            name="John",
            address="1 Main St",
            aadhaar="12345678901A",
            contact="9999999999",
        )


def test_contact_must_be_10_digits(tmp_path):
    db_path = tmp_path / "bank.db"
    db = BankDB(str(db_path))
    db.init_schema()

    with pytest.raises(ValueError, match=r"contact: must be exactly 10 digits"):
        db.create_customer(
            name="John",
            address="1 Main St",
            aadhaar="123456789012",
            contact="12345",
        )

    with pytest.raises(ValueError, match=r"contact: must be exactly 10 digits"):
        db.create_customer(
            name="John",
            address="1 Main St",
            aadhaar="123456789012",
            contact="123456789A",
        )


def test_create_account_invalid_account_type(tmp_path):
    db_path = tmp_path / "bank.db"
    db = BankDB(str(db_path))
    db.init_schema()

    customer = db.create_customer(
        name="Alice",
        address="1 Main St",
        aadhaar="123456789012",
        contact="9999999999",
    )

    with pytest.raises(ValueError, match="account_type"):
        db.create_account(
            customer_id=customer.customer_id,
            account_type="fixed",
            initial_deposit=0,
            pin="1234",
        )


def test_create_account_invalid_pin(tmp_path):
    db_path = tmp_path / "bank.db"
    db = BankDB(str(db_path))
    db.init_schema()

    customer = db.create_customer(
        name="Alice",
        address="1 Main St",
        aadhaar="123456789012",
        contact="9999999999",
    )

    with pytest.raises(ValueError, match="pin"):
        db.create_account(
            customer_id=customer.customer_id,
            account_type="savings",
            initial_deposit=0,
            pin="12ab",
        )


def test_deposit_invalid_amount(tmp_path):
    db_path = tmp_path / "bank.db"
    db = BankDB(str(db_path))
    db.init_schema()

    customer = db.create_customer(
        name="Alice",
        address="1 Main St",
        aadhaar="123456789012",
        contact="9999999999",
    )
    account = db.create_account(
        customer_id=customer.customer_id,
        account_type="savings",
        initial_deposit=0,
        pin="1234",
    )

    with pytest.raises(ValueError, match="amount"):
        db.deposit(account_id=account.account_id, pin="1234", amount=0)
