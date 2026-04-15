from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
import threading
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CustomerRecord:
    customer_id: int
    name: str
    address: str
    aadhaar: str
    contact: str


@dataclass(frozen=True)
class AccountRecord:
    account_id: int
    customer_id: int
    account_type: str
    balance: int
    is_closed: bool


class BankDB:
    _BEGIN_IMMEDIATE = "BEGIN IMMEDIATE"
    _INSERT_TX = (
        "INSERT INTO transactions(account_id,kind,amount,balance_after) VALUES (?,?,?,?)"
    )

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()

    def _conn(self) -> sqlite3.Connection:
        conn: Optional[sqlite3.Connection] = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None,  # manage transactions manually
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn = conn
        return conn

    def init_schema(self) -> None:
        conn = self._conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              address TEXT NOT NULL,
              aadhaar TEXT NOT NULL UNIQUE,
              contact TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS accounts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              customer_id INTEGER NOT NULL REFERENCES customers(id),
              account_type TEXT NOT NULL,
              balance INTEGER NOT NULL DEFAULT 0,
              pin_salt BLOB NOT NULL,
              pin_hash BLOB NOT NULL,
              is_closed INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS transactions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              account_id INTEGER NOT NULL REFERENCES accounts(id),
              kind TEXT NOT NULL,
              amount INTEGER NOT NULL,
              balance_after INTEGER NOT NULL,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )

    @staticmethod
    def _hash_pin(pin: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            100_000,
        )

    def create_customer(self, *, name: str, address: str, aadhaar: str, contact: str) -> CustomerRecord:
        conn = self._conn()
        cur = conn.execute(
            "INSERT INTO customers(name,address,aadhaar,contact) VALUES (?,?,?,?)",
            (name.strip(), address.strip(), aadhaar.strip(), contact.strip()),
        )
        customer_id = int(cur.lastrowid)
        return CustomerRecord(
            customer_id=customer_id,
            name=name.strip(),
            address=address.strip(),
            aadhaar=aadhaar.strip(),
            contact=contact.strip(),
        )

    def create_account(
        self,
        *,
        customer_id: int,
        account_type: str,
        initial_deposit: int,
        pin: str,
    ) -> AccountRecord:
        if initial_deposit < 0:
            raise ValueError("initial_deposit must be >= 0")
        if not pin or len(pin) < 4:
            raise ValueError("PIN must be at least 4 characters")

        conn = self._conn()
        salt = os.urandom(16)
        pin_hash = self._hash_pin(pin, salt)

        conn.execute(self._BEGIN_IMMEDIATE)
        try:
            row = conn.execute("SELECT id FROM customers WHERE id=?", (customer_id,)).fetchone()
            if row is None:
                raise ValueError("customer_id not found")

            cur = conn.execute(
                "INSERT INTO accounts(customer_id,account_type,balance,pin_salt,pin_hash) VALUES (?,?,?,?,?)",
                (customer_id, account_type.strip(), int(initial_deposit), salt, pin_hash),
            )
            account_id = int(cur.lastrowid)
            if initial_deposit > 0:
                conn.execute(
                    self._INSERT_TX,
                    (account_id, "deposit", int(initial_deposit), int(initial_deposit)),
                )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

        return AccountRecord(
            account_id=account_id,
            customer_id=customer_id,
            account_type=account_type.strip(),
            balance=int(initial_deposit),
            is_closed=False,
        )

    def _verify_pin(self, account_id: int, pin: str, *, conn: sqlite3.Connection) -> sqlite3.Row:
        row = conn.execute(
            "SELECT id, customer_id, account_type, balance, pin_salt, pin_hash, is_closed FROM accounts WHERE id=?",
            (account_id,),
        ).fetchone()
        if row is None:
            raise ValueError("account_id not found")
        if int(row["is_closed"]) == 1:
            raise ValueError("account is closed")

        salt = bytes(row["pin_salt"])
        expected = bytes(row["pin_hash"])
        actual = self._hash_pin(pin, salt)
        if not hmac.compare_digest(expected, actual):
            raise ValueError("invalid PIN")
        return row

    def deposit(self, *, account_id: int, pin: str, amount: int) -> int:
        if amount <= 0:
            raise ValueError("amount must be > 0")

        conn = self._conn()
        conn.execute(self._BEGIN_IMMEDIATE)
        try:
            row = self._verify_pin(account_id, pin, conn=conn)
            new_balance = int(row["balance"]) + int(amount)
            conn.execute("UPDATE accounts SET balance=? WHERE id=?", (new_balance, account_id))
            conn.execute(
                self._INSERT_TX,
                (account_id, "deposit", int(amount), new_balance),
            )
            conn.execute("COMMIT")
            return new_balance
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def withdraw(self, *, account_id: int, pin: str, amount: int) -> int:
        if amount <= 0:
            raise ValueError("amount must be > 0")

        conn = self._conn()
        conn.execute(self._BEGIN_IMMEDIATE)
        try:
            row = self._verify_pin(account_id, pin, conn=conn)
            balance = int(row["balance"])
            if amount > balance:
                raise ValueError("insufficient balance")
            new_balance = balance - int(amount)
            conn.execute("UPDATE accounts SET balance=? WHERE id=?", (new_balance, account_id))
            conn.execute(
                self._INSERT_TX,
                (account_id, "withdraw", int(amount), new_balance),
            )
            conn.execute("COMMIT")
            return new_balance
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def get_balance(self, *, account_id: int, pin: str) -> int:
        conn = self._conn()
        row = self._verify_pin(account_id, pin, conn=conn)
        return int(row["balance"])

    def close_account(self, *, account_id: int, pin: str) -> None:
        conn = self._conn()
        conn.execute(self._BEGIN_IMMEDIATE)
        try:
            row = self._verify_pin(account_id, pin, conn=conn)
            balance = int(row["balance"])
            if balance != 0:
                raise ValueError("account balance must be 0 to close")
            conn.execute("UPDATE accounts SET is_closed=1 WHERE id=?", (account_id,))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def get_account_summary(self, *, account_id: int) -> AccountRecord:
        conn = self._conn()
        row = conn.execute(
            "SELECT id, customer_id, account_type, balance, is_closed FROM accounts WHERE id=?",
            (account_id,),
        ).fetchone()
        if row is None:
            raise ValueError("account_id not found")
        return AccountRecord(
            account_id=int(row["id"]),
            customer_id=int(row["customer_id"]),
            account_type=str(row["account_type"]),
            balance=int(row["balance"]),
            is_closed=bool(int(row["is_closed"])),
        )

    def get_customer(self, *, customer_id: int) -> CustomerRecord:
        conn = self._conn()
        row = conn.execute(
            "SELECT id, name, address, aadhaar, contact FROM customers WHERE id=?",
            (customer_id,),
        ).fetchone()
        if row is None:
            raise ValueError("customer_id not found")
        return CustomerRecord(
            customer_id=int(row["id"]),
            name=str(row["name"]),
            address=str(row["address"]),
            aadhaar=str(row["aadhaar"]),
            contact=str(row["contact"]),
        )
