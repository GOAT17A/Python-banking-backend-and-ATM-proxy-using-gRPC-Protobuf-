from __future__ import annotations

import grpc
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt

from banking_app.proto import banking_pb2, banking_pb2_grpc


def _create_customer(console: Console, stub: banking_pb2_grpc.BankServiceStub) -> None:
    name = Prompt.ask("Name")
    address = Prompt.ask("Address")
    aadhaar = Prompt.ask("Aadhaar")
    contact = Prompt.ask("Contact")
    resp = stub.CreateCustomer(
        banking_pb2.CreateCustomerRequest(
            name=name,
            address=address,
            aadhaar=aadhaar,
            contact=contact,
        )
    )
    if resp.status.ok:
        console.print(f"[green]{resp.status.message}[/green]")
        console.print(f"Customer ID: [bold]{resp.customer.customer_id}[/bold]")
    else:
        console.print(f"[red]{resp.status.message}[/red]")


def _create_account(console: Console, stub: banking_pb2_grpc.BankServiceStub) -> None:
    customer_id = IntPrompt.ask("Customer ID")
    account_type = Prompt.ask("Account type", default="savings")
    initial_deposit = IntPrompt.ask("Initial deposit", default=0)
    pin = Prompt.ask("Set PIN", password=True)
    resp = stub.CreateAccount(
        banking_pb2.CreateAccountRequest(
            customer_id=customer_id,
            account_type=account_type,
            initial_deposit=initial_deposit,
            pin=pin,
        )
    )
    if resp.status.ok:
        console.print(f"[green]{resp.status.message}[/green]")
        console.print(f"Account ID: [bold]{resp.account.account_id}[/bold]")
        console.print(f"Balance: {resp.account.balance}")
    else:
        console.print(f"[red]{resp.status.message}[/red]")


def _close_account(console: Console, stub: banking_pb2_grpc.BankServiceStub) -> None:
    account_id = IntPrompt.ask("Account ID")
    pin = Prompt.ask("PIN", password=True)
    resp = stub.CloseAccount(banking_pb2.CloseAccountRequest(account_id=account_id, pin=pin))
    if resp.status.ok:
        console.print(f"[green]{resp.status.message}[/green]")
    else:
        console.print(f"[red]{resp.status.message}[/red]")


def run_admin(*, bank_addr: str) -> None:
    console = Console()
    console.print(Panel.fit("Bank Admin", subtitle=f"Bank: {bank_addr}"))

    with grpc.insecure_channel(bank_addr) as channel:
        stub = banking_pb2_grpc.BankServiceStub(channel)

        while True:
            console.print("\n[bold]1[/bold] Create customer")
            console.print("[bold]2[/bold] Create account")
            console.print("[bold]3[/bold] Close account")
            console.print("[bold]4[/bold] Exit")

            choice = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="1")

            if choice == "1":
                _create_customer(console, stub)

            elif choice == "2":
                _create_account(console, stub)

            elif choice == "3":
                _close_account(console, stub)

            elif choice == "4":
                return
