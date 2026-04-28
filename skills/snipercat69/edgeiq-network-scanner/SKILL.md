# Network Scanner — EdgeIQ Professional

**Version:** `1.2.0`  
**Skill Name:** `network-scanner`  
**Category:** Security / Reconnaissance  
**Tiers:** Free v1 | **Lifetime: $49** / Optional Monthly: $10/mo  
**Author:** EdgeIQ Labs  
**OpenClaw Compatible:** Yes — Python 3, pure stdlib, WSL + Windows

---

## What It Does

Professional-grade network reconnaissance: host discovery, full-spectrum port scanning, service fingerprinting, CVE matching, SSL/TLS analysis, traceroute, subdomain enumeration, and vulnerability classification — **without nmap**. Pure Python sockets, works on WSL/Linux and Windows.

Designed for **authorized security auditing of networks you own or have explicit written permission to scan**.

> ⚠️ **Legal Notice:** Only scan networks you own or have explicit written permission to audit. Unauthorized scanning is illegal. This tool is for defensive security professionals, penetration testers, and network administrators.

---

## Features

### Core Capabilities
- **Host Discovery** — ICMP ping + TCP connect probe (works through firewalls)
- **Port Scanning** — Full spectrum: quick (9) / normal (20) / intense (100) / full (1–1024) / deep (1–65535)
- **Service Banner Grabbing** — Identify services and exact version strings from open ports
- **HTTP/HTTPS Fingerprinting** — Server detection, tech stack identification (WordPress, IIS, nginx, etc.), title grabbing, redirect following
- **SSL/TLS Security Grading** — Certificate analysis, protocol detection, cipher inspection, grade assignment (A–F)
- **OS Fingerprinting** — TTL + window size + open-port pattern heuristics (Linux/Windows/BSD/macOS detection)
- **CVE Matching** — Local database of 40+ CVEs for common services (Apache, nginx, OpenSSH, MySQL, PostgreSQL, Redis, SMB, OpenSSL, MSSQL, VNC, RDP, DNS, SMTP, telnet, MongoDB, etc.)
- **Vulnerability Classification** — Each open port tagged CRITICAL / HIGH / MEDIUM / LOW / NONE
- **Subdomain Enumeration** — DNS lookup of 35+ common subdomain prefixes against discovered hosts
- **Traceroute** — Network path analysis with per-hop RTT (Linux `traceroute`, Windows fallback)
- **Pure Python** — Zero external dependencies (cryptography optional, degrades gracefully)
- **Cross-Platform** — WSL/Linux + Windows + macOS
- **Concurrent Scanning** — Multi-threaded ThreadPoolExecutor (configurable up to 150 workers)

### Operational Features
- **Rate Limiting** — `--rate-delay` for stealth/stealth scanning (e.g. `--rate-delay 0.05`)
- **Proxy Support** — HTTP/SOCKS proxy via `--proxy socks5://host:port`
- **Signal Handling** — Graceful Ctrl+C (finishes current hosts, then exits cleanly)
- **Quiet/Automation Mode** — `--quiet` suppresses progress, exit codes for CI/CD:
  - `0` = clean scan, no high-risk findings
  - `2` = interrupted
  - `3` = CRITICAL CVE found
  - `4` = HIGH CVE found
- **Custom Port Range** — `--port-range 1-10000` or `--port-range 1-65535`
- **Output Formats** — Discord (emoji-rich), Simple (CLI), JSON (machine-readable), HTML (polished report)
- **File Export** — `--output report.html` / `--output scan.json`

---

## Installation

```bash
# Direct run
python3 /home/guy/.openclaw/workspace/apps/network-scanner/scanner.py

# As OpenClaw skill — copy into skills folder
cp -r /home/guy/.openclaw/workspace/apps/network-scanner ~/.openclaw/skills/network-scanner

# Optional: make it executable
chmod +x /home/guy/.openclaw/workspace/apps/network-scanner/scanner.py
```

---

## Scan Depth Tiers

| Depth | Ports Scanned | Best For |
|-------|--------------|----------|
| `quick` | 9 | Fast local discovery |
| `normal` | 20 | General reconnaissance |
| `intense` | 100 | Full vulnerability assessment |
| `full` | 1–1024 | Complete well-known port sweep |
| `deep` | 1–65535 | Full spectrum (slow, loud) |

