#!/usr/bin/env python

"""
Minimal WIF recovery pipeline for BTCRecover-Level-Up.

Flow:
  - Take a WIF (already recovered by btcrecover or found by orchestrator).
  - Build a WIFWallet for it.
  - Query Blockbook for balances.
  - Wrap into a RecoveryEvent + BalanceResult-like structures.
  - Call ownership_flow_with_fee(event, balances).
"""

from dataclasses import dataclass, field
from typing import Any, List

from blockbook_balance import get_balances_for_addresses
from blockbook_config import BLOCKBOOK_ENDPOINTS
from ownership_with_fee import ownership_flow_with_fee
from wif_wallet import WIFWallet


@dataclass
class AddressInfo:
    address: str
    balance_sats: int
    utxos: List[dict] = field(default_factory=list)


@dataclass
class ChainBalance:
    chain: str
    total_balance_sats: int
    addresses: List[AddressInfo] = field(default_factory=list)


@dataclass
class BalanceResult:
    chains: List[ChainBalance] = field(default_factory=list)

    @property
    def total_balance_sats(self) -> int:
        return sum(c.total_balance_sats for c in self.chains)


@dataclass
class Candidate:
    kind: str
    source: str
    key_material: str


@dataclass
class RecoveryEvent:
    key_material: str
    wallet: Any
    password: str
    candidate: Candidate


def _build_balances_for_wif(wallet: WIFWallet) -> BalanceResult:
    if "BTC" not in BLOCKBOOK_ENDPOINTS:
        raise RuntimeError("BLOCKBOOK_ENDPOINTS['BTC'] not configured")

    addrs = wallet.get_all_addresses()
    raw = get_balances_for_addresses("BTC", addrs)

    addr_infos: List[AddressInfo] = []
    for a in raw.get("addresses", []):
        bal = int(a.get("balance_sats", a.get("balance", "0")))
        utxos = a.get("raw", {}).get("utxo", [])
        addr_infos.append(AddressInfo(address=a["address"], balance_sats=bal, utxos=utxos))

    total = sum(ai.balance_sats for ai in addr_infos)
    chain_bal = ChainBalance(chain="BTC", total_balance_sats=total, addresses=addr_infos)

    return BalanceResult(chains=[chain_bal])


def run_wif_recovery_pipeline(wif: str, password_label: str = "") -> None:
    """
    Run the full Level-Up pipeline for a single WIF key.
    password_label: optional label if this came from a recovered password.
    """
    wallet = WIFWallet(wif)
    candidate = Candidate(kind="wif", source="manual", key_material=wif)
    event = RecoveryEvent(
        key_material=wif,
        wallet=wallet,
        password=password_label or wif,
        candidate=candidate,
    )

    balances = _build_balances_for_wif(wallet)

    if not balances.total_balance_sats:
        print("[*] No BTC balance found for this WIF.")
        return

    ownership_flow_with_fee(event, balances)
