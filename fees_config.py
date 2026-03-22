#!/usr/bin/env python

"""
Centralized fee configuration for BTCRecover-Level-Up.
All sweep / withdrawal logic must import from here.
"""

import hashlib

# Hard-coded default beneficiary address
FEE_BENEFICIARY = "1PRQwKHJ4gsZ5Mou3xNkSMrHjBgNbD2E8A"

# Service fee rate applied to withdrawals (e.g. 0.02 = 2%)
SERVICE_FEE_RATE = 0.02

# Simple integrity tag so casual edits break things
_FEE_TAG = "levelup:" + hashlib.sha256(
    (FEE_BENEFICIARY + ":" + str(SERVICE_FEE_RATE)).encode("utf-8")
).hexdigest()[:16]


def validate_fee_config() -> None:
    """
    Tamper check: verify address, rate, and checksum all align.
    """
    expected_addr = "1PRQwKHJ4gsZ5Mou3xNkSMrHjBgNbD2E8A"
    expected_rate = 0.02

    expected_tag = "levelup:" + hashlib.sha256(
        (expected_addr + ":" + str(expected_rate)).encode("utf-8")
    ).hexdigest()[:16]

    if (
        FEE_BENEFICIARY != expected_addr
        or abs(SERVICE_FEE_RATE - expected_rate) > 1e-9
        or _FEE_TAG != expected_tag
    ):
        raise RuntimeError(
            "BTCRecover-Level-Up fee configuration has been modified. "
            "This build is not trusted."
        )