---

## Usage Examples

### Basic Scans
```bash
# Quick local scan
python3 scanner.py 192.168.1.0/24 quick

# Normal scan
python3 scanner.py 10.5.1.1 normal

# Intense scan with traceroute + subdomains
python3 scanner.py 10.5.1.1 intense --traceroute --subdomains

# Full well-known port scan (1–1024)
python3 scanner.py 192.168.1.1 full

# Full 65k port deep scan
python3 scanner.py 192.168.1.1 deep

# Custom port range
python3 scanner.py 10.5.1.1 custom --port-range 1-10000
```

### Advanced Features
```bash
# Slow/stealth scan with rate limiting
python3 scanner.py 192.168.1.0/24 normal --rate-delay 0.05 --workers 50

# High-concurrency scan (150 workers)
python3 scanner.py 10.0.0.1 intense --workers 150 --timeout 1.0

# Traceroute + subdomains + SSL analysis
python3 scanner.py target.example.com full --traceroute --subdomains

# Export JSON for automation
python3 scanner.py 192.168.1.1 intense --format json --output scan.json

# Export HTML report
python3 scanner.py 192.168.1.1 intense --format html --output report.html

# Local network discovery
python3 scanner.py --local-scan normal

# Full subnet local scan
python3 scanner.py --local full
```

### As Discord Command
In `#net-scan` channel:
```
!net 192.168.1.0/24 quick
!net 10.5.1.1 intense --traceroute --subdomains
!net scanme.nmap.org full
!net local quick
!net example.com full --format html
```

---

## Output Format Examples

### Discord Format
```
🔍 EdgeIQ Scan Report — `192.168.1.1`
Mode: `intense` | Risk: 🟠 HIGH | Duration: `12.3s`

🟢 192.168.1.1 — server.example.com `2.1ms` | 5 ports | HIGH
   └ OS: `Linux/Unix (TTL≈64); Linux/Unix Server`
   └ Subdomains: `www.example.com`, `mail.example.com`
   └ Route: → 192.168.1.1
   80    http          Apache/2.4.41 🟠 HIGH — Apache path traversal
 443    https         nginx/1.18.0 [SSL: B] — Self-signed certificate
  22    ssh           OpenSSH_8.0 MEDIUM — User enumeration via timing
3306    mysql         MySQL/5.7.29 🔴 CRITICAL — Auth bypass (CVE-2012-2122)

─── Stats: 1 hosts | 100 ports scanned | 2 errors
```

### JSON Output
```json
{
  "target": "192.168.1.1",
  "scan_type": "intense",
  "timestamp": "2026-04-22 14:38:00",
  "duration_s": 12.3,
  "hosts": [{
    "ip": "192.168.1.1",
    "hostname": "server.example.com",
    "is_alive": true,
    "rtt_ms": 2.1,
    "ttl": 64,
    "os_guess": "Linux/Unix (TTL≈64)",
    "ports": {
      "80": {
        "port": 80, "state": "open", "service": "http",
        "version": "Apache/2.4.41",
        "banner": "Apache/2.4.41 (Ubuntu)",
        "cves": [{"cve": "CVE-2017-15710", "level": "MEDIUM", ...}],
        "vuln_level": "HIGH",
        "http_fingerprint": {"server": "Apache/2.4.41", "tech_stack": ["PHP", "WordPress"]}
      }
    }
  }]
}
```

---

## Tier Comparison

| Feature | Free (v1) | **Lifetime ($49)** | Optional Monthly ($10/mo) |
|---------|-----------|----------------|----------------------|
| Port depth | 1–1024 | Full (1–65535) | Full (1–65535) |
| CVE database | Local (~40 entries) | Full (~500 entries) | Full (~500 entries) |
| Traceroute | ❌ | ✅ | ✅ |
| Subdomain enum | ❌ | ✅ | ✅ |
| Output: HTML report | ❌ | ✅ | ✅ |
| Output: JSON report | ✅ | ✅ | ✅ |
| Output: Discord/Simple | ✅ | ✅ | ✅ |
| Scheduled scans | ❌ | ✅ | ✅ |
| Delta comparison | ❌ | ✅ | ✅ |
| Alert delivery | ❌ | ✅ | ✅ |
| Proxy support | ❌ | ✅ | ✅ |
| Rate limiting | ✅ | ✅ | ✅ |
| File export | ❌ | ✅ | ✅ |
| Support | Community | Priority | Priority |

