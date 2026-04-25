# Subdomain Hunter

**Skill Name:** `subdomain-hunter`  
**Version:** `1.0.0`  
**Category:** Security / Reconnaissance  
**Price:** **Lifetime: $39** / Optional Monthly: $7/mo (all Pro features permanently)  
**Author:** EdgeIQ Labs  
**OpenClaw Compatible:** Yes — Python 3, pure stdlib + socket, WSL + Linux

---

## What It Does

Passive subdomain enumeration using Certificate Transparency logs, DNS zone transfer checks, and takeover detection. Reconnaissance-grade discovery without sending active probes.

> ⚠️ **Legal Notice:** Only enumerate domains you own or have explicit written permission to audit. Unauthorized recon is illegal.

---

## Features

- **Certificate Transparency enumeration** — scrape crt.sh for subdomain history
- **DNS zone transfer check** — attempt AXFR with common NS records
- **Takeover detection** — identify subdomains pointing to unclaimed/inactive services (CNAME to dead endpoints)
- **Common subdomain bruteforce** — lightweight wordlist scan for common subdomains
- **Subdomain resolution** — verify discovered subdomains resolve
- **JSON export** — structured output for integration

---

## Tier Comparison

| Feature | Free | Pro ($19/mo) | Bundle ($39/mo) |
|---------|------|--------------|-----------------|
| CT log enumeration | ✅ (50 results) | ✅ (unlimited) | ✅ (unlimited) |
| Zone transfer check | ✅ | ✅ | ✅ |
| Takeover detection | — | ✅ | ✅ |
| Bruteforce wordlist | ✅ (2000 names) | ✅ (2000 names) | ✅ (2000 names) |
| JSON export | ✅ | ✅ | ✅ |
| Concurrent resolution | ✅ (50 threads) | ✅ (50 threads) | ✅ (50 threads) |

---

## Installation

```bash
cp -r /home/guy/.openclaw/workspace/apps/subdomain-hunter ~/.openclaw/skills/subdomain-hunter
```

---

## Usage

### Basic scan (free tier — 50 results)

```bash
python3 subdomain_hunter.py --domain example.com
```

### Pro scan (unlimited + takeover detection)

```bash
EDGEIQ_EMAIL=your_email@gmail.com python3 subdomain_hunter.py --domain example.com --pro
```

### Full bundle scan (bruteforce + concurrent threads)

```bash
EDGEIQ_EMAIL=your_email@gmail.com python3 subdomain_hunter.py --domain example.com --bundle --bruteforce
```

### Export to JSON

```bash
python3 subdomain_hunter.py --domain example.com --output results.json
```

### Check for takeovers only

```bash
python3 subdomain_hunter.py --domain example.com --takeover-only
```

### As OpenClaw Discord Command

In `#edgeiq-support` channel:
```
!subdomain example.com
!subdomain example.com --takeover
!subdomain example.com --bruteforce
```

---

## Parameters

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--domain` | string | — | Target domain |
| `--pro` | flag | False | Enable Pro features |
| `--bundle` | flag | False | Enable Bundle features |
| `--bruteforce` | flag | False | Run common subdomain wordlist |
| `--takeover` | flag | False | Run takeover detection |
| `--takeover-only` | flag | False | Only run takeover detection |
| `--output` | string | — | Write JSON report to file |
| `--threads` | int | 20/50 | Concurrent threads (Pro/Bundle) |

---

## Output Example

```
=== Subdomain Hunter ===
example.com
  CT Entries:    47
  Resolved:      31
  Dead:          5
  Takeovers:     2 🔴

  Discovered subdomains:
    api.example.com         ✅ resolves → 1.2.3.4
    staging.example.com    ✅ resolves → 1.2.3.5
    dev.example.com         ❌ DEAD (CNAME to Heroku)
    old.example.com         🔴 TAKEOVER (no CNAME, 404)
    blog.example.com        ✅ resolves → 1.2.3.6

  Zone Transfer:  BLOCKED
  Threat Level:  MEDIUM
```

---

## Pricing

**Lifetime License: $39** — your tool forever, all features included permanently.

**Optional Monthly: $7/mo** — for those who prefer recurring billing (cancel anytime).
👉 [Buy Lifetime — $39](https://buy.stripe.com/5kQdRbbqbfNHf2A7wA7wA0S_lifetime  ·  [Monthly $7/mo](https://buy.stripe.com/5kQdRbbqbfNHf2A7wA7wA0S_monthly))
👉 [Subscribe Monthly — $7/mo](https://buy.stripe.com/5kQdRbbqbfNHf2A7wA7wA0S_lifetime)

## Pro Upgrade *(deprecated)*
All features now included in Lifetime purchase.

---

## Support

Open a ticket in [#edgeiq-support](https://discord.gg/PaP7nsFUJT) or email [gpalmieri21@gmail.com](mailto:gpalmieri21@gmail.com)

---

## 🔗 More from EdgeIQ Labs

**edgeiqlabs.com** — Security tools, OSINT utilities, and micro-SaaS products for developers and security professionals.

- 🛠️ **Subdomain Hunter** — Passive subdomain enumeration via Certificate Transparency
- 📸 **Screenshot API** — URL-to-screenshot API for developers
- 🔔 **uptime.check** — URL uptime monitoring with alerts
- 🛡️ **headers.check** — HTTP security headers analyzer

👉 [Visit edgeiqlabs.com →](https://edgeiqlabs.com)
