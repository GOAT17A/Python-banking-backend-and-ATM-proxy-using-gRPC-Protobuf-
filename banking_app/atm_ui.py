from __future__ import annotations

import grpc
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from banking_app.proto import banking_pb2, banking_pb2_grpc


def _print_status(console: Console, status: banking_pb2.Status) -> None:
    if status.ok:
        console.print(f"[green]{status.message}[/green]")
    else:
        console.print(f"[red]{status.message}[/red]")


def _login(console: Console, stub: banking_pb2_grpc.BankServiceStub):
    while True:
        account_id = IntPrompt.ask("Enter account number", default=0)
        if account_id <= 0:
            console.print("[yellow]Enter a valid account number.[/yellow]")
            continue
        pin = Prompt.ask("Enter PIN", password=True)
        if not pin:
            console.print("[yellow]PIN cannot be empty.[/yellow]")
            continue

        resp = stub.GetBalance(banking_pb2.BalanceRequest(account_id=account_id, pin=pin))
        if resp.status.ok:
            return account_id, pin, resp.balance

        _print_status(console, resp.status)
        again = Prompt.ask("Try again?", choices=["y", "n"], default="y")
        if again != "y":
            return None


def _action_withdraw(console: Console, stub: banking_pb2_grpc.BankServiceStub, *, account_id: int, pin: str) -> None:
    amount = IntPrompt.ask("Withdraw amount", default=0)
    tx = stub.Withdraw(banking_pb2.WithdrawRequest(account_id=account_id, pin=pin, amount=amount))
    _print_status(console, tx.status)
    if tx.status.ok:
        console.print(f"[cyan]New balance: {tx.new_balance}[/cyan]")


def _action_deposit(console: Console, stub: banking_pb2_grpc.BankServiceStub, *, account_id: int, pin: str) -> None:
    amount = IntPrompt.ask("Deposit amount", default=0)
    tx = stub.Deposit(banking_pb2.DepositRequest(account_id=account_id, pin=pin, amount=amount))
    _print_status(console, tx.status)
    if tx.status.ok:
        console.print(f"[cyan]New balance: {tx.new_balance}[/cyan]")


def _action_balance(console: Console, stub: banking_pb2_grpc.BankServiceStub, *, account_id: int, pin: str) -> None:
    bal = stub.GetBalance(banking_pb2.BalanceRequest(account_id=account_id, pin=pin))
    _print_status(console, bal.status)
    if bal.status.ok:
        console.print(f"[cyan]Balance: {bal.balance}[/cyan]")


def _session(console: Console, stub: banking_pb2_grpc.BankServiceStub, *, account_id: int, pin: str) -> None:
    actions = {
        "1": _action_withdraw,
        "2": _action_deposit,
        "3": _action_balance,
    }
    while True:
        table = Table(title="Menu")
        table.add_column("Option", justify="right")
        table.add_column("Action")
        table.add_row("1", "Withdraw")
        table.add_row("2", "Deposit")
        table.add_row("3", "Check balance")
        table.add_row("4", "Exit")
        console.print(table)

        choice = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="3")

        action = actions.get(choice)
        if action is None:
            return
        action(console, stub, account_id=account_id, pin=pin)


def run_atm(atm_addr: str | None = None, bank_addr: str | None = None) -> None:
    console = Console()
    addr = atm_addr or bank_addr
    if not addr:
        raise ValueError("ATM address is required")
    console.print(Panel.fit("ATM", subtitle=f"ATM Server: {addr}"))

    with grpc.insecure_channel(addr) as channel:
        stub = banking_pb2_grpc.BankServiceStub(channel)

        login = _login(console, stub)
        if login is None:
            return
        account_id, pin, balance = login
        console.print(f"[cyan]Login successful. Current balance: {balance}[/cyan]")
        _session(console, stub, account_id=account_id, pin=pin)