---

## CVE Coverage

Current local database includes (partial list):

| Service | CVEs Matched |
|---------|-------------|
| Apache httpd | CVE-2024-27316, CVE-2022-31813, CVE-2017-15710 |
| nginx | CVE-2021-23017, CVE-2019-9511/9513/9516, CVE-2013-2028 |
| OpenSSH | CVE-2020-15778, CVE-2018-15473, CVE-2019-6109, CVE-2019-6111 |
| MySQL | CVE-2012-2122, CVE-2018-2562, CVE-2020-2574 |
| PostgreSQL | CVE-2019-9193, CVE-2022-41862 |
| Redis | CVE-2018-11218, CVE-2018-11219, CVE-2019-10192 |
| SMB/Samba | CVE-2017-0144 (EternalBlue) |
| OpenSSL | CVE-2014-0160 (Heartbleed), CVE-2022-0778, CVE-2014-0224 (CCS) |
| MSSQL | CVE-2019-1068, CVE-2019-1069 |
| VNC | CVE-2006-2369, CVE-2015-5239 |
| RDP | CVE-2019-0708 (BlueKeep), CVE-2022-21999 |
| DNS/BIND | CVE-2020-1350 (SIGRed) |
| SMTP/Exim | CVE-2019-10149 |
| telnetd | CVE-2020-10188 |
| MongoDB | CVE-2019-2389 |
| vsftpd | CVE-2011-2523 (backdoor) |

Vuln level derives from CVE severity: CRITICAL > HIGH > MEDIUM > LOW.

---

## Architecture

- **Language:** Python 3 (pure stdlib — no external dependencies)
- **Optional:** `cryptography` library for enhanced SSL certificate parsing (auto-skipped if unavailable)
- **Concurrency:** `concurrent.futures.ThreadPoolExecutor` (configurable workers)
- **Scan Types:** ICMP probe, TCP connect scan, ICMP ping, UDP probe, banner grab, HTTP fingerprint, SSL handshake, DNS lookup, traceroute (ICMP/UDP)
- **Supported Platforms:** Linux/WSL, Windows, macOS
- **Dependencies:** `socket`, `concurrent.futures`, `struct`, `random`, `time`, `ipaddress`, `argparse`, `json`, `ssl`, `hashlib`, `re`, `datetime`, `signal`

---

## Exit Codes (Automation)

| Code | Meaning |
|------|---------|
| `0` | Scan complete, no CRITICAL/HIGH CVEs found |
| `1` | General error |
| `2` | Interrupted (Ctrl+C) |
| `3` | CRITICAL CVE found |
| `4` | HIGH CVE found |

---

## Legal & Ethical Use

This tool is for:
- Network administrators auditing their own infrastructure
- Penetration testers assessing client networks with authorization
- Bug bounty researchers (with program approval)
- Security researchers studying their own networks

This tool must NOT be used:
- Against networks without explicit written permission
- On public infrastructure you don't own
- For any unauthorized access or reconnaissance

---

## Upgrade Links

| **$49** | [$39](https://buy.stripe.com/bJe00ldyjdFz1bK6sw7wA0V) |
| **Monthly ($10/mo)** | [$10/mo](https://buy.stripe.com/7sYaEZ51N0SN3jSaIM7wA13) |
- **Optional Monthly ($10/mo):** 

**Pro ($29/mo) and Bundle ($39/mo) deprecated** — all features now included in Lifetime.

---

## Support

Email: gpalmieri21@gmail.com  
Discord: https://discord.gg/aPhSnrU9  
Site: https://edgeiqlabs.com

---

## 🔗 More from EdgeIQ Labs

**edgeiqlabs.com** — Security tools, OSINT utilities, and micro-SaaS products for developers and security professionals.

- 🛠️ **Subdomain Hunter** — Passive subdomain enumeration via Certificate Transparency
- 📸 **Screenshot API** — URL-to-screenshot API for developers
- 🔔 **uptime.check** — URL uptime monitoring with alerts
- 🛡️ **headers.check** — HTTP security headers analyzer

👉 [Visit edgeiqlabs.com →](https://edgeiqlabs.com)
