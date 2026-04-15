from __future__ import annotations

from concurrent import futures

import grpc

from banking_app.proto import banking_pb2, banking_pb2_grpc


def _err_status(message: str) -> banking_pb2.Status:
    return banking_pb2.Status(ok=False, message=message)


_NOT_AVAILABLE = "Not available via ATM"


class ATMProxyService(banking_pb2_grpc.BankServiceServicer):
    def __init__(self, bank_stub: banking_pb2_grpc.BankServiceStub):
        self._bank = bank_stub

    def CreateCustomer(self, request: banking_pb2.CreateCustomerRequest, context):
        return banking_pb2.CustomerResponse(status=_err_status(_NOT_AVAILABLE))

    def CreateAccount(self, request: banking_pb2.CreateAccountRequest, context):
        return banking_pb2.AccountResponse(status=_err_status(_NOT_AVAILABLE))

    def CloseAccount(self, request: banking_pb2.CloseAccountRequest, context):
        return banking_pb2.CloseAccountResponse(status=_err_status(_NOT_AVAILABLE))

    def Deposit(self, request: banking_pb2.DepositRequest, context):
        return self._bank.Deposit(request)

    def Withdraw(self, request: banking_pb2.WithdrawRequest, context):
        return self._bank.Withdraw(request)

    def GetBalance(self, request: banking_pb2.BalanceRequest, context):
        return self._bank.GetBalance(request)


def serve_atm(*, listen_addr: str, bank_addr: str) -> None:
    bank_channel = grpc.insecure_channel(bank_addr)
    bank_stub = banking_pb2_grpc.BankServiceStub(bank_channel)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    banking_pb2_grpc.add_BankServiceServicer_to_server(ATMProxyService(bank_stub), server)
    server.add_insecure_port(listen_addr)
    server.start()
    try:
        server.wait_for_termination()
    finally:
        server.stop(grace=None)
        bank_channel.close()
