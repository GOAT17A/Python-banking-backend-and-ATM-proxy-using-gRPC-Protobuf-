from __future__ import annotations

from concurrent import futures

import grpc

from banking_app.db import BankDB
from banking_app.proto import banking_pb2, banking_pb2_grpc


def _ok(message: str = "OK") -> banking_pb2.Status:
    return banking_pb2.Status(ok=True, message=message)


def _err(message: str) -> banking_pb2.Status:
    return banking_pb2.Status(ok=False, message=message)


class BankService(banking_pb2_grpc.BankServiceServicer):
    def __init__(self, db: BankDB):
        self._db = db

    def CreateCustomer(self, request: banking_pb2.CreateCustomerRequest, context):
        try:
            customer = self._db.create_customer(
                name=request.name,
                address=request.address,
                aadhaar=request.aadhaar,
                contact=request.contact,
            )
            return banking_pb2.CustomerResponse(
                status=_ok("Customer created"),
                customer=banking_pb2.Customer(
                    customer_id=customer.customer_id,
                    name=customer.name,
                    address=customer.address,
                    aadhaar=customer.aadhaar,
                    contact=customer.contact,
                ),
            )
        except Exception as exc:
            return banking_pb2.CustomerResponse(status=_err(str(exc)))

    def CreateAccount(self, request: banking_pb2.CreateAccountRequest, context):
        try:
            account = self._db.create_account(
                customer_id=int(request.customer_id),
                account_type=request.account_type,
                initial_deposit=int(request.initial_deposit),
                pin=request.pin,
            )
            return banking_pb2.AccountResponse(
                status=_ok("Account created"),
                account=banking_pb2.Account(
                    account_id=account.account_id,
                    customer_id=account.customer_id,
                    account_type=account.account_type,
                    balance=account.balance,
                    is_closed=account.is_closed,
                ),
            )
        except Exception as exc:
            return banking_pb2.AccountResponse(status=_err(str(exc)))

    def Deposit(self, request: banking_pb2.DepositRequest, context):
        try:
            new_balance = self._db.deposit(
                account_id=int(request.account_id),
                pin=request.pin,
                amount=int(request.amount),
            )
            return banking_pb2.TransactionResponse(status=_ok("Deposit successful"), new_balance=new_balance)
        except Exception as exc:
            return banking_pb2.TransactionResponse(status=_err(str(exc)), new_balance=0)

    def Withdraw(self, request: banking_pb2.WithdrawRequest, context):
        try:
            new_balance = self._db.withdraw(
                account_id=int(request.account_id),
                pin=request.pin,
                amount=int(request.amount),
            )
            return banking_pb2.TransactionResponse(status=_ok("Withdraw successful"), new_balance=new_balance)
        except Exception as exc:
            return banking_pb2.TransactionResponse(status=_err(str(exc)), new_balance=0)

    def GetBalance(self, request: banking_pb2.BalanceRequest, context):
        try:
            balance = self._db.get_balance(account_id=int(request.account_id), pin=request.pin)
            return banking_pb2.BalanceResponse(status=_ok("Balance fetched"), balance=balance)
        except Exception as exc:
            return banking_pb2.BalanceResponse(status=_err(str(exc)), balance=0)

    def CloseAccount(self, request: banking_pb2.CloseAccountRequest, context):
        try:
            self._db.close_account(account_id=int(request.account_id), pin=request.pin)
            return banking_pb2.CloseAccountResponse(status=_ok("Account closed"))
        except Exception as exc:
            return banking_pb2.CloseAccountResponse(status=_err(str(exc)))


def serve(*, listen_addr: str, db_path: str) -> None:
    db = BankDB(db_path)
    db.init_schema()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    banking_pb2_grpc.add_BankServiceServicer_to_server(BankService(db), server)
    server.add_insecure_port(listen_addr)
    server.start()
    try:
        server.wait_for_termination()
    finally:
        server.stop(grace=None)
