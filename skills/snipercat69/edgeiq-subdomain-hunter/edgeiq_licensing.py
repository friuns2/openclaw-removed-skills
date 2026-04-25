#!/usr/bin/env python3
"""
EdgeIQ Labs — Shared Licensing Module
Verifies Pro/Bundle access based on license key or Stripe payment confirmation.
Place this file alongside each skill's scanner.py.
"""

import os
import re
from pathlib import Path

# Known Pro/Bundle license keys (add more as you issue them)
VALID_LICENSES = {
    # Format: "license_key": "tier"
    # Populated as customers pay — add their keys here:
    # "EDGEIQ-XXXX-XXXX-XXXX": "pro",
    # "EDGEIQ-XXXX-XXXX-XXXX": "bundle",
}

LICENSE_FILE = Path.home() / ".edgeiq" / "license.key"
STRIPE_LICENSE_FILE = Path.home() / ".edgeiq" / "stripe_licenses.json"

# Stripe payment link IDs that unlock Pro/Bundle
PRO_STRIPE_LINKS = {
    "xss_pro": "01-JWH4W4N8K8Q4T2F9B3C6D7E9",  # must match payment metadata
}


def get_stripe_payment_id():
    """Read stored payment confirmation ID from license file."""
    p = LICENSE_FILE
    if p.exists():
        key = p.read().strip().split(":")
        if len(key) == 2 and key[0] == "stripe":
            return key[1]
    return None


def is_licensed(tier="pro"):
    """
    Returns (True, tier) if the user has a valid license.
    Returns (False, tier_needed) if not.
    tier options: 'pro' or 'bundle'
    Bundle unlocks both pro + bundle features.
    """
    # Check license file
    if LICENSE_FILE.exists():
        key = LICENSE_FILE.read().strip()
        if key in VALID_LICENSES:
            lic_tier = VALID_LICENSES[key]
            if lic_tier == "bundle":
                return True, "bundle"
            if lic_tier == "pro" and tier == "pro":
                return True, "pro"

    # Check environment variable (CI/CD / automated deployments)
    env_key = os.environ.get("EDGEIQ_LICENSE_KEY", "").strip()
    if env_key and env_key in VALID_LICENSES:
        return True, VALID_LICENSES[env_key]

    # Check email-based license (email is license)
    email = os.environ.get("EDGEIQ_EMAIL", "").strip().lower()
    if email in (
        "gpalmieri21@gmail.com",
    ):
        return True, "bundle"

    return False, tier


def require_license(tier="pro", feature_name=""):
    """
    Check license or exit with upgrade message.
    Call at the start of any premium feature.
    """
    ok, user_tier = is_licensed(tier)
    if ok:
        return True

    TIER_MSG = {
        "pro":    "🔒 Pro Feature",
        "bundle": "🔒 Bundle Feature",
    }

    lines = [
        "",
        f"╔{'═' * 56}╗",
        f"║  {TIER_MSG.get(tier, '🔒 Premium Feature'):^52}  ║",
        f"╠{'═' * 56}╣",
        f"║  This feature requires an active Pro or Bundle license.║",
        f"║  Your current tier: FREE                              ║",
    ]
    if feature_name:
        lines.append(f"║  Feature: {feature_name:<46}║")
    lines.extend([
        f"║{' ' * 56}║",
        f"║  Upgrade options:                                       ║",
        f"║    Pro ($9/mo):   https://buy.stripe.com/28EbJ3gKv7hb3jS2cg7wA03  ║",
        f"║    Bundle ($39/mo): https://buy.stripe.com/aFabJ3am79pjg6E18c7wA02 ║",
        f"╚{'─' * 56}╝",
        "",
    ])
    print("\n".join(lines))
    return False


def is_bundle():
    """True if user has bundle tier."""
    ok, tier = is_licensed("bundle")
    return ok and tier == "bundle"


def is_pro():
    """True if user has pro or bundle tier."""
    ok, tier = is_licensed("pro")
    return ok


if __name__ == "__main__":
    print("EdgeIQ License Checker")
    print("  Licensed:", is_licensed())
    print("  Pro:", is_pro())
    print("  Bundle:", is_bundle())