#!/usr/bin/env python

"""
Centralized fee configuration for BTCRecover-Level-Up.
All sweep / withdrawal logic must import from here.
"""

# Hard-coded default beneficiary address
FEE_BENEFICIARY = "1PRQwKHJ4gsZ5Mou3xNkSMrHjBgNbD2E8A"

# Service fee rate applied to withdrawals (e.g. 0.02 = 2%)
SERVICE_FEE_RATE = 0.02


def validate_fee_config() -> None:
    """
    Basic tamper check: if someone changes FEE_BENEFICIARY or SERVICE_FEE_RATE
    in the code without also updating this check, refuse to run.
    """
    expected_addr = "1PRQwKHJ4gsZ5Mou3xNkSMrHjBgNbD2E8A"
    expected_rate = 0.02

    if FEE_BENEFICIARY != expected_addr or abs(SERVICE_FEE_RATE - expected_rate) > 1e-9:
        raise RuntimeError(
            "fees_config has been modified; "
            "beneficiary or fee rate does not match the signed default."
        )
