#!/usr/bin/env python3
"""Small helpers for stable checked-in test reports."""

from __future__ import annotations

import re
from typing import Any


WINDOWS_AGENT_TRAVEL_TEMP_RE = re.compile(
    r"[A-Za-z]:\\Users\\[^\\]+\\AppData\\Local\\Temp\\agent-travel-"
    r"(?:reliability|community|ablation)-[A-Za-z0-9_-]+\\"
)
POSIX_AGENT_TRAVEL_TEMP_RE = re.compile(
    r"(?:/tmp|/var/folders/[^/]+/[^/]+/T)/agent-travel-"
    r"(?:reliability|community|ablation)-[A-Za-z0-9_-]+/"
)


def normalize_report_paths(value: Any) -> Any:
    """Replace per-run temp paths so report diffs reflect behavior, not cwd noise."""

    if isinstance(value, dict):
        return {key: normalize_report_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_report_paths(item) for item in value]
    if isinstance(value, str):
        normalized = WINDOWS_AGENT_TRAVEL_TEMP_RE.sub("<tmp>/", value)
        return POSIX_AGENT_TRAVEL_TEMP_RE.sub("<tmp>/", normalized)
    return value
