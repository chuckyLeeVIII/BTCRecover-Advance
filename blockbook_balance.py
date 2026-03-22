#!/usr/bin/env python

"""
Thin Blockbook / RICKEY balance helper.

This module does NOT get called yet; we will hook orchestrator.py
into it in a later step, once the file is in place and tested.
"""

from typing import Dict, List, Any

import json
import sys
import urllib.parse
import urllib.request

from blockbook_config import BLOCKBOOK_ENDPOINTS


class BlockbookError(Exception):
    pass


def _http_get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "btcrecover-advance"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
    except Exception as e:
        raise BlockbookError(f"HTTP error for {url}: {e}") from e

    try:
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        raise BlockbookError(f"JSON decode error for {url}: {e}") from e


def get_address_info(chain: str, address: str) -> Dict[str, Any]:
    """
    Query a single address on a given chain via Blockbook-like API.

    Expected Blockbook path:
        GET /api/v2/address/<address>?details=txids
    """
    base = BLOCKBOOK_ENDPOINTS.get(chain)
    if not base:
        raise BlockbookError(f"No Blockbook endpoint configured for chain {chain}")

    # normalize base without trailing slash
    base = base.rstrip("/")

    # standard Blockbook address path
    path = f"/api/v2/address/{urllib.parse.quote(address)}?details=txids"
    url = base + path

    return _http_get_json(url)


def get_balances_for_addresses(
    chain: str, addresses: List[str]
) -> Dict[str, Any]:
    """
    Convenience helper:
        - loops over a list of addresses
        - queries each via Blockbook
        - returns aggregate:
            {
              "chain": chain,
              "total_sats": <int>,
              "addresses": [
                {
                  "address": <str>,
                  "balance_sats": <int>,
                  "txs": <int>,
                  "raw": <full blockbook JSON>,
                },
                ...
              ]
            }
    """
    result: Dict[str, Any] = {
        "chain": chain,
        "total_sats": 0,
        "addresses": [],
    }

    for addr in addresses:
        try:
            info = get_address_info(chain, addr)
        except BlockbookError as e:
            print(f"[Blockbook:{chain}] error for {addr}: {e}", file=sys.stderr)
            continue

        # Blockbook usually returns balance as a string in satoshis or smallest unit
        bal_str = str(info.get("balance", "0"))
        try:
            bal_sats = int(bal_str)
        except ValueError:
            bal_sats = 0

        addr_entry = {
            "address": addr,
            "balance_sats": bal_sats,
            "txs": int(info.get("txs", 0)),
            "raw": info,
        }

        result["addresses"].append(addr_entry)
        result["total_sats"] += bal_sats

    return result
