#!/usr/bin/env python3
"""
Run Django behind an ngrok tunnel and point Daraja B2C callbacks at the public URL.

Usage:
  export NGROK_AUTHTOKEN=2azn1cnpc8auVxoMSPpPnbQigXG_23we1GFZMJYZFFdCH3S7Q   # from https://dashboard.ngrok.com/
  python runserver_ngrok.py              # tunnel -> localhost:8000, runserver :8000
  python runserver_ngrok.py 8085        # tunnel -> localhost:8085, runserver :8085

Any extra args are passed to runserver (e.g. python runserver_ngrok.py 8000 --noreload).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    os.chdir(root)
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)

    local_port = 8000
    rest: list[str] = []
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        local_port = int(sys.argv[1])
        rest = sys.argv[2:]
    else:
        rest = sys.argv[1:]

    from supermarket.ngrok_daraja import connect_ngrok_and_configure_daraja_callbacks

    connect_ngrok_and_configure_daraja_callbacks(local_port)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "supermarket.settings")
    from django.core.management import execute_from_command_line

    manage = root / "manage.py"
    execute_from_command_line(
        [str(manage), "runserver", f"0.0.0.0:{local_port}", *rest]
    )


if __name__ == "__main__":
    main()
