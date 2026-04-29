# EdgeIQ XSS Scanner

**Version:** `1.2.0`  
**Skill Name:** `xss-scanner`  
**Category:** Security / Offensive / Auditing  
**Author:** EdgeIQ Labs  
**License:** Defensive Use Only  
**OpenClaw Compatible:** Yes — Python 3, pure stdlib, WSL + Windows + macOS

---

## What It Does

Professional-grade XSS vulnerability scanner for authorized security auditing. Scans web applications for **reflected XSS**, **DOM-based XSS**, **stored/persistent XSS** (via blind callback), and **WAF-bypass variants**. Designed for penetration testers, bug bounty researchers, and security teams with explicit written authorization.

> ⚠️ **Legal Notice:** Only scan targets you own or have explicit written permission to audit. Unauthorized scanning is illegal and strictly prohibited. This tool is for **defensive security professionals**.

---

## Pricing

| Feature | Lifetime ($39) | Optional Monthly ($7/mo) |
|---------|:--------:|:----------------------:|
| All scanner features | ✅ | ✅ |
| Blind XSS detection | ✅ | ✅ |
| Screenshot evidence capture | ✅ | ✅ |
| HTML report export | ✅ | ✅ |
| Reflected params deep analysis | ✅ | ✅ |
| Scheduled recurring scans | ✅ | ✅ |
| Alert delivery (Discord/Telegram/Email) | ✅ | ✅ |
| Priority support | ✅ | ✅ |
| Core reflected XSS scan (40+ payloads) | ✅ | ✅ |
| Crawl mode + BFS depth | ✅ | ✅ |
| JSON report export | ✅ | ✅ |
| HTTP security header analysis | ✅ | ✅ |
| WAF detection + auto-bypass | ✅ | ✅ |
| Custom headers, cookies, auth | ✅ | ✅ |
| Proxy support | ✅ | ✅ |
| Rate limiting control | ✅ | ✅ |
| `--quiet` mode + exit codes | ✅ | ✅ |

**Lifetime License: $39** — your tool forever, all Pro features included permanently.

**Optional Monthly: $7/mo** — for those who prefer recurring billing (cancel anytime).

