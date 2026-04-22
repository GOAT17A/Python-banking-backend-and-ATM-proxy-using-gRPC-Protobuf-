(Banking project)

This repo contains a **Bank backend gRPC server** and an **ATM terminal UI** that talks to it using gRPC.

## Quickstart

### 1) Start the Bank backend

```bash
./.venv/bin/python3 main.py bank-server --listen 127.0.0.1:50051 --db bank.db
```

### 2) Start the ATM server (proxy)

```bash
./.venv/bin/python3 main.py atm-server --listen 127.0.0.1:50052 --bank 127.0.0.1:50051
```

### 3) Create a customer + account (Bank Admin)

```bash
./.venv/bin/python3 main.py bank-admin --bank 127.0.0.1:50051
```

This prints the **Customer ID** and **Account ID**. You also set a **PIN** while creating the account.

### 4) Use the ATM UI

```bash
./.venv/bin/python3 main.py atm --atm 127.0.0.1:50052
```
###.python -m pytest -q

ATM flow:
- Enter account number
- Enter PIN
- Withdraw / Deposit / Check balance / Exit

## Notes

- Data is persisted in SQLite (default: `bank.db`).
- Amounts are stored as integers (no decimals).


#validations should happen at each field while 
#withdraw insufficient balance
#close requires zero balance
#invalid pin - 