"""
EdgeIQ Licensing Module — XSS Scanner
Handles license tier checks for premium features.
"""
import os

# ─── License Configuration ───────────────────────────────────────────────────

# License file locations (checked in order)
LICENSE_FILES = [
    os.path.expanduser("~/.config/edgeiq-licensing/license"),
    "/etc/edgeiq-license",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".license"),
]

# Upgrade URLs
UPGRADE_URLS = {
    "xss_pro": "https://buy.stripe.com/3cI14p0Lxbxr8Ec8AE7wA00",
    "network_pro": "https://buy.stripe.com/7sYaEZeCn5934nW8AE7wA01",
    "bundle": "https://buy.stripe.com/aFabJ3am79pjg6E18c7wA02",
}

PRO_UPGRADE_URL = UPGRADE_URLS["xss_pro"]
BUNDLE_UPGRADE_URL = UPGRADE_URLS["bundle"]

# ─── Tier Definitions ─────────────────────────────────────────────────────────

VALID_TIERS = {"free", "pro", "bundle", "network_pro"}


def _read_license_file() -> str:
    """Read license key from the first found license file."""
    for path in LICENSE_FILES:
        if os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    return f.read().strip().lower()
            except Exception:
                pass
    return ""


def _get_cached_tier() -> str:
    """Read cached tier from env var (set by license activation hook)."""
    return os.environ.get("EDGEIQ_LICENSE_TIER", "").lower()


def get_license_tier() -> str:
    """
    Return the current license tier: 'free', 'pro', 'bundle', or 'network_pro'.
    Cached env var takes precedence over file check.
    """
    cached = _get_cached_tier()
    if cached in VALID_TIERS:
        return cached
    file_tier = _read_license_file()
    if file_tier in VALID_TIERS:
        return file_tier
    return "free"


def is_pro() -> bool:
    """Return True if current tier is Pro or Bundle."""
    tier = get_license_tier()
    return tier in ("pro", "bundle", "network_pro")


def is_bundle() -> bool:
    """Return True if current tier is Bundle."""
    return get_license_tier() == "bundle"


def is_network_pro() -> bool:
    """Return True if current tier is Network Pro or Bundle."""
    tier = get_license_tier()
    return tier in ("network_pro", "bundle")


# ─── License Gating ───────────────────────────────────────────────────────────

LICENSE_BOX_WIDTH = 60


def require_license(tier: str, feat: str = "") -> bool:
    """
    Check if the current license tier meets the required tier.
    Prints a styled upgrade message and returns False if not licensed.
    Returns True if the license is sufficient.
    """
    if tier not in VALID_TIERS:
        tier = "pro"

    current = get_license_tier()
    upgrade_url = PRO_UPGRADE_URL
    tier_label = "Pro"

    if tier == "bundle" or tier == "network_pro":
        upgrade_url = BUNDLE_UPGRADE_URL
        tier_label = "Bundle" if tier == "bundle" else "Network Pro"

    # Sufficient tier?
    if current == tier:
        return True
    if tier in ("pro", "network_pro") and current == "bundle":
        return True
    if tier == "network_pro" and current == "pro":
        return True

    # Not licensed — print upgrade box
    feat_line = f" '{feat}'" if feat else ""
    print()
    print("╔" + "═" * LICENSE_BOX_WIDTH + "╗")
    print("║" + " ".ljust(LICENSE_BOX_WIDTH) + "║")
    print(f"║  🔒  {feat_line} requires {tier_label} license.".ljust(LICENSE_BOX_WIDTH + 1) + "║")
    print("║" + " ".ljust(LICENSE_BOX_WIDTH) + "║")
    print(f"║  Upgrade: {UPGRADE_URLS.get('xss_pro', UPGRADE_URLS['xss_pro'])}".ljust(LICENSE_BOX_WIDTH + 1) + "║")
    print("║" + " ".ljust(LICENSE_BOX_WIDTH) + "║")
    print("║  Or get everything with the Bundle:".ljust(LICENSE_BOX_WIDTH + 1) + "║")
    print(f"║  {BUNDLE_UPGRADE_URL}".ljust(LICENSE_BOX_WIDTH + 1) + "║")
    print("║" + " ".ljust(LICENSE_BOX_WIDTH) + "║")
    print("╚" + "═" * LICENSE_BOX_WIDTH + "╝")
    print()
    return False


if __name__ == "__main__":
    tier = get_license_tier()
    print(f"Current license tier: {tier}")
    print(f"is_pro(): {is_pro()}")
    print(f"is_bundle(): {is_bundle()}")
    print(f"is_network_pro(): {is_network_pro()}")
