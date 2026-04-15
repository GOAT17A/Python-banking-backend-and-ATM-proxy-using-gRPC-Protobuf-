from __future__ import annotations

import argparse
import sys


def _missing_deps_message(missing_module: str) -> str:
    return (
        f"Missing dependency: {missing_module}\n\n"
        "Run using the repo venv (recommended):\n"
        "  ./.venv/bin/python main.py ...\n\n"
        "Or install dependencies into your Python environment:\n"
        "  python3 -m pip install -U grpcio protobuf rich\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="banking", description="Bank backend + ATM (gRPC)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    bank_server = sub.add_parser("bank-server", help="Run the bank backend gRPC server")
    bank_server.add_argument("--listen", default="127.0.0.1:50051", help="host:port to bind")
    bank_server.add_argument("--db", default="bank.db", help="SQLite DB file path")

    atm_server = sub.add_parser("atm-server", help="Run the ATM gRPC server (proxies to bank server)")
    atm_server.add_argument("--listen", default="127.0.0.1:50052", help="host:port to bind")
    atm_server.add_argument("--bank", default="127.0.0.1:50051", help="bank server host:port")

    atm = sub.add_parser("atm", help="Run the ATM interactive UI (talks to bank server)")
    atm.add_argument("--atm", default="127.0.0.1:50052", help="ATM server host:port")
    atm.add_argument("--bank", default=None, help="(deprecated) use --atm instead")

    admin = sub.add_parser("bank-admin", help="Run bank admin interactive UI")
    admin.add_argument("--bank", default="127.0.0.1:50051", help="bank server host:port")

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    try:
        if args.cmd == "bank-server":
            from banking_app.bank_server import serve

            serve(listen_addr=args.listen, db_path=args.db)
            return

        if args.cmd == "atm-server":
            from banking_app.atm_server import serve_atm

            serve_atm(listen_addr=args.listen, bank_addr=args.bank)
            return

        if args.cmd == "atm":
            from banking_app.atm_ui import run_atm

            atm_addr = args.bank or args.atm
            run_atm(atm_addr)
            return

        if args.cmd == "bank-admin":
            from banking_app.bank_admin import run_admin

            run_admin(bank_addr=args.bank)
            return
    except ModuleNotFoundError as exc:
        print(_missing_deps_message(exc.name), file=sys.stderr)
        raise SystemExit(1)

    raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
