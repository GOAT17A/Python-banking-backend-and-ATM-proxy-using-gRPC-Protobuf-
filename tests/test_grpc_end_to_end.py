from __future__ import annotations

from concurrent import futures

import grpc
import pytest

from banking_app.atm_server import ATMProxyService
from banking_app.bank_server import BankService
from banking_app.db import BankDB
from banking_app.proto import banking_pb2, banking_pb2_grpc


@pytest.fixture()
def bank_server(tmp_path):
    db_path = tmp_path / "bank.db"
    db = BankDB(str(db_path))
    db.init_schema()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    banking_pb2_grpc.add_BankServiceServicer_to_server(BankService(db), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    try:
        yield f"127.0.0.1:{port}"
    finally:
        server.stop(grace=None)


@pytest.fixture()
def atm_server(bank_server):
    bank_channel = grpc.insecure_channel(bank_server)
    bank_stub = banking_pb2_grpc.BankServiceStub(bank_channel)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    banking_pb2_grpc.add_BankServiceServicer_to_server(ATMProxyService(bank_stub), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    try:
        yield f"127.0.0.1:{port}", bank_stub
    finally:
        server.stop(grace=None)
        bank_channel.close()


def test_end_to_end_via_atm_proxy(atm_server):
    atm_addr, bank_stub = atm_server

    # Create customer & account via bank (admin path)
    cust = bank_stub.CreateCustomer(
        banking_pb2.CreateCustomerRequest(
            name="Eve",
            address="5 River St",
            aadhaar="5555-6666-7777",
            contact="5555555555",
        )
    )
    assert cust.status.ok

    acct = bank_stub.CreateAccount(
        banking_pb2.CreateAccountRequest(
            customer_id=cust.customer.customer_id,
            account_type="savings",
            initial_deposit=500,
            pin="9999",
        )
    )
    assert acct.status.ok
    account_id = acct.account.account_id

    # Use ATM proxy for balance/withdraw/deposit
    atm_channel = grpc.insecure_channel(atm_addr)
    atm_stub = banking_pb2_grpc.BankServiceStub(atm_channel)

    bal = atm_stub.GetBalance(banking_pb2.BalanceRequest(account_id=account_id, pin="9999"))
    assert bal.status.ok
    assert bal.balance == 500

    wd = atm_stub.Withdraw(banking_pb2.WithdrawRequest(account_id=account_id, pin="9999", amount=120))
    assert wd.status.ok
    assert wd.new_balance == 380

    dep = atm_stub.Deposit(banking_pb2.DepositRequest(account_id=account_id, pin="9999", amount=20))
    assert dep.status.ok
    assert dep.new_balance == 400

    blocked = atm_stub.CreateAccount(
        banking_pb2.CreateAccountRequest(customer_id=1, account_type="x", initial_deposit=0, pin="1234")
    )
    assert not blocked.status.ok

    atm_channel.close()