👉 [Buy Lifetime — $39](https://buy.stripe.com/14AfZjcuf30V8Ec4ko7wA0O)
👉 [Subscribe Monthly — $7/mo](https://buy.stripe.com/00w28t2TF30V5s0eZ27wA15)
👉 [Subscribe Monthly — $7/mo](https://buy.stripe.com/00w28t2TF30V5s0eZ27wA15)

---

## Feature Tiers at a Glance

| Feature | Free | **Lifetime ($39)** |
|---------|:----:|:--------:|
| Core reflected XSS scan (40+ payloads) | ✅ | ✅ |
| Crawl mode + BFS depth | ✅ | ✅ |
| JSON report export | ✅ | ✅ |
| HTTP security header analysis | ✅ | ✅ |
| WAF detection + auto-bypass | ✅ | ✅ |
| Custom headers, cookies, auth | ✅ | ✅ |
| Proxy support | ✅ | ✅ |
| Rate limiting control | ✅ | ✅ |
| `--quiet` mode + exit codes | ✅ | ✅ |
| **Blind XSS detection** (`--blind-callback`) | ❌ | ✅ |
| **Screenshot evidence capture** (`--screenshot-dir`) | ❌ | ✅ |
| **HTML report export** (`--format html`) | ❌ | ✅ |
| Reflected params deep analysis | ❌ | ✅ |
| Scheduled recurring scans | ❌ | ✅ |
| Alert delivery (Discord/Telegram/Email) | ❌ | ✅ |
| Priority support | ❌ | ✅ |

> **All Pro features are now included in the Lifetime License.** The Lifetime purchase gives you permanent access to everything previously locked behind Pro/Bundle tiers.

---

## What's New in v2

| Feature | Free | **Lifetime ($39)** |
|---------|------|-----|
| Core reflected XSS scan | ✅ | ✅ |
| 40+ payloads (incl. WAF bypass) | ✅ | ✅ |
| 7 injection context modes | ✅ | ✅ |
| Crawl mode with BFS depth | ✅ | ✅ |
| JSON + HTML report export | ✅ | ✅ |
| HTTP security header analysis (CSP, XFO, HSTS…) | ✅ | ✅ |
| WAF detection + auto-bypass payload switching | ✅ | ✅ |
| Custom headers, cookies, auth | ✅ | ✅ |
| Proxy support (stealth scanning) | ✅ | ✅ |
| Rate limiting control | ✅ | ✅ |
| Blind XSS detection (callback mode) | ❌ | ✅ |
| Reflected params analysis | ❌ | ✅ |
| Screenshot evidence capture | ❌ | ✅ |
| `--quiet` mode + exit codes (CI/CD) | ✅ | ✅ |
| Scheduled recurring scans | ❌ | ✅ |
| Alert delivery (Discord / Telegram / Email) | ❌ | ✅ |
| Priority support | ❌ | ✅ |

---

## Installation

```bash
# Standalone usage
python3 /home/guy/.openclaw/workspace/apps/xss-scanner/scanner.py <target>

# As OpenClaw command (in any channel):
!xss https://example.com
!xss https://example.com --depth 3 --workers 20
```

---

## Quick Start

### Basic Scan
```bash
python3 scanner.py https://example.com
```

### Verbose / Full Crawl
```bash
python3 scanner.py https://example.com --depth 2 --max-urls 30
```

### With Proxy (Burp Suite / OWASP ZAP)
```bash
python3 scanner.py https://example.com --proxy http://127.0.0.1:8080 --quiet
```

### Authenticated Scan
```bash
python3 scanner.py https://example.com --auth admin:secret --cookies "session=abc123"
```

### Blind XSS (stored/persistent XSS detection)
```bash
python3 scanner.py https://example.com --blind-callback https://your-callback.com/log
```

### Security Headers Audit
```bash
python3 scanner.py https://example.com --analyze-headers --format json --out report.json
```

### Export HTML Report
```bash
python3 scanner.py https://example.com --format html --out xss-report.html
```

### Automation / CI-CD (exit codes + quiet mode)
```bash
python3 scanner.py https://example.com --quiet --format json -o result.json
echo "Exit code: $?"   # 0=safe, 1=vulns found, 2=error, 3=interrupted
```

---

## Command Reference

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `url` | Target URL (auto-adds https:// if missing) |

### Core Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--depth` | int | 2 | Crawl depth (BFS link discovery) |
| `--max-urls` | int | 20 | Maximum URLs to scan before stopping |
| `--workers` | int | 15 | Concurrent threads for payload testing |
| `--format` | choice | discord | Output format: `discord`, `json`, `html`, `simple` |
| `--follow-external` | flag | False | Follow links to external domains |
| `--quiet`, `-q` | flag | False | Suppress progress output |
| `--out`, `-o` | path | — | Write output to file |

### Network Options

| Flag | Type | Description |
|------|------|-------------|
| `--proxy` | URL | HTTP/S proxy (e.g. `http://127.0.0.1:8080` for Burp/ZAP) |
| `--user-agent` | string | Custom User-Agent string |
| `--auth` | user:pass | Basic HTTP authentication |
| `--cookies` | string | Cookie string (`name=value; name2=value2`) |
| `--custom-header` | HDR | Add custom header (`Name: value`) — repeatable |
| `--timeout` | float | Request timeout in seconds (default: 15) |
| `--rate-limit` | float | Minimum seconds between requests (anti-rate-limit) |

### Advanced Options

| Flag | Type | Description |
|------|------|-------------|
| `--blind-callback` | URL | Blind XSS callback URL for stored XSS detection |
| `--analyze-headers` | flag | Analyze HTTP security headers (CSP, X-Frame-Options, HSTS…) |
| `--reflected-only` | flag | Map reflected params without sending payloads |
| `--screenshot-dir` | path | Directory for evidence HTML files (default: `/tmp/xss-screenshots`) |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Scan complete — no vulnerabilities found |
| `1` | Scan complete — vulnerabilities detected |
| `2` | Scan error — target unreachable or connection failed |
| `3` | Interrupted — SIGINT/SIGTERM received |

---

## Payload Context Detection

The scanner automatically detects the **injection context** of each reflection and assigns severity accordingly:

| Context | Triggered When | Severity | Example |
|---------|---------------|----------|---------|
| `js_string` | Payload inside `<script>` or JS string | **Critical** | `<script>alert(1)</script>` |
| `event_handler` | Payload inside `on*` attribute | **Critical** | `onerror=alert(1)` |
| `html_attr` | Payload inside HTML attribute | **High** | `" onmouseover=alert(1) x="` |
| `dom` | DOM mutation / innerHTML injection | **High** | DOM clobbering vectors |
| `html_body` | Plain text reflection in HTML | **Medium** | `<script>alert(1)</script>` |
| `comment` | Inside HTML comment `<!-- -->` | **Medium** | `--><script>alert(1)</script>` |
| `css` | Inside `<style>` tag | **Medium** | Style-based injection |
| `url_param` | URL-encoded param in URL | **Low** | `?q=<script>alert(1)</script>` |

---

## WAF Detection & Bypass

Automatically detects these WAFs and switches to bypass payloads:

- Cloudflare, AWS CloudFront, Akamai, Imperva
- Fortinet, Sucuri, F5 BIG-IP ASM, Barracuda
- DenyAll, Cisco ACE, dotDefender, Google Armr

**Bypass payloads activated automatically** when WAF block patterns are detected:
- Case mutation: `<ScRipT>`, `<IMG SRC=x ONERROR=...>`
- Unicode escape: `<script>\u0061lert(1)</script>`
- Protocol-less: `//evil.com/x.js`

---

## Security Header Analysis

When `--analyze-headers` is used, reports on:

| Header | What It Checks |
|--------|---------------|
| `Content-Security-Policy` | `unsafe-inline` / `unsafe-eval` present? |
| `X-Frame-Options` | Clickjacking protection (`DENY` / `SAMEORIGIN`) |
| `X-Content-Type-Options` | MIME-sniffing disabled (`nosniff`) |
| `Strict-Transport-Security` | HTTPS enforcement |
| `Referrer-Policy` | Referrer leakage |
| `X-XSS-Protection` | Legacy XSS filter (often disabled intentionally) |
| `Permissions-Policy` | Browser feature restrictions |

---

## Output Formats

### Discord (default)
Rich embed with severity breakdown, grouped by critical/high/medium/low. Clean formatting for Discord channels.

### JSON (machine-readable)
Full structured report for CI/CD pipelines, includes:
- Scan stats + metadata
- All vulnerabilities with severity, evidence, timestamp
- Security header findings
- WAF detection results
- Reflected parameter map

### HTML (shareable report)
Self-contained styled HTML file — dark theme, sortable vulnerability table, header findings, WAF info. Ready to share with clients or include in pentest deliverables.

### Simple (console)
One-line-per-finding format. Good for grep/parsing.

---

## Discord Command Usage

In any OpenClaw Discord channel:

```
!xss https://example.com
!xss https://example.com --depth 3 --max-urls 50 --workers 20
!xss https://example.com --follow-external --format json -o report.json
!xss https://example.com --proxy http://127.0.0.1:8080 --quiet
!xss https://example.com --blind-callback https://your-domain.com/log
!xss https://example.com --analyze-headers --format html -o report.html
```

---

## Free vs Pro

### Free (v1) — Included
Full-featured scanner for manual authorized auditing. Everything in this SKILL.md except the Pro-only items.

### Pro ($19/mo)
- Blind XSS detection with persistent callback monitoring
- Scheduled recurring scans (cron-based)
- Alert delivery to Discord, Telegram, or Email
- Screenshot evidence capture
- Reflected params deep analysis
- Priority onboarding and support

### Network Pro ($29/mo) *(deprecated)*
All features included in Lifetime purchase above.

### Bundle ($39/mo) *(deprecated)*
All features now included in Lifetime purchase above.

### Upgrade Links

| Tier | Link |
|------|------|
| **$39** | [$39](https://buy.stripe.com/14AfZjcuf30V8Ec4ko7wA0O) |
| **Monthly ($7/mo)** | [$7/mo](https://buy.stripe.com/00w28t2TF30V5s0eZ27wA15) |
| **$7/mo** | [$7/mo](https://buy.stripe.com/00w28t2TF30V5s0eZ27wA15) |

**Contact:** gpalmieri21@gmail.com

---

## Architecture

| Component | Detail |
|-----------|--------|
| **Language** | Python 3 (pure stdlib — no external dependencies) |
| **Concurrency** | `concurrent.futures.ThreadPoolExecutor` for parallel payload testing |
| **Crawl Strategy** | BFS with configurable depth, URL dedup, external-link filtering |
| **HTTP Client** | Custom `HTTPClient` class with proxy, auth, cookie, custom-header support |
| **WAF Detection** | Pattern-matching on response body + headers against 15+ WAF signatures |
| **Context Detection** | Regex + HTML parser across 8 injection contexts |
| **Payload Library** | 40+ payloads across script injection, event handlers, attribute injection, URL injection, context breakers, mution/mull-byte bypass, Unicode, DOM clobbering |
| **Supported OS** | Linux/WSL, Windows, macOS |
| **Exit Codes** | Full automation support (0/1/2/3) |

---

## Legal & Ethical Use

**This tool is for:**
- Security researchers auditing authorized bug bounty targets
- Penetration testers assessing client applications under contract
- Developers testing their own applications
- Defensive security teams auditing internal infrastructure
- Capture The Flag (CTF) participants in authorized labs

**This tool must NOT be used:**
- Against targets without explicit written permission
- On production systems without authorization
- For any unauthorized access, enumeration, or exploitation
- In any jurisdiction where automated vulnerability scanning is restricted

---

## Support

- **Email:** gpalmieri21@gmail.com
- **Discord:** https://discord.gg/aPhSnrU9
- **Site:** https://edgeiqlabs.com


---

## 🔗 More from EdgeIQ Labs

**edgeiqlabs.com** — Security tools, OSINT utilities, and micro-SaaS products for developers and security professionals.

- 🛠️ **Subdomain Hunter** — Passive subdomain enumeration via Certificate Transparency
- 📸 **Screenshot API** — URL-to-screenshot API for developers
- 🔔 **uptime.check** — URL uptime monitoring with alerts
- 🛡️ **headers.check** — HTTP security headers analyzer

👉 [Visit edgeiqlabs.com →](https://edgeiqlabs.com)
