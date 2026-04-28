"""
EdgeIQ Licensing — Pro/Bundle tier gating for Network Scanner.
Determines feature access based on license tier.
"""
from typing import Literal

# ─── Stripe Upgrade URLs ───────────────────────────────────────────────────────
PRO_URL   = "https://buy.stripe.com/7sYaEZeCn5934nW8AE7wA01"
BUNDLE_URL = "https://buy.stripe.com/aFabJ3am79pjg6E18c7wA02"

# ─── License Tier ─────────────────────────────────────────────────────────────
# TODO: Replace with real license-key validation (env var, file, API call, etc.)
# For now, all tiers default to False (all features gated until a license is activated).

LICENSE_TIER = "free"  # "free" | "pro" | "bundle"


def is_pro() -> bool:
    """True when the active license is Pro or Bundle."""
    return LICENSE_TIER in ("pro", "bundle")


def is_bundle() -> bool:
    """True when the active license is Bundle."""
    return LICENSE_TIER == "bundle"


def _tier_weight(tier: str) -> int:
    weights = {"free": 0, "pro": 1, "bundle": 2}
    return weights.get(tier, 0)


def require_license(
    tier: Literal["pro", "bundle"],
    feature_name: str,
) -> bool:
    """
    Check if the current license meets `tier`.
    Prints a styled upgrade prompt and returns False if not authorized.
    Returns True if access is granted.
    """
    required_weight = _tier_weight(tier)
    current_weight  = _tier_weight(LICENSE_TIER)

    if current_weight >= required_weight:
        return True

    url = PRO_URL if tier == "pro" else BUNDLE_URL

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              🔒  EdgeIQ License Required  🔒              ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  ✖  Feature: {feature_name:<46} ║")
    print(f"║  ✖  Required: {tier.upper():<46} ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Upgrade to unlock this feature and support EdgeIQ Labs!  ║")
    print(f"║  → {url:<53} ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    return False
