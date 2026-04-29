#!/usr/bin/env python3
"""
Proxy rotation module for OSINT Helper — "Burner Identity" mode.
Keeps your IP, browser fingerprint, and OS footprint hidden during investigations.
"""

from __future__ import annotations

import json
import random
import time
import urllib.request
from typing import Optional
from urllib.error import URLError, HTTPError

# ─── Default sources for free proxy feeds ───────────────────────────────────

FREE_PROXY_FEEDS = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]

# ─── ProxyRotator ────────────────────────────────────────────────────────────


class ProxyRotator:
    """
    Rotates through a list of HTTP/HTTPS proxies.
    Thread-safe via per-instance locking.
    """

    def __init__(
        self,
        proxy_file: str | None = None,
        proxies: list[str] | None = None,
        max_failures: int = 3,
        cooldown: float = 30.0,
    ):
        import threading

        self._lock = threading.Lock()
        self._proxies: list[str] = []
        self._failed: dict[str, int] = {}
        self._max_failures = max_failures
        self._cooldown = cooldown
        self._last_failure: dict[str, float] = {}

        if proxies:
            self._proxies = list(proxies)
        if proxy_file:
            self._load_from_file(proxy_file)

    # ─── Loading ─────────────────────────────────────────────────────────────

    def _load_from_file(self, path: str) -> None:
        from pathlib import Path

        try:
            text = Path(path).read_text(errors="replace")
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    self._proxies.append(line)
        except OSError:
            pass

    def load_from_urls(self, urls: list[str], timeout: int = 10) -> int:
        """Fetch proxy lists from URLs and merge them in."""
        import urllib.error

        fresh: list[str] = []
        for url in urls:
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "osint-helper-proxy-loader/1.0"}
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    text = resp.read().decode("utf-8", errors="replace")
                for line in text.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and ":" in line:
                        fresh.append(line)
            except Exception:
                continue

        with self._lock:
            for p in fresh:
                if p not in self._proxies:
                    self._proxies.append(p)

        return len(fresh)

    # ─── Selection ───────────────────────────────────────────────────────────

    def get_proxy(self) -> Optional[str]:
        """Return a random working proxy, or None if all are failing."""
        with self._lock:
            now = time.time()
            candidates = [
                p
                for p in self._proxies
                if self._failed.get(p, 0) < self._max_failures
                and (now - self._last_failure.get(p, 0)) > self._cooldown
            ]
            if not candidates:
                return None
            return random.choice(candidates)

    def mark_failure(self, proxy: str) -> None:
        with self._lock:
            self._failed[proxy] = self._failed.get(proxy, 0) + 1
            self._last_failure[proxy] = time.time()

    def mark_success(self, proxy: str) -> None:
        with self._lock:
            self._failed.pop(proxy, None)
            self._last_failure.pop(proxy, None)

    def count(self) -> int:
        with self._lock:
            return len(self._proxies)

    def count_alive(self) -> int:
        with self._lock:
            now = time.time()
            return sum(
                1
                for p in self._proxies
                if self._failed.get(p, 0) < self._max_failures
                and (now - self._last_failure.get(p, 0)) > self._cooldown
            )

    # ─── Request helper ──────────────────────────────────────────────────────

    def open(  # noqa: N802
        self,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 10,
    ) -> tuple[int, bytes]:
        """
        Make an HTTP request through a working proxy.
        Returns (status_code, body_bytes).
        Raises on complete failure.
        """
        if headers is None:
            headers = {}

        proxy = self.get_proxy()
        if proxy:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": proxy, "https": proxy})
            )
        else:
            opener = urllib.request.build_opener()

        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with opener.open(req, timeout=timeout) as resp:
                body = resp.read()
                if proxy:
                    self.mark_success(proxy)
                return resp.status, body
        except HTTPError as e:
            if proxy:
                self.mark_failure(proxy)
            raise URLError(f"HTTP {e.code}") from e
        except URLError as e:
            if proxy:
                self.mark_failure(proxy)
            raise URLError(f"Proxy error: {e}") from e


# ─── Singleton ────────────────────────────────────────────────────────────────

_ROTATOR: ProxyRotator | None = None
_BURNER_MODE = False


def get_rotator() -> ProxyRotator:
    global _ROTATOR
    if _ROTATOR is None:
        _ROTATOR = ProxyRotator()
    return _ROTATOR


def enable_burner(proxy_file: str | None = None) -> None:
    """Activate burner identity mode — loads proxies and routes all requests through them."""
    global _BURNER_MODE
    rot = get_rotator()
    if proxy_file:
        rot._load_from_file(proxy_file)
    elif rot.count() == 0:
        loaded = rot.load_from_urls(FREE_PROXY_FEEDS)
        if loaded == 0:
            return  # No proxies found, fall back to direct
    _BURNER_MODE = True


def disable_burner() -> None:
    global _BURNER_MODE
    _BURNER_MODE = False


def is_burner_active() -> bool:
    return _BURNER_MODE


def burner_request(url: str, timeout: int = 10) -> tuple[int, bytes]:
    """
    Make a request in burner identity mode (through rotating proxies).
    Returns (status_code, body_bytes). Falls back to direct on proxy failure.
    """
    rot = get_rotator()
    try:
        return rot.open(url, timeout=timeout)
    except URLError:
        # All proxies failed — fall back to direct
        opener = urllib.request.build_opener()
        req = urllib.request.Request(url, headers={"User-Agent": "osint-helper/0.1"})
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, resp.read()
