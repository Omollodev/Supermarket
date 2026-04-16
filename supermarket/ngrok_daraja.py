"""
Ngrok tunnel helpers for local dev: expose Django and align Daraja B2C callback URLs.

Requires NGROK_AUTHTOKEN in the environment when using authtoken_from_env=True.

Safaricom still expects the same URLs registered in the Daraja developer portal; this
module updates what your process sends (MPESA_B2C_* env) to match the live tunnel URL.
"""
from __future__ import annotations

import os
from typing import Any


def connect_ngrok(local_port: int = 8000, **forward_kw: Any):
    """
    Start an HTTP tunnel to localhost:local_port.

    Pass authtoken_from_env=True (default) and set NGROK_AUTHTOKEN, or pass authtoken=...
    """
    import ngrok

    addr = f"localhost:{int(local_port)}"
    forward_kw.setdefault("authtoken_from_env", True)
    return ngrok.forward(addr, **forward_kw)


def apply_ngrok_url_to_daraja_env(public_url: str) -> dict[str, str]:
    """Set MPESA_B2C_RESULT_URL and MPESA_B2C_QUEUE_TIMEOUT_URL from the tunnel base URL."""
    base = (public_url or "").strip().rstrip("/")
    urls = {
        "MPESA_B2C_RESULT_URL": f"{base}/webhooks/mpesa/b2c/result/",
        "MPESA_B2C_QUEUE_TIMEOUT_URL": f"{base}/webhooks/mpesa/b2c/timeout/",
    }
    for key, val in urls.items():
        os.environ[key] = val
    return urls


def connect_ngrok_and_configure_daraja_callbacks(local_port: int = 8000, **forward_kw: Any):
    """
    Open ngrok, push callback URLs into os.environ, print them for Daraja portal copy-paste.
    Call this before Django imports settings (e.g. from runserver_ngrok.py).
    """
    forwarder = connect_ngrok(local_port, **forward_kw)
    public = forwarder.url()
    urls = apply_ngrok_url_to_daraja_env(public)
    print(f"Ingress: {public}")
    print("Daraja callback URLs (also register these in the Daraja app):")
    for k, v in urls.items():
        print(f"  {k}={v}")
    return forwarder
