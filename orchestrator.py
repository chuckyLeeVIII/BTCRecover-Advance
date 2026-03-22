#!/usr/bin/env python

import sys
from datetime import datetime


def handle_recovered(password: str) -> None:
    """
    Triggered every time btcrpass.main() finds a password/key.

    For now:
      - log it locally (without exposing the raw secret on stdout)
      - print a simple confirmation so you see the hook is live

    Later:
      - derive addresses
      - query Blockbook / RICKEY DB
      - run multi‑chain PyKryptonite scan
      - ask user whether to sweep funds, etc.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Minimal local log; adjust path/format as you like
    try:
        with open("recovered.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] recovered secret of length {len(password)}\n")
    except Exception:
        # logging failure should never break a recovery run
        pass

    print(
        f"[+] Trigger fired at {timestamp} "
        f"(secret length={len(password)})",
        file=sys.stderr,
    )
