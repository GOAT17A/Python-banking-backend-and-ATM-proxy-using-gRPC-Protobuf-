from __future__ import annotations

import grpc
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt

from banking_app.proto import banking_pb2, banking_pb2_grpc
from banking_app.ui_prompts import prompt_int_validated, prompt_validated
from banking_app.validation import (
    validate_aadhaar,
    validate_account_id,
    validate_account_type,
    validate_address,
    validate_contact,
    validate_customer_id,
    validate_initial_deposit,
    validate_name,
    validate_pin,
)


def _create_customer(console: Console, stub: banking_pb2_grpc.BankServiceStub) -> None:
    name = prompt_validated(console, label="Name", validator=validate_name)
    address = prompt_validated(console, label="Address", validator=validate_address)
    aadhaar = prompt_validated(console, label="Aadhaar (12 digits)", validator=validate_aadhaar)
    contact = prompt_validated(console, label="Contact (10 digits)", validator=validate_contact)
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
    customer_id = prompt_int_validated(console, label="Customer ID", validator=validate_customer_id)
    account_type = prompt_validated(console, label="Account type (savings/current)", validator=validate_account_type)
    initial_deposit = prompt_int_validated(
        console, label="Initial deposit", validator=validate_initial_deposit, default=0
    )
    pin = prompt_validated(console, label="Set PIN (4 digits)", validator=validate_pin, password=True)
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
    account_id = prompt_int_validated(console, label="Account ID", validator=validate_account_id)
    pin = prompt_validated(console, label="PIN (4 digits)", validator=validate_pin, password=True)
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
