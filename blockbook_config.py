#!/usr/bin/env python

"""
Central place to configure Blockbook / RICKEY endpoints and
chain codes for the orchestrator and any future modules.
"""

from typing import Dict


# Logical chain name -> Blockbook (or compatible) HTTP endpoint
BLOCKBOOK_ENDPOINTS: Dict[str, str] = {
    # Fill these with your actual endpoints, e.g.:
    # "BTC": "https://btc1.trezor.io/api",
    # "BCH": "https://bch1.trezor.io/api",
    # "LTC": "https://ltc1.trezor.io/api",
}


# Optional: map chain -> address prefix / HRP / etc. if you need it later
CHAIN_METADATA: Dict[str, dict] = {
    # "BTC": {
    #     "p2pkh_version": 0x00,
    #     "p2sh_version": 0x05,
    #     "bech32_hrp": "bc",
    # },
}
