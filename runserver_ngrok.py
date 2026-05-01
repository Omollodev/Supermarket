#!/usr/bin/env python3
"""
Run Django and point Daraja B2C callback env vars at your public ngrok URL.

<<<<<<< HEAD
Usage:
  export NGROK_AUTHTOKEN=2azn1cnpc8auVxoMSPpPnbQigXG_23we1GFZMJYZFFdCH3S7Q   # from https://dashboard.ngrok.com/
  python runserver_ngrok.py              # tunnel -> localhost:8000, runserver :8000
  python runserver_ngrok.py 8085        # tunnel -> localhost:8085, runserver :8085
=======
Two workflows:
>>>>>>> c4c16f12c9ec4e1cbc67355b297ebabddcf53cf2

1) Embedded ngrok Python SDK (needs a verified ngrok account + token):
     export NGROK_AUTHTOKEN=...   # https://dashboard.ngrok.com/get-started/your-authtoken
     python runserver_ngrok.py [PORT]

2) System ngrok CLI (separate terminal) — tunnel must target the SAME port Django uses:
     # Django on 8000 → use 8000 here (NOT 80 unless Django really listens on 80)
     ngrok http 8000
     # Copy the https://….ngrok-free.app URL from the ngrok UI, then:
     python runserver_ngrok.py --ngrok-url https://YOUR-SUBDOMAIN.ngrok-free.app [PORT]

   Or:  export NGROK_PUBLIC_URL=https://YOUR-SUBDOMAIN.ngrok-free.app
         python runserver_ngrok.py --external [PORT]

Extra args after PORT are passed to runserver (e.g. python runserver_ngrok.py 8000 --noreload).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _parse_args(argv: list[str]) -> tuple[str | None, int, list[str]]:
    """
    Returns (ngrok_public_base_url_or_none, local_port, runserver_extra_args).
    If ngrok_public_base_url_or_none is set, skip the Python SDK tunnel.
    """
    args = list(argv)
    ngrok_url: str | None = None
    external = False

    if "--external" in args:
        external = True
        args.remove("--external")

    if "--ngrok-url" in args:
        i = args.index("--ngrok-url")
        if i + 1 >= len(args):
            print("error: --ngrok-url requires a value", file=sys.stderr)
            sys.exit(2)
        ngrok_url = args[i + 1].strip().rstrip("/")
        del args[i : i + 2]

    if external and not ngrok_url:
        ngrok_url = (os.environ.get("NGROK_PUBLIC_URL") or "").strip().rstrip("/")
        if not ngrok_url:
            print(
                "error: --external needs NGROK_PUBLIC_URL in the environment "
                "(your https://….ngrok… URL from `ngrok http <port>`)",
                file=sys.stderr,
            )
            sys.exit(2)

    local_port = 8000
    if args and args[0].isdigit():
        local_port = int(args[0])
        args = args[1:]

    return ngrok_url, local_port, args


def _print_cli_ngrok_help(local_port: int) -> None:
    print(
        "\nUse the ngrok CLI in another terminal (same port as Django), then pass that URL here:\n"
        f"  ngrok http {local_port}\n"
        "Then run:\n"
        f"  python runserver_ngrok.py --ngrok-url https://<your-host>.ngrok-free.app {local_port}\n"
        "\nNote: `ngrok http 80` forwards to localhost:80 only. "
        f"For `runserver` on {local_port}, use `ngrok http {local_port}`.\n",
        file=sys.stderr,
    )


def main() -> None:
    root = Path(__file__).resolve().parent
    os.chdir(root)
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)

    ngrok_url, local_port, rest = _parse_args(sys.argv[1:])

    from supermarket.ngrok_daraja import (
        apply_ngrok_url_to_daraja_env,
        connect_ngrok_and_configure_daraja_callbacks,
    )

    if ngrok_url:
        urls = apply_ngrok_url_to_daraja_env(ngrok_url)
        print(f"Using public base: {ngrok_url}")
        print("Daraja callback URLs (match these in the Daraja app):")
        for k, v in urls.items():
            print(f"  {k}={v}")
    else:
        try:
            connect_ngrok_and_configure_daraja_callbacks(local_port)
        except ValueError as exc:
            err = str(exc)
            if "4018" in err or "authtoken" in err.lower() or "verified account" in err.lower():
                print(
                    "\nngrok Python SDK: missing or invalid authtoken.\n"
                    "  export NGROK_AUTHTOKEN=…   # from https://dashboard.ngrok.com/get-started/your-authtoken\n"
                    "Or skip the SDK and use the ngrok binary + --ngrok-url (see below).\n",
                    file=sys.stderr,
                )
            else:
                print(f"\nngrok error: {exc}\n", file=sys.stderr)
            _print_cli_ngrok_help(local_port)
            sys.exit(1)
        except Exception as exc:  # noqa: BLE001 — dev helper
            print(f"\nngrok error: {exc}\n", file=sys.stderr)
            _print_cli_ngrok_help(local_port)
            sys.exit(1)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "supermarket.settings")
    from django.core.management import execute_from_command_line

    manage = root / "manage.py"
    execute_from_command_line(
        [str(manage), "runserver", f"0.0.0.0:{local_port}", *rest]
    )


if __name__ == "__main__":
    main()
